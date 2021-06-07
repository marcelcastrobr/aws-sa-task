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
)

class MyEcsConstructStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        vpc = ec2.Vpc(self, "MyVpc", max_azs=3)     # default is all AZs in region

        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)
        cluster.connections.allow_from_any_ipv4(ec2.Port.tcp(8080))

        ecsService = ecs_patterns.ApplicationLoadBalancedFargateService(self, "MyFargateService",
            cluster=cluster,            # Required
            cpu=512,                    # Default is 256
            desired_count=1,            # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("MythicalMysfits-Service"),
                container_name="MythicalMysfits-Service",
                container_port= 8080),
            memory_limit_mib=2048,      # Default is 512
            public_load_balancer=True)


        ecsService.service.connections.allow_from(ec2.Peer.ipv4(vpc.vpc_cidr_block),ec2.Port.tcp(8080))

        taskDefinitionPolicy = iam.PolicyStatement()
        taskDefinitionPolicy.add_actions(
            # Rules which allow ECS to attach network interfaces to instances
            # on your behalf in order for awsvpc networking mode to work right
            "ec2:AttachNetworkInterface",
            "ec2:CreateNetworkInterface",
            "ec2:CreateNetworkInterfacePermission",
            "ec2:DeleteNetworkInterface",
            "ec2:DeleteNetworkInterfacePermission",
            "ec2:Describe*",
            "ec2:DetachNetworkInterface",

            # Rules which allow ECS to update load balancers on your behalf
            #  with the information sabout how to send traffic to your containers
            "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
            "elasticloadbalancing:DeregisterTargets",
            "elasticloadbalancing:Describe*",
            "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
            "elasticloadbalancing:RegisterTargets",

            #  Rules which allow ECS to run tasks that have IAM roles assigned to them.
            "iam:PassRole",

            #  Rules that let ECS create and push logs to CloudWatch.
            "logs:DescribeLogStreams",
            "logs:CreateLogGroup"
        )
        taskDefinitionPolicy.add_all_resources()
        ecsService.service.task_definition.add_to_execution_role_policy(taskDefinitionPolicy)

        taskRolePolicy =  iam.PolicyStatement()
        taskRolePolicy.add_actions(
            # Allow the ECS Tasks to download images from ECR
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            # Allow the ECS tasks to upload logs to CloudWatch
            "logs:CreateLogStream",
            "logs:CreateLogGroup",
            "logs:PutLogEvents"
        )
        taskRolePolicy.add_all_resources()
        ecsService.service.task_definition.add_to_task_role_policy(taskRolePolicy)




