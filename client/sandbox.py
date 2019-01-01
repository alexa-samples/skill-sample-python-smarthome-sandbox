#!/usr/bin/python
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
import random
import sys
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import build_opener, HTTPSHandler, Request, urlopen

sys.path.append('../lambda/api')
from endpoint_cloud import ApiAuth, ApiUtils

api_auth = ApiAuth()
cloudformation_aws = boto3.client('cloudformation')
cloudformation_aws_resource = boto3.resource('cloudformation')

# The template to use for the Sandbox
template = '../cloudformation/sandbox.template'
redirect_uri = 'http://127.0.0.1:9090/cb'

auth_code = client_id = client_secret = access_token = refresh_token = 'INVALID'
auth_code_http_server = None


class AuthCodeServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code, auth_code_http_server,  client_id, client_secret, access_token, refresh_token

        path = self.path[:3]
        if path == '/cb':
            query_params = parse_qs(urlparse(self.path).query)
            auth_code = query_params['code'][0]
            print('auth_code', auth_code)
            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(
                bytes('<html><head>'
                      '<title>Smart Home Sandbox</title>'
                      '</head><body><center>'
                      '<h2>AuthCode: {}<br/></h2>'
                      '<h3>Starting stack creation, visit <a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks">the console for status</a>.</h3></center></body></html>'.format(auth_code), 'UTF-8'))

            # Get access and refresh tokens
            response_token = api_auth.get_access_token(auth_code, client_id, client_secret, redirect_uri)
            response_token_string = response_token.read().decode('utf-8')
            # print('LOG directive.process.authorization.response_token_string:', response_token_string)
            response_object = json.loads(response_token_string)
            # print(response_object)
            access_token = response_object['access_token']
            refresh_token = response_object['refresh_token']

            # Stop the server
            def shutdown_server(server):
                server.shutdown()

            thread = Thread(target=shutdown_server, args=(auth_code_http_server,))
            thread.start()


def create_endpoint(endpoint_file_name, user_id, endpoint_api_url):
    with open(endpoint_file_name, 'r') as endpoint_file:
        event_object = json.load(endpoint_file)
        event_object['event']['endpoint']['userId'] = user_id

        url = endpoint_api_url + 'endpoints'
        data = bytes(json.dumps(event_object), encoding="utf-8")
        headers = {'Content-Type': 'application/json'}
        req = Request(url, data, headers)
        result = urlopen(req).read().decode("utf-8")
        response = json.loads(result)
        if ApiUtils.check_response(response):
            print('\tCreated endpoint', endpoint_file_name)
        endpoint_file.close()


def create_stack(stack_name, vendor_id, client_id, client_secret, access_token, refresh_token):
    print('Creating Stack', stack_name)
    with open(template, 'r') as template_file:
        template_object = json.load(template_file)
        # Run the CF Template with parameters
        response_cloudformation = cloudformation_aws.create_stack(
            StackName=stack_name,
            TemplateBody=json.dumps(template_object),
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Parameters=[
                {
                    "ParameterKey": "VendorId",
                    "ParameterValue": vendor_id
                },
                {
                    "ParameterKey": "ClientId",
                    "ParameterValue": client_id
                },
                {
                    "ParameterKey": "ClientSecret",
                    "ParameterValue": client_secret
                },
                {
                    "ParameterKey": "AccessToken",
                    "ParameterValue": access_token
                },
                {
                    "ParameterKey": "RefreshToken",
                    "ParameterValue": refresh_token
                }
            ]
        )
        if ApiUtils.check_response(response_cloudformation):
            print(stack_name, 'Stack creation started')


def get_auth_code_url(redirect_uri, client_id):
    query_params = {
        'redirect_uri': redirect_uri,
        'scope': 'alexa::ask:skills:readwrite profile:user_id',
        'state': 'Ask-SkillModel-ReadWrite',
        'response_type': 'code',
        'client_id': client_id
    }
    return 'https://www.amazon.com/ap/oa?' + urlencode(query_params)


def main():
    global auth_code_http_server, client_id, client_secret, access_token, refresh_token

    print('INSTRUCTION: Enter the Vendor ID, LWA Client ID, and LWA Client Secret')
    vendor_id = input('Vendor ID: ')
    client_id = input('Login with Amazon Client ID: ')
    client_secret = input('Login with Amazon Client Secret: ')

    print('\tAuthorizing User...')
    webbrowser.open(get_auth_code_url('http://127.0.0.1:9090/cb', client_id), new=2)

    # Start HTTP server to wait for auth code
    print('\tWaiting for authorization from User...')
    server_address = ('127.0.0.1', 9090)
    auth_code_http_server = httpd = HTTPServer(server_address, AuthCodeServerHandler)
    httpd.serve_forever()

    # Start the Stack Creation
    name_id = ''.join(random.choice('0123456789') for _ in range(6))
    stack_name = 'SmartHomeSandbox-' + name_id
    create_stack(stack_name, vendor_id, client_id, client_secret, access_token, refresh_token)

    stack = cloudformation_aws_resource.Stack(stack_name)
    while True:
        status = stack.stack_status
        print('\tstack status:', status)

        if status == 'CREATE_COMPLETE':
            break

        if status == 'ROLLBACK_COMPLETE':
            print('Error during stack creation, check the CloudWatch logs')
            return

        time.sleep(5)
        stack = cloudformation_aws_resource.Stack(stack_name)

    # Unpack the outputs from the created stack
    for output in stack.outputs:

        if output['OutputKey'] == 'AccessToken':
            access_token = output['OutputValue']
            print('\taccess_token:', access_token)

        if output['OutputKey'] == 'AlexaSkillId':
            alexa_skill_id = output['OutputValue']
            print('\talexa_skill_id:', alexa_skill_id)

        if output['OutputKey'] == 'ClientId':
            client_id = output['OutputValue']
            print('\tclient_id:', client_id)

        if output['OutputKey'] == 'ClientSecret':
            client_secret = output['OutputValue']
            print('\tclient_secret:', client_secret)

        if output['OutputKey'] == 'EndpointApiUrl':
            endpoint_api_url = output['OutputValue']
            print('\tendpoint_api_url:', endpoint_api_url)

        if output['OutputKey'] == 'SkillLambdaArn':
            skill_lambda_arn = output['OutputValue']
            print('\tskill_lambda_arn:', skill_lambda_arn)

    account_linking_request = {
        "accountLinkingRequest": {
            "skipOnEnablement": "false",
            "type": "AUTH_CODE",
            "authorizationUrl": "https://www.amazon.com/ap/oa",
            "domains": [],
            "clientId": client_id,
            "scopes": ["profile:user_id"],
            "accessTokenUrl": "https://api.amazon.com/auth/o2/token",
            "clientSecret": client_secret,
            "accessTokenScheme": "HTTP_BASIC",
            "defaultTokenExpirationInSeconds": 20
        }
    }
    url_update_account_linking = \
        'https://api.amazonalexa.com/v1/skills/{0}/stages/development/accountLinkingClient'.format(alexa_skill_id)
    # print('url_update_account_linking:', url_update_account_linking)

    if access_token == 'INVALID':
        print('\taccess_token:', access_token)
        return

    opener = build_opener(HTTPSHandler)
    request = Request(url_update_account_linking, data=bytes(json.dumps(account_linking_request), 'iso-8859-1'))
    request.add_header('Authorization', access_token)
    request.get_method = lambda: 'PUT'
    try:
        response = opener.open(request)
        print('\tSetup Account Linking Request Response Status Code:', response.getcode())

    except HTTPError as e:
        print(e, e.reason, e.headers)

    enable_url = 'https://alexa.amazon.com/spa/index.html#skills/beta/{}/?ref=skill_dsk_skb_ys'.format(alexa_skill_id)
    print('INSTRUCTION: Enable the Sandbox Skill at', enable_url)
    print('\tOpening Skill Page for Alexa Skill:', alexa_skill_id)
    webbrowser.open(enable_url, new=2)

    print('\tAdding User to SampleUsers table and Creating sample endpoint files')
    user_id_object = json.loads(api_auth.get_user_id(access_token).read().decode('utf-8'))
    user_id = user_id_object['user_id']
    print('\tuser_id', user_id)

    # Update the stored credentials
    table = boto3.resource('dynamodb').Table('SampleUsers')
    result = table.put_item(
        Item={
            'UserId': user_id,
            'AccessToken': access_token,
            'ClientId': client_id,
            'ClientSecret': client_secret,
            'RefreshToken': refresh_token,
            'RedirectUri': redirect_uri
        }
    )
    if ApiUtils.check_response(result):
        print('\tCreated information for ', user_id)

    if use_defaults:
        create_endpoint('sample-switch-black.json', user_id, endpoint_api_url)
        create_endpoint('sample-switch-white.json', user_id, endpoint_api_url)
        create_endpoint('sample-toaster.json', user_id, endpoint_api_url)


if __name__ == '__main__':
    use_defaults = True
    run = True
    # Parse the command line options
    if len(sys.argv) > 1:
        if sys.argv[1] == 'no-defaults':
            print('Option: Not using defaults')
            use_defaults = False

        if sys.argv[1] == 'clean-logs':
            print('Option: Cleaning Logs')
            cloudwatch_client_aws = boto3.client('logs')
            response = cloudwatch_client_aws.describe_log_groups(
                logGroupNamePrefix='/aws/lambda/SmartHomeSandbox'
            )
            print(response)
            if 'logGroups' in response:
                for log_group in response['logGroups']:
                    response = cloudwatch_client_aws.delete_log_group(
                        logGroupName=log_group['logGroupName']
                    )
                    print(response)
            run = False

        if sys.argv[1] == 'clean-things':
            print('Option: Cleaning Things')
            iot_aws = boto3.client('iot')
            response = iot_aws.list_things_in_thing_group(
                thingGroupName='Samples'
            )
            print(response)
            if 'things' in response:
                for thing in response['things']:
                    response = iot_aws.delete_thing(
                        thingName=thing,
                    )
                    print(response)
            run = False

    if run:
        main()
