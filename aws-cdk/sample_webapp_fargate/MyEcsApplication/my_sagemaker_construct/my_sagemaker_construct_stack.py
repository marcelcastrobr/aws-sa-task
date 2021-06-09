from constructs import Construct

from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_codecommit as codecommit,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
import aws_cdk as cdk
from aws_cdk.aws_iam import ServicePrincipal

class MySagemakerConstructStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create iam role that will give to the Sagemaker notebook instance the permissions needed to perform the tasks
        mysfitsNotebookRole = iam.Role(self, "MysfitsNotbookRole", 
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com") )

        mysfitsNotebookPolicy = iam.PolicyStatement()
        mysfitsNotebookPolicy.add_actions('sagemaker:*',
        'ecr:GetAuthorizationToken',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
        'ecr:BatchCheckLayerAvailability',
        'cloudwatch:PutMetricData',
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:DescribeLogStreams',
        'logs:PutLogEvents',
        'logs:GetLogEvents',
        's3:CreateBucket',
        's3:ListBucket',
        's3:GetBucketLocation',
        's3:GetObject',
        's3:PutObject',
        's3:DeleteObject')

        mysfitsNotebookPolicy.add_all_resources()

        mysfitsNotebookPassRolePolicy = iam.PolicyStatement()
        mysfitsNotebookPassRolePolicy.add_actions('iam:PassRole')
        mysfitsNotebookPassRolePolicy.add_all_resources()
        mysfitsNotebookPassRolePolicy.add_condition('StringEquals', {
            'iam:PassedToService': 'sagemaker.amazonaws.com',})
        iam.Policy(self, "MysfitsNotebookPolicy",
            policy_name="mysfits_notebook_policy",
            statements=[
                mysfitsNotebookPolicy,
                mysfitsNotebookPassRolePolicy
            ],
            roles=[mysfitsNotebookRole]
        )

        #Create the Sagemaker notebook instance
        notebookInstance = sagemaker.CfnNotebookInstance(self, "MythicalMysfits-SageMaker-Notebook", 
        role_arn=mysfitsNotebookRole.role_arn,
        instance_type="ml.t2.medium"
        )

        #Create CodeCommit repository to hold the lambda function.
        lambdaRepository = codecommit.Repository(self, "RecommendationsLambdaRepository",
        repository_name="MythicalMysfits-RecommendationsLambdaRepository")

        cdk.CfnOutput(self, "recommendationsRepositoryCloneUrlHttp",
        value=lambdaRepository.repository_clone_url_http,
        description="Recommendations Lambda Repository Clone Url HTTP")

        cdk.CfnOutput(self, "recommendationsRepositoryCloneUrlSsh",
        value=lambdaRepository.repository_clone_url_ssh,
        description="Recommendations Lambda Repository Clone Url SSH")


        #Let´s define the Recommendations microservice infrastructure
        recommandationsLambdaFunctionPolicyStm = iam.PolicyStatement()
        recommandationsLambdaFunctionPolicyStm.add_actions("sagemaker:InvokeEndpoint")
        recommandationsLambdaFunctionPolicyStm.add_all_resources()

        mysfitsRecommendations = _lambda.Function(self, "MyRecommendationLambdaFunction",
        handler="recommendations.recommend",
        runtime=_lambda.Runtime.PYTHON_3_6,
        description="A microservice backend to invoke a SageMaker endpoint.",
        memory_size=128,
        code=_lambda.Code.from_asset("../environment/lambda-recommendations/service"),
        timeout=cdk.Duration.seconds(30),
        initial_policy=[recommandationsLambdaFunctionPolicyStm]
        )

        questionsApiRole = iam.Role(self, "QuestionsApiRole",
        assumed_by=ServicePrincipal("apigateway.amazonaws.com"))

        apiPolicy = iam.PolicyStatement()
        apiPolicy.add_actions("lambda:InvokeFunction")
        apiPolicy.add_resources(mysfitsRecommendations.function_arn)
        iam.Policy(self, "QuestionsApiPolicy",
        policy_name="questions_api_policy",
        statements=[apiPolicy],
        roles=[questionsApiRole]
        )

        # Lets Integrates an AWS Lambda function to an API Gateway method.
        questionsIntegration = apigw.LambdaIntegration(mysfitsRecommendations,
        credentials_role=questionsApiRole,
        integration_responses=[{
            "statusCode": "200",
            "responseTemplates": {
                "application/json": '{"status":"OK"}'
            }
            }]
        )

        #Lets defines an API Gateway REST API with AWS Lambda proxy integration.
        api = apigw.LambdaRestApi(self, "APIEndpoint",
        handler=mysfitsRecommendations,
        #deploy_options=[{
        #    "restApiName": "Recommendation API Service"
        #    }],
        proxy=False
        )

        recommendationsMethod = api.root.add_resource("recommendations")
        recommendationsMethod.add_method("POST", questionsIntegration,
        method_responses=[{
            # Successful response from the integration
            "statusCode": "200",
            # Define what parameters are allowed or not
            "responseParameters": {
            "method.response.header.Access-Control-Allow-Headers": True,
            "method.response.header.Access-Control-Allow-Methods": True,
            "method.response.header.Access-Control-Allow-Origin": True
            }
            }],
        authorization_type= apigw.AuthorizationType.NONE
        )

        recommendationsMethod.add_method("OPTIONS", apigw.MockIntegration(
        integration_responses=[{
            "statusCode": '200',
            "responseParameters": {
            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'",
            'method.response.header.Access-Control-Allow-Origin': "'*'",
            'method.response.header.Access-Control-Allow-Credentials': "'false'",
            'method.response.header.Access-Control-Allow-Methods': "'OPTIONS,GET,PUT,POST,DELETE'",
            }}],
            passthrough_behavior= apigw.PassthroughBehavior.NEVER,
            request_templates={ "application/json": "{\"statusCode\": 200}"}
        ),
        method_responses=[{
                "statusCode": '200',
                "responseParameters": {
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Credentials': True,
                'method.response.header.Access-Control-Allow-Origin': True,
                },  
            }]
        )


        