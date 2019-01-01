# -*- coding: utf-8 -*-

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import datetime
import random
import string


class ApiUtils:

    @staticmethod
    def check_response(response):
        if response is None:
            print('ERR ApiUtils.check_response is None')
            return False
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print('ERR ApiUtils.check_response.HTTPStatusCode', response)
            return False
        else:
            return True

    @staticmethod
    def get_time_utc():
        """
        An ISO 8601 formatted string in UTC (e.g. YYYY-MM-DDThh:mm:ss.sD)
        :return: string date time
        """
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def get_code_string(size):
        """
        A code string composed of uppercase ASCII and digits
        :param size:  The length of the code as an int
        :return: string code
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=size))

    @staticmethod
    def get_random_color_string():
        """
        A random color name string composed of uppercase ASCII and digits
        :return: string color
        """
        return random.choice(['Beige', 'Blue', 'Brown', 'Cyan', 'Green', 'Magenta', 'Orange', 'Red', 'Violet', 'Yellow'])
