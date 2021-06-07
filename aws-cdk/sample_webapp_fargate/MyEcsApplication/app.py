#!/usr/bin/env python3
import os
#import aws_cdk as cdk
import aws_cdk as cdk


from my_ecs_construct.my_ecs_construct_stack import MyEcsConstructStack
from my_ecr_construct.ecr_stack import MyEcrConstructStack


app = cdk.App()
MyEcsConstructStack(app, "MyEcsConstructStack",
    env=cdk.Environment(account='905400909115', region='us-east-1'),
    )


MyEcrConstructStack(app, "MyEcrConstructStack",
    env=cdk.Environment(account='905400909115', region='us-east-1'),
    )

app.synth()
