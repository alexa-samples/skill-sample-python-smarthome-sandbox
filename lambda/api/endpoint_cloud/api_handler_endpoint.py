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

import boto3
from botocore.exceptions import ClientError

from endpoint_cloud.api_handler_event import ApiHandlerEvent
from .api_utils import ApiUtils

dynamodb_aws = boto3.client('dynamodb')
iot_aws = boto3.client('iot')

samples_thing_group_name = 'Samples'


class ApiHandlerEndpoint:
    class EndpointDetails:
        def __init__(self):
            self.capabilities = ''
            self.description = 'Sample Description'
            self.display_categories = 'OTHER'
            self.friendly_name = ApiUtils.get_random_color_string() + ' Sample Endpoint'
            self.id = 'SAMPLE_ENDPOINT_' + ApiUtils.get_code_string(8)
            self.manufacturer_name = 'Sample Manufacturer'
            self.sku = 'OT00'
            self.user_id = '0'

        def dump(self):
            print('EndpointDetails -----')
            print('capabilities:', self.capabilities)
            print('description:', self.description)
            print('display_categories:', self.display_categories)
            print('friendly_name:', self.friendly_name)
            print('id:', self.id)
            print('manufacturer_name:', self.manufacturer_name)
            print('sku:', self.sku)
            print('user_id:', self.user_id)

    @staticmethod
    def add_thing_to_thing_group(thing_name):
        response = iot_aws.add_thing_to_thing_group(thingGroupName=samples_thing_group_name, thingName=thing_name)
        print('LOG api_handler_endpoint.add_thing_to_thing_group -----')
        print(json.dumps(response))
        return response

    @staticmethod
    def check_thing_group_name_exists():
        thing_groups = iot_aws.list_thing_groups(namePrefixFilter=samples_thing_group_name, recursive=False)
        if 'thingGroups' in thing_groups:
            for thing_group in thing_groups['thingGroups']:
                if thing_group['groupName'] == samples_thing_group_name:
                    print('checkForThingGroup found', samples_thing_group_name)
                    return True
        return False

    def create(self, request):
        try:
            endpoint_details = self.EndpointDetails()

            # Map our incoming API body to a thing that will virtually represent a discoverable device for Alexa
            json_object = json.loads(request['body'])
            endpoint = json_object['event']['endpoint']
            endpoint_details.user_id = endpoint['userId']  # Expect a Profile
            endpoint_details.capabilities = endpoint['capabilities']
            endpoint_details.sku = endpoint['sku']  # A custom endpoint type, ex: SW01

            if 'friendlyName' in endpoint:
                endpoint_details.friendly_name = endpoint['friendlyName']

            if 'manufacturerName' in endpoint:
                endpoint_details.manufacturer_name = endpoint['manufacturerName']

            if 'description' in endpoint:
                endpoint_details.description = endpoint['description']

            if 'displayCategories' in endpoint:
                endpoint_details.display_categories = endpoint['displayCategories']

            # Validate the Samples group is available, if not, create it
            thing_group_name_exists = self.check_thing_group_name_exists()
            if not thing_group_name_exists:
                response = self.create_thing_group(samples_thing_group_name)
                if not ApiUtils.check_response(response):
                    print('ERR api_handler_endpoint.create.create_thing_group.response', response)

            # Create the thing in AWS IoT
            response = self.create_thing(endpoint_details)
            if not ApiUtils.check_response(response):
                print('ERR api_handler_endpoint.create.create_thing.response', response)
                
            # Create the thing details in DynamoDb
            response = self.create_thing_details(endpoint_details)
            if not ApiUtils.check_response(response):
                print('ERR api_handler_endpoint.create.create_thing_details.response', response)

            # Add the thing to the Samples Thing Group
            response = self.add_thing_to_thing_group(endpoint_details.id)
            if not ApiUtils.check_response(response):
                print('ERR api_handler_endpoint.create.add_thing_to_thing_group.response', response)

            # Send an Event that updates Alexa
            endpoint = {
                'userId': endpoint_details.user_id,
                'id': endpoint_details.id,
                'friendlyName': endpoint_details.friendly_name,
                'sku': endpoint_details.sku,
                'capabilities': endpoint_details.capabilities
            }

            # Package into an Endpoint Cloud Event
            event_request = {'event': {'type': 'AddOrUpdateReport', 'endpoint': endpoint}}
            event_body = {'body': json.dumps(event_request)}
            event = ApiHandlerEvent().create(event_body)
            print(json.dumps(event, indent=2))
            return response

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

    def create_thing(self, endpoint_details):
        print('LOG api_handler_endpoint.create_thing -----')
        # Create the ThingType if missing
        thing_type_name = self.create_thing_type(endpoint_details.sku)
        try:
            response = iot_aws.create_thing(
                thingName=endpoint_details.id,
                thingTypeName=thing_type_name,
                attributePayload={
                    'attributes': {
                        'user_id': endpoint_details.user_id
                    }
                }
            )

            print(json.dumps(response))
            return response

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print('WARN iot resource already exists, trying update')
                return self.update_thing(endpoint_details)
        except Exception as e:
            print(e)
            return None
            
    @staticmethod
    def create_thing_details(endpoint_details):
        print('LOG api_handler_endpoint.create_thing_details -----')
        print('LOG api_handler_endpoint.create_thing_details.endpoint_details', endpoint_details.dump())
        dynamodb_aws_resource = boto3.resource('dynamodb')
        table = dynamodb_aws_resource.Table('SampleEndpointDetails')
        print('LOG api_handler_endpoint.create_thing_details Updating Item in SampleEndpointDetails')
        try:
            response = table.update_item(
                Key={
                    'EndpointId': endpoint_details.id
                },
                UpdateExpression='SET \
                        Capabilities = :capabilities, \
                        Description = :description, \
                        DisplayCategories = :display_categories, \
                        FriendlyName = :friendly_name, \
                        ManufacturerName = :manufacturer_name, \
                        SKU = :sku, \
                        UserId = :user_id',
                ExpressionAttributeValues={
                    ':capabilities': str(json.dumps(endpoint_details.capabilities)),
                    ':description': str(endpoint_details.description),
                    ':display_categories': str(json.dumps(endpoint_details.display_categories)),
                    ':friendly_name': str(endpoint_details.friendly_name),
                    ':manufacturer_name': str(endpoint_details.manufacturer_name),
                    ':sku': str(endpoint_details.sku),
                    ':user_id': str(endpoint_details.user_id)

                }
            )
            print(json.dumps(response))
            return response
        except Exception as e:
            print(e)
            return None


    @staticmethod
    def create_thing_group(thing_group_name):
        print('LOG api_handler_endpoint.create_thing_group -----')
        response = iot_aws.create_thing_group(
            thingGroupName=thing_group_name
        )
        print(json.dumps(response))
        return response

    @staticmethod
    def create_thing_type(sku):
        print('LOG api_handler_endpoint.create_thing_type -----')
        # Set the default at OTHER (OT00)
        thing_type_name = 'SampleOther'
        thing_type_description = 'A sample endpoint'

        if sku.upper().startswith('LI'):
            thing_type_name = 'SampleLight'
            thing_type_description = 'A sample light endpoint'

        if sku.upper().startswith('MW'):
            thing_type_name = 'SampleMicrowave'
            thing_type_description = 'A sample microwave endpoint'

        if sku.upper().startswith('SW'):
            thing_type_name = 'SampleSwitch'
            thing_type_description = 'A sample switch endpoint'

        if sku.upper().startswith('TT'):
            thing_type_name = 'SampleToaster'
            thing_type_description = 'A sample toaster endpoint'

        response = {}
        try:
            response = iot_aws.create_thing_type(
                thingTypeName=thing_type_name,
                thingTypeProperties={
                    'thingTypeDescription': thing_type_description
                }
            )
        except ClientError as e:
            print(e, e.response)

        print(json.dumps(response))
        return thing_type_name

    def delete(self, request):
        try:
            response = {}
            print(request)
            json_object = json.loads(request['body'])
            endpoint_ids = []
            delete_all_sample_endpoints = False
            for endpoint_id in json_object:
                # Special Case for * - If any match, delete all
                if endpoint_id == '*':
                    delete_all_sample_endpoints = True
                    break
                endpoint_ids.append(endpoint_id)

            if delete_all_sample_endpoints is True:
                self.delete_samples()
                response = {'message': 'Deleted all sample endpoints'}

            for endpoint_id in endpoint_ids:
                iot_aws.delete_thing(thingName=endpoint_id)
                response = dynamodb_aws.delete_item(TableName='SampleEndpointDetails', Key={'EndpointId': endpoint_id})
                # TODO Check Response
                # TODO UPDATE ALEXA!
                # Send AddOrUpdateReport to Alexa Event Gateway

            return response

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

    def delete_samples(self):
        table = boto3.resource('dynamodb').Table('SampleEndpointDetails')
        result = table.scan()
        items = result['Items']
        for item in items:
            endpoint_id = item['EndpointId']
            self.delete_thing(endpoint_id)

    # TODO Improve response handling
    @staticmethod
    def delete_thing(endpoint_id):

        # Delete from DynamoDB
        response = dynamodb_aws.delete_item(
            TableName='SampleEndpointDetails',
            Key={'EndpointId': {'S': endpoint_id}}
        )
        print('LOG api_handler_endpoint.delete_thing.dynamodb_aws.delete_item.response -----')
        print(response)

        # Delete from AWS IoT
        response = iot_aws.delete_thing(
            thingName=endpoint_id
        )
        print('LOG api_handler_endpoint.delete_thing.iot_aws.delete_item.response -----')
        print(response)
        return response

    def read(self, request):
        try:
            response = {}
            resource = request['resource']
            if resource == '/endpoints':
                parameters = request['queryStringParameters']
                if parameters is not None and 'endpoint_id' in parameters:
                    endpoint_id = request['queryStringParameters']['endpoint_id']
                    response = self.read_thing(endpoint_id)
                else:
                    list_response = iot_aws.list_things()
                    # TODO List things only in the Samples Thing Group
                    # list_response = iot_aws.list_things_in_thing_group(thingGroupName=thing_group_name)
                    status = list_response['ResponseMetadata']['HTTPStatusCode']
                    if 200 <= int(status) < 300:
                        things = list_response['things']
                        response = []
                        for thing in things:
                            response.append(thing)

            print('LOG api_handler_endpoint.read -----')
            print(json.dumps(response))
            return response

        except ClientError as client_error:
            return "ClientError: " + str(client_error)

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

    @staticmethod
    def read_thing(endpoint_id):
        return iot_aws.describe_thing(thingName=endpoint_id)

    # TODO Work in Progress: Update the Endpoint Details
    @staticmethod
    def update(request):
        raise NotImplementedError()
        # TODO Get the endpoint ID
        # TODO With the endpoint ID, Get the endpoint information from IoT
        # TODO With the endpoint ID, Get the endpoint details from DDB
        #     Get the endpoint as JSON pre-configured
        # TODO Send a command to IoT to update the endpoint
        # TODO Send a command to DDB to update the endpoint
        # TODO UPDATE ALEXA!
        # Send AddOrUpdateReport to Alexa Event Gateway

    # TODO Work in Progress: Update Endpoint States
    @staticmethod
    def update_states(request, states):
        raise NotImplementedError()
        # TODO Get the endpoint ID
        # TODO With the endpoint ID, Get the endpoint information from IoT
        # TODO With the endpoint ID, Get the endpoint details from DDB
        #     Get the endpoint as JSON pre-configured
        # TODO Send a command to IoT to update the endpoint
        # TODO Send a command to DDB to update the endpoint
        # TODO UPDATE ALEXA!
        # Send ChangeReport to Alexa Event Gateway

    def update_thing(self, endpoint_details):
        # Create the ThingType if missing
        thing_type_name = self.create_thing_type(endpoint_details.sku)
        response = iot_aws.update_thing(
            thingName=endpoint_details.id,
            thingTypeName=thing_type_name,
            attributePayload={
                'attributes': {
                    'user_id': endpoint_details.user_id
                }
            }
        )
        return response
