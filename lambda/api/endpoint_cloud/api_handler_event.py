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

import http.client
import json
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from alexa.skills.smarthome import AlexaResponse
from .api_auth import ApiAuth

dynamodb_aws = boto3.client('dynamodb')
iot_aws = boto3.client('iot')
iot_data_aws = boto3.client('iot-data')


class ApiHandlerEvent:

    def create(self, request):
        print('LOG event.create.request -----')
        print(request)

        try:
            json_object = json.loads(request['body'])

            # Transpose the Endpoint Cloud Event into an Alexa Event Gateway Event

            # Get the common information from the body of the request
            event_type = json_object['event']['type']  # Expect AddOrUpdateReport, ChangeReport, DeleteReport
            endpoint_user_id = json_object['event']['endpoint']['userId']  # Expect a Profile
            endpoint_id = json_object['event']['endpoint']['id']  # Expect a valid AWS IoT Thing Name

            # Get the Access Token
            token = self.get_user_info(endpoint_user_id)

            # Build a default response
            response = AlexaResponse(name='ErrorResponse', message="No valid event type")

            if event_type == 'AddOrUpdateReport':
                # Get the additional information from the body of the request
                endpoint_friendly_name = json_object['event']['endpoint']['friendlyName']  # Expect a valid string friendly name
                endpoint_capabilities = json_object['event']['endpoint']['capabilities']  # Expect a valid AWS IoT Thing Name
                sku = json_object['event']['endpoint']['sku']  # Expect a meaningful type, ex: SW00

                # From the SKU, get the information for the device and combine it in the payload
                endpoint_sku_details = self.get_sku_details(sku)
                payload = {
                    'endpoints': [
                        {
                            'endpointId': endpoint_id,
                            'friendlyName': endpoint_friendly_name,
                            'description': endpoint_sku_details['description'],
                            'manufacturerName': endpoint_sku_details['manufacturer_name'],
                            'displayCategories': endpoint_sku_details['display_categories'],
                            'capabilities': endpoint_capabilities
                        }],
                    'scope': {
                        'type': 'BearerToken',
                        'token': token
                    }
                }

                # Send an event to Alexa to add/update the endpoint
                response = self.send_event('Alexa.Discovery', 'AddOrUpdateReport', endpoint_id, token, payload)

            if event_type == 'ChangeReport':
                try:
                    state = json_object['event']['endpoint']['state']  # Expect a string, ex: powerState
                    state_value = json_object['event']['endpoint']['value']  # Expect string or JSON
                    namespace = json_object['event']['endpoint']['namespace']
                    instance = json_object['event']['endpoint'].get('instance', None)
                    if instance:
                        state = instance+'.'+state
                        prop = AlexaResponse.create_context_property(instance=instance, namespace=namespace, name=state, value=state_value)
                    else:
                        prop = AlexaResponse.create_context_property(namespace=namespace, name=state, value=state_value)
                    # Update the IoT Thing Shadow state
                    msg = {
                        'state': {
                            'desired':
                                {
                                    state: state_value
                                }
                        }
                    }
                    mqtt_msg = json.dumps(msg)
                    result = iot_data_aws.update_thing_shadow(
                        thingName=endpoint_id,
                        payload=mqtt_msg.encode())
                    print('LOG event.create.iot_aws.update_thing_shadow.result -----')
                    print(result)

                    # Update Alexa with an Event Update
                    if endpoint_user_id == '0':
                        print('LOG Event: Not sent for user_id of 0')
                    else:
                        payload = {
                            'change': {
                                'cause': {
                                    'type': 'PHYSICAL_INTERACTION'
                                },
                                "properties": [
                                    prop
                                ]
                            }
                        }
                        print('LOG Event: Sending event')
                        response = self.send_event('Alexa', 'ChangeReport', endpoint_id, token, payload)

                except ClientError as e:
                    alexa_response = AlexaResponse(name='ErrorResponse', message=e, payload={'type': 'INTERNAL_ERROR', 'message': e})
                    return alexa_response.get()

            if event_type == 'DeleteReport':
                # Send an event to Alexa to delete the endpoint
                payload = {
                    'endpoints': [
                        {
                            'endpointId': endpoint_id
                        }
                    ],
                    "scope": {
                        "type": "BearerToken",
                        "token": token
                    }
                }
                response = self.send_event('Alexa.Discovery', 'DeleteReport', endpoint_id, token, payload)

            result = response.read().decode('utf-8')
            print('LOG event.create.result -----')
            print(result)
            return result

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

    # TODO Improve this with a database lookup
    @staticmethod
    def get_sku_details(sku):

        # Set the default at OTHER (OT00)
        sku_details = dict(description='A sample endpoint', manufacturer_name='Sample Manufacturer', display_categories=['OTHER'])

        if sku.upper().startswith('LI'):
            sku_details['description'] = 'A sample light endpoint'
            sku_details['display_categories'] = ["LIGHT"]

        if sku.upper().startswith('MW'):
            sku_details['description'] = 'A sample microwave endpoint'
            sku_details['display_categories'] = ["MICROWAVE"]

        if sku.upper().startswith('TT'):
            sku_details['description'] = 'A sample toaster endpoint'
            sku_details['display_categories'] = ["OTHER"]

        if sku.upper().startswith('SW'):
            sku_details['description'] = 'A sample switch endpoint'
            sku_details['display_categories'] = ["SWITCH"]

        return sku_details

    def get_user_info(self, endpoint_user_id):
        print('LOG event.create.get_user_info -----')
        table = boto3.resource('dynamodb').Table('SampleUsers')
        result = table.get_item(
            Key={
                'UserId': endpoint_user_id
            },
            AttributesToGet=[
                'UserId',
                'AccessToken',
                'ClientId',
                'ClientSecret',
                'ExpirationUTC',
                'RedirectUri',
                'RefreshToken',
                'TokenType'
            ]
        )

        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            if 'Item' in result:
                print('LOG event.create.get_user_info.SampleUsers.get_item -----')
                print(str(result['Item']))
                if 'ExpirationUTC' in result['Item']:
                    expiration_utc = result['Item']['ExpirationUTC']
                    token_is_expired = self.is_token_expired(expiration_utc)
                else:
                    token_is_expired = True
                print('LOG event.create.send_event.token_is_expired:', token_is_expired)
                if token_is_expired:
                    # The token has expired so get a new access token using the refresh token
                    refresh_token = result['Item']['RefreshToken']
                    client_id = result['Item']['ClientId']
                    client_secret = result['Item']['ClientSecret']
                    redirect_uri = result['Item']['RedirectUri']

                    api_auth = ApiAuth()
                    response_refresh_token = api_auth.refresh_access_token(refresh_token, client_id, client_secret, redirect_uri)
                    response_refresh_token_string = response_refresh_token.read().decode('utf-8')
                    response_refresh_token_object = json.loads(response_refresh_token_string)

                    # Store the new values from the refresh
                    access_token = response_refresh_token_object['access_token']
                    refresh_token = response_refresh_token_object['refresh_token']
                    token_type = response_refresh_token_object['token_type']
                    expires_in = response_refresh_token_object['expires_in']

                    # Calculate expiration
                    expiration_utc = datetime.utcnow() + timedelta(seconds=(int(expires_in) - 5))

                    print('access_token', access_token)
                    print('expiration_utc', expiration_utc)

                    result = table.update_item(
                        Key={
                            'UserId': endpoint_user_id
                        },
                        UpdateExpression="set AccessToken=:a, RefreshToken=:r, TokenType=:t, ExpirationUTC=:e",
                        ExpressionAttributeValues={
                            ':a': access_token,
                            ':r': refresh_token,
                            ':t': token_type,
                            ':e': expiration_utc.strftime("%Y-%m-%dT%H:%M:%S.00Z")
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                    print('LOG event.create.send_event.SampleUsers.update_item:', str(result))

                    # TODO Return an error here if the token could not be refreshed
                else:
                    # Use the stored access token
                    access_token = result['Item']['AccessToken']
                    print('LOG Using stored access_token:', access_token)

                return access_token

    @staticmethod
    def is_token_expired(expiration_utc):
        now = datetime.utcnow().replace(tzinfo=None)
        then = datetime.strptime(expiration_utc, "%Y-%m-%dT%H:%M:%S.00Z")
        is_expired = now > then
        if is_expired:
            return is_expired
        seconds = (now - then).seconds
        is_soon = seconds < 30  # Give a 30 second buffer for expiration
        return is_soon

    @staticmethod
    def send_event(alexa_namespace, alexa_name, endpoint_id, token, payload):

        remove_endpoint = alexa_name is not "ChangeReport"
        alexa_response = AlexaResponse(namespace=alexa_namespace, name=alexa_name, endpoint_id=endpoint_id, token=token, remove_endpoint=remove_endpoint)
        alexa_response.set_payload(payload)
        payload = json.dumps(alexa_response.get())
        print('LOG api_handler_event.send_event.payload:')
        print(payload)

        # TODO Map to correct endpoint for Europe: https://api.eu.amazonalexa.com/v3/events
        # TODO Map to correct endpoint for Far East: https://api.fe.amazonalexa.com/v3/events
        alexa_event_gateway_uri = 'api.amazonalexa.com'
        connection = http.client.HTTPSConnection(alexa_event_gateway_uri)
        headers = {
            'Authorization': "Bearer " + token,
            'Content-Type': "application/json;charset=UTF-8",
            'Cache-Control': "no-cache"
        }
        connection.request('POST', '/v3/events', payload, headers)
        response = connection.getresponse()
        print('LOG api_handler_event.send_event HTTP Status code: ' + str(response.getcode()))
        return response
