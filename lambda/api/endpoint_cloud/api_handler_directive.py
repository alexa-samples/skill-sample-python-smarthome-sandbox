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

import json
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from alexa.skills.smarthome import AlexaResponse
from jsonschema import validate, SchemaError, ValidationError
from .api_auth import ApiAuth
from .api_handler_endpoint import ApiHandlerEndpoint

dynamodb_aws = boto3.client('dynamodb')
iot_aws = boto3.client('iot')
iot_data_aws = boto3.client('iot-data')

DEFAULT_VAL = {
    'Alexa.RangeController': 1,
    'Alexa.PowerController': 'OFF'
}

class ApiHandlerDirective:

    @staticmethod
    def get_db_value(value):
        if 'S' in value:
            value = value['S']
        return value

    def process(self, request, client_id, client_secret, redirect_uri):
        print('LOG api_handler_directive.process -----')
        # print(json.dumps(request))

        response = None
        # Process an Alexa directive and route to the right namespace
        # Only process if there is an actual body to process otherwise return an ErrorResponse
        json_body = request['body']
        if json_body:
            json_object = json.loads(json_body)
            namespace = json_object['directive']['header']['namespace']

            if namespace == "Alexa":
                name = json_object['directive']['header']['name']
                correlation_token = json_object['directive']['header']['correlationToken']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']

                if name == 'ReportState':
                    # Get the User ID from the access_token
                    response_user_id = json.loads(ApiAuth.get_user_id(token).read().decode('utf-8'))
                    result = dynamodb_aws.get_item(TableName='SampleEndpointDetails', Key={'EndpointId': {'S': endpoint_id}})
                    capabilities_string = self.get_db_value(result['Item']['Capabilities'])
                    capabilities = json.loads(capabilities_string)
                    props=[]
                    for c in capabilities:
                        if not 'properties' in c:
                            continue
                        retrievable = c['properties'].get('retrievable', False)
                        if retrievable:
                            props.append(c)
                    state = {}   
                    try: 
                        res = iot_data_aws.get_thing_shadow(thingName=endpoint_id)
                        shadow=json.loads(res['payload'].read())
                        state = shadow['state']['desired']
                    except ClientError as e:
                        print('LOG ', e)
                        
                    
                    print('Sending StateReport for', response_user_id, 'on endpoint', endpoint_id)
                    statereport_response = AlexaResponse(name='StateReport', endpoint_id=endpoint_id, correlation_token=correlation_token, token=token)
                    
                    for p in props:
                        key = p['properties']['supported'][0]['name']
                        if 'instance' in p:
                            key = p['instance']+'.'+key
                        current_state = state.get(key, DEFAULT_VAL[p['interface']])
                        if 'instance' in p:
                            statereport_response.add_context_property(namespace=p['interface'],
                                name=p['properties']['supported'][0]['name'], value=current_state,
                                instance=p['instance'])
                        else: 
                            statereport_response.add_context_property(namespace=p['interface'],
                                name=p['properties']['supported'][0]['name'], value=current_state)


                    response = statereport_response.get()

            if namespace == "Alexa.Authorization":
                grant_code = json_object['directive']['payload']['grant']['code']
                grantee_token = json_object['directive']['payload']['grantee']['token']

                # Spot the default from the Alexa.Discovery sample. Use as a default for development.
                if grantee_token == 'access-token-from-skill':
                    user_id = "0"  # <- Useful for development
                    response_object = {
                        'access_token': 'INVALID',
                        'refresh_token': 'INVALID',
                        'token_type': 'Bearer',
                        'expires_in': 9000
                    }
                else:
                    # Get the User ID
                    response_user_id = json.loads(ApiAuth.get_user_id(grantee_token).read().decode('utf-8'))
                    if 'error' in response_user_id:
                        print('ERROR api_handler_directive.process.authorization.user_id:', response_user_id['error_description'])
                        return AlexaResponse(name='ErrorResponse', payload={'type': 'INTERNAL_ERROR', 'message': response_user_id})

                    user_id = response_user_id['user_id']
                    print('LOG api_handler_directive.process.authorization.user_id:', user_id)

                # Get the Access and Refresh Tokens
                api_auth = ApiAuth()
                print('grant_code', grant_code, 'client_id', client_id, 'client_secret', client_secret, 'redirect_uri', redirect_uri)
                response_token = api_auth.get_access_token(grant_code, client_id, client_secret, redirect_uri)
                response_token_string = response_token.read().decode('utf-8')
                print('LOG api_handler_directive.process.authorization.response_token_string:', response_token_string)
                response_object = json.loads(response_token_string)

                if 'error' in response_object:
                    return AlexaResponse(name='ErrorResponse', payload={'type': 'INTERNAL_ERROR', 'response_object': response_object})

                # Store the retrieved from the Authorization Server
                access_token = response_object['access_token']
                refresh_token = response_object['refresh_token']
                token_type = response_object['token_type']
                expires_in = response_object['expires_in']

                # Calculate expiration
                expiration_utc = datetime.utcnow() + timedelta(seconds=(int(expires_in) - 5))

                # Store the User Information - This is useful for inspection during development
                table = boto3.resource('dynamodb').Table('SampleUsers')
                result = table.put_item(
                    Item={
                        'UserId': user_id,
                        'GrantCode': grant_code,
                        'GranteeToken': grantee_token,
                        'AccessToken': access_token,
                        'ClientId': client_id,
                        'ClientSecret': client_secret,
                        'ExpirationUTC': expiration_utc.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                        'RedirectUri': redirect_uri,
                        'RefreshToken': refresh_token,
                        'TokenType': token_type
                    }
                )

                if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print('LOG api_handler_directive.process.authorization.SampleUsers.put_item:', result)
                    alexa_accept_grant_response = AlexaResponse(namespace='Alexa.Authorization', name='AcceptGrant.Response')
                    response = alexa_accept_grant_response.get()
                else:
                    error_message = 'Error creating User'
                    print('ERR api_handler_directive.process.authorization', error_message)
                    alexa_error_response = AlexaResponse(name='ErrorResponse')
                    alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': error_message})
                    response = alexa_error_response.get()

            if namespace == "Alexa.Cooking":
                name = json_object['directive']['header']['name']
                correlation_token = json_object['directive']['header']['correlationToken']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']
                if name == "SetCookingMode":
                    alexa_error_response = AlexaResponse(endpoint_id=endpoint_id, correlation_token=correlation_token, token=token)
                    response = alexa_error_response.get()

            if namespace == "Alexa.Discovery":
                # Given the Access Token, get the User ID
                access_token = json_object['directive']['payload']['scope']['token']

                # Spot the default from the Alexa.Discovery sample. Use as a default for development.
                if access_token == 'access-token-from-skill':
                    print('WARN api_handler_directive.process.discovery.user_id: Using development user_id of 0')
                    user_id = "0"  # <- Useful for development
                else:
                    response_user_id = json.loads(ApiAuth.get_user_id(access_token).read().decode('utf-8'))
                    if 'error' in response_user_id:
                        print('ERROR api_handler_directive.process.discovery.user_id: ' + response_user_id['error_description'])
                    user_id = response_user_id['user_id']
                    print('LOG api_handler_directive.process.discovery.user_id:', user_id)

                adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')

                # Get the list of endpoints to return for a User ID and add them to the response
                # Use the AWS IoT entries for state but get the discovery details from DynamoDB
                # Wanted to list by group name but that requires a second lookup for the details
                # iot_aws.list_things_in_thing_group(thingGroupName="Samples")
                list_response = iot_aws.list_things()

                # Get a list of sample things by the user_id attribute
                for thing in list_response['things']:
                    if 'user_id' in thing['attributes']:
                        if thing['attributes']['user_id'] == user_id:
                            # We have an endpoint thing!
                            endpoint_details = ApiHandlerEndpoint.EndpointDetails()
                            endpoint_details.id = str(thing['thingName'])
                            print('LOG api_handler_directive.process.discovery: Found:', endpoint_details.id, 'for user:', user_id)
                            result = dynamodb_aws.get_item(TableName='SampleEndpointDetails', Key={'EndpointId': {'S': endpoint_details.id}})
                            capabilities_string = self.get_db_value(result['Item']['Capabilities'])
                            endpoint_details.capabilities = json.loads(capabilities_string)
                            endpoint_details.description = self.get_db_value(result['Item']['Description'])
                            endpoint_details.display_categories = json.loads(self.get_db_value(result['Item']['DisplayCategories']))
                            endpoint_details.friendly_name = self.get_db_value(result['Item']['FriendlyName'])
                            endpoint_details.manufacturer_name = self.get_db_value(result['Item']['ManufacturerName'])
                            endpoint_details.sku = self.get_db_value(result['Item']['SKU'])
                            endpoint_details.user_id = self.get_db_value(result['Item']['UserId'])

                            adr.add_payload_endpoint(
                                friendly_name=endpoint_details.friendly_name,
                                endpoint_id=endpoint_details.id,
                                capabilities=endpoint_details.capabilities,
                                display_categories=endpoint_details.display_categories,
                                manufacturer_name=endpoint_details.manufacturer_name
                                )

                response = adr.get()

            if namespace == "Alexa.PowerController":
                name = json_object['directive']['header']['name']
                correlation_token = None
                if 'correlationToken' in json_object['directive']['header']:
                    correlation_token = json_object['directive']['header']['correlationToken']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']

                response_user_id = json.loads(ApiAuth.get_user_id(token).read().decode('utf-8'))
                if 'error' in response_user_id:
                    print('ERROR api_handler_directive.process.power_controller.user_id: ' + response_user_id['error_description'])
                user_id = response_user_id['user_id']
                print('LOG api_handler_directive.process.power_controller.user_id:', user_id)

                # Convert to a local stored state
                power_state_value = 'OFF' if name == "TurnOff" else 'ON'
                msg = {
                    'state': {
                        'desired':
                            {
                                'powerState': 'ON'
                            }
                    }
                }

                msg['state']['desired']['powerState'] = power_state_value
                mqtt_msg = json.dumps(msg)
                # Send the state to the Thing Shadow
                try:
                    response_update = iot_data_aws.update_thing_shadow(thingName=endpoint_id, payload=mqtt_msg.encode())
                    print('LOG api_handler_directive.process.power_controller.response_update -----')
                    print(response_update)
                    alexa_response = AlexaResponse(token=token, correlation_token=correlation_token, endpoint_id=endpoint_id)
                    alexa_response.add_context_property(namespace='Alexa.PowerController', name='powerState', value=power_state_value)
                    alexa_response.add_context_property()
                    response = alexa_response.get()

                except ClientError as e:
                    print('ERR api_handler_directive.process.power_controller Exception:ClientError:', e)
                    response = AlexaResponse(name='ErrorResponse', message=e).get()

            if namespace == "Alexa.ModeController":
                alexa_error_response = AlexaResponse(name='ErrorResponse')
                alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': 'Not Yet Implemented'})
                response = alexa_error_response.get()

            if namespace == "Alexa.RangeController":
                name = json_object['directive']['header']['name']
                correlation_token = json_object['directive']['header']['correlationToken']
                instance = json_object['directive']['header']['instance']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']
                
                result = dynamodb_aws.get_item(TableName='SampleEndpointDetails', Key={'EndpointId': {'S': endpoint_id}})
                capabilities_string = self.get_db_value(result['Item']['Capabilities'])
                capabilities = json.loads(capabilities_string)
                
                for c in capabilities:
                    if 'instance' in c and c['instance'] == instance:
                        MIN_VAL = c['configuration']['supportedRange']['minimumValue']
                        MAX_VAL = c['configuration']['supportedRange']['maximumValue']
                        PREC = c['configuration']['supportedRange']['precision']
                        break
                
                alexa_response = AlexaResponse(endpoint_id=endpoint_id, correlation_token=correlation_token, token=token)
                value = 0
                if name == "AdjustRangeValue":
                    range_value_delta = json_object['directive']['payload']['rangeValueDelta']
                    range_value_delta_default = json_object['directive']['payload']['rangeValueDeltaDefault']
                    reported_range_value = 0

                    # Check to see if we need to use the delta default value (The user did not give a precision)
                    if range_value_delta_default:
                        range_value_delta = PREC

                    # Lookup the existing value of the endpoint by endpoint_id and limit ranges as appropriate - for this sample, expecting 1-6
                    try:
                        response = iot_data_aws.get_thing_shadow(thingName=endpoint_id)
                        payload = json.loads(response['payload'].read())
                        reported_range_value = payload['state']['reported'][instance + '.rangeValue']
                        print('LOG api_handler_directive.process.range_controller.range_value:', reported_range_value)
                    except ClientError as e:
                        print(e)
                    except KeyError as errorKey:
                        print('Could not find key:', errorKey)

                    new_range_value = reported_range_value + range_value_delta

                    value = max(min(new_range_value, MAX_VAL), MIN_VAL)

                if name == "SetRangeValue":
                    range_value = json_object['directive']['payload']['rangeValue']

                    value = max(min(range_value, MAX_VAL), MIN_VAL)
                    alexa_response.add_context_property(
                        namespace='Alexa.RangeController',
                        name='rangeValue',
                        value=value)

                # Update the Thing Shadow
                msg = {'state': {'desired': {}}}
                # NOTE: The instance is used to keep the stored value unique
                msg['state']['desired'][instance + '.rangeValue'] = value
                mqtt_msg = json.dumps(msg)
                response_update = iot_data_aws.update_thing_shadow(thingName=endpoint_id, payload=mqtt_msg.encode())
                print('LOG api_handler_directive.process.range_controller.response_update -----')
                print(response_update)

                # Send back the response
                response = alexa_response.get()

            if namespace == "Alexa.ToggleController":
                name = json_object['directive']['header']['name']
                correlation_token = json_object['directive']['header']['correlationToken']
                instance = json_object['directive']['header']['instance']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']

                # Convert to a local stored state
                toggle_state_value = 'OFF' if name == "TurnOff" else 'ON'
                state_name = instance + '.state'
                msg = {
                    'state': {
                        'desired':
                            {
                                state_name: 'ON'
                            }
                    }
                }
                msg['state']['desired'][state_name] = toggle_state_value
                mqtt_msg = json.dumps(msg)
                # Send the state to the Thing Shadow
                try:
                    response_update = iot_data_aws.update_thing_shadow(thingName=endpoint_id, payload=mqtt_msg.encode())
                    print('LOG api_handler_directive.process.toggle_controller.response_update -----')
                    print(response_update)
                    alexa_response = AlexaResponse(token=token, correlation_token=correlation_token, endpoint_id=endpoint_id)
                    alexa_response.add_context_property(
                        namespace='Alexa.ToggleController',
                        name='toggleState',
                        instance=instance,
                        value=toggle_state_value)
                    alexa_response.add_context_property()
                    response = alexa_response.get()

                except ClientError as e:
                    print('ERR api_handler_directive.process.toggle_controller Exception:ClientError:', e)
                    response = AlexaResponse(name='ErrorResponse', message=e).get()

        else:
            alexa_error_response = AlexaResponse(name='ErrorResponse')
            alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': 'Empty Body'})
            response = alexa_error_response.get()

        if response is None:
            # response set to None indicates an unhandled directive, review the logs
            alexa_error_response = AlexaResponse(name='ErrorResponse')
            alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': 'Empty Response: No response processed. Unhandled Directive.'})
            response = alexa_error_response.get()

        print('LOG api_handler_directive.process.response -----')
        print(json.dumps(response))
        return response


def validate_response(response):
    valid = False
    try:
        with open('alexa_smart_home_message_schema.json', 'r') as schema_file:
            json_schema = json.load(schema_file)
            validate(response, json_schema)
        valid = True
    except SchemaError as se:
        print('LOG api_handler_directive.validate_response: Invalid Schema')
        print(se.context)
    except ValidationError as ve:
        print('LOG api_handler_directive.validate_response: Invalid Content')
        print(ve.context)

    return valid
