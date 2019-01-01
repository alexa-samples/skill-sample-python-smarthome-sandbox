# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import boto3
import json
from urllib.request import build_opener, HTTPError, HTTPHandler, Request, urlopen

lambda_aws = boto3.client('lambda')


def handler(event, context):
    print("LOG setup.index.handler.event -----\n", json.dumps(event))

    if event['RequestType'] == "Create":

        resource_properties = event['ResourceProperties']

        access_token = resource_properties['AccessToken']
        print("LOG setup.index.handler.access_token:", access_token)

        endpoint_apid_id = event['ResourceProperties']['EndpointApiId']
        print("LOG setup.index.handler.endpoint_apid_id:", endpoint_apid_id)

        endpoint_lambda = event['ResourceProperties']['EndpointLambda']
        print("LOG setup.index.handler.endpoint_lambda:", endpoint_lambda)

        skill_id = resource_properties['SkillId']
        print("LOG setup.index.handler.skill_id:", skill_id)

        skill_lambda = event['ResourceProperties']['SkillLambda']
        print("LOG setup.index.handler.skill_lambda:", skill_lambda)

        alexa_skill_lambda_permission_statement_id = event['ResourceProperties']['AlexaSkillLambdaPermissionStatementId']
        print("LOG setup.index.handler.alexa_skill_lambda_permission_statement_id:", alexa_skill_lambda_permission_statement_id)

        response = lambda_aws.remove_permission(
            FunctionName=skill_lambda,
            StatementId=alexa_skill_lambda_permission_statement_id
        )
        print(response)

        response = lambda_aws.add_permission(
            FunctionName=skill_lambda,
            StatementId=alexa_skill_lambda_permission_statement_id,
            Action='lambda:InvokeFunction',
            Principal='alexa-connectedhome.amazon.com',
            EventSourceToken=skill_id
        )
        print(response)

        # Get the messaging credentials
        url = 'https://api.amazonalexa.com/v1/skills/{}/credentials'.format(skill_id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': access_token
        }
        request = Request(url=url, headers=headers)
        result = urlopen(request).read().decode("utf-8")
        response = json.loads(result)
        if 'skillMessagingCredentials' in response:
            client_id = response['skillMessagingCredentials']['clientId']
            client_secret = response['skillMessagingCredentials']['clientSecret']

            # Update the Lambda
            response = lambda_aws.update_function_configuration(
                FunctionName=endpoint_lambda,
                Environment={
                    'Variables': {
                        'api_id': endpoint_apid_id,
                        'client_id': client_id,
                        'client_secret': client_secret
                    }
                }
            )
            print(response)
        else:
            print('ERR setup.index.handler: Invalid SMAPI response')

    # if event['RequestType'] == "Delete":
    #     print("LOG setup.index.handler:Delete")
    #     return send_response(event, context, "SUCCESS", {})

    response_status = 'SUCCESS'
    response_data = {'event': event}

    response_body = json.dumps(
        {
            'Status': response_status,
            'Reason': "CloudWatch Log Stream: " + context.log_stream_name,
            'PhysicalResourceId': context.log_stream_name,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Data': response_data
        }
    )

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=bytes(response_body, 'utf-8'))
    request.add_header('Content-Type', '')  # NOTE This has to be empty
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'

    try:
        print("LOG setup.index.send:opener.open -----")
        response = opener.open(request, timeout=7)
        print("Response Status Code: {0} Message: {1}".format(response.getcode(), response.msg))
        return True

    except HTTPError as e:
        print("HTTPError: {}".format(e))
        return False
