#!/usr/bin/env python3

import aws_cdk as cdk

from sample_webapp.sample_webapp_stack import SampleWebappStack


app = cdk.App()
SampleWebappStack(app, "sample-webapp", env={'region': 'eu-west-2'})

app.synth()
