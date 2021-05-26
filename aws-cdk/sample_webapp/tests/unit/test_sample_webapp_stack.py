import json
import pytest

import aws_cdk_lib as core
from sample_webapp.sample_webapp_stack import SampleWebappStack


def get_template():
    app = core.App()
    SampleWebappStack(app, "sample-webapp")
    return json.dumps(app.synth().get_stack("sample-webapp").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())


def test_sns_topic_created():
    assert("AWS::SNS::Topic" in get_template())
