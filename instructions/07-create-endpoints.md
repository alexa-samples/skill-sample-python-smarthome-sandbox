# Step 7: Create the Endpoints
Create endpoints to be discovered during the Alexa Smart Home Skill Discovery.

#### <span style="color:#aaa">7.1</span> Collect the User Id
The JSON template for creating an endpoint defaults the User Id to `0`. This is useful for testing simulated calls to your AWS Lambda for a variety of directives with a known (and invalid) User Id. To associate the device with an actual Amazon account, the correct User Id obtained with the access token must be used. During skill enablement, the credentials are saved to DynamoDB into the SampleUsers table for reference.
> The credentials in the SampleUsers table are for development reference only and should be stored securely in a production environment.

<span style="color:#ccc">7.2.1</span> Go to [https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:selected=SampleUsers](https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:selected=SampleUsers) and select the **Items** tab.

<span style="color:#ccc">7.2.2</span> In the list of _SampleUsers_ select the first entry UserId column that has the following format:
```
amzn1.account.XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

<span style="color:#ccc">7.2.3</span> Copy the UserId value and save it to the [user_id] section of the `setup.txt` file. The User Id is used to identify devices associated with the Amazon account.

#### <span style="color:#aaa">7.2</span> Set Up Postman
Postman is a tool for managing and executing HTTP requests and is very useful for API development and usage. To use it for the sample code, it must first be installed if not currently available on your system and have a sample environment configured for use.

##### <span style="color:#aaa">7.2.1</span> Install Postman
<span style="color:#ccc">7.2.1</span> Go to [getpostman.com](https://www.getpostman.com) and download and install the correct Postman application for your platform.

<span style="color:#ccc">7.2.2</span> Download the Postman Sample Smart Home Collection [skill-sample-smarthome-iot.postman_collection.json](https://raw.githubusercontent.com/alexa/skill-sample-python-smarthome-iot/master/instructions/skill-sample-smarthome-iot.postman_collection.json) file into the `Alexa-SmartHome-Sample` directory on your Desktop. Additionally, download the [skill-sample-smarthome-iot.postman_environment.json](https://raw.githubusercontent.com/alexa/skill-sample-python-smarthome-iot/master/instructions/skill-sample-smarthome-iot.postman_environment.json) file into the same directory.

##### <span style="color:#aaa">7.2.2</span> Import the *Alexa Smart Home (smarthome-iot)* Postman collection

<span style="color:#ccc">7.2.2.1</span> Open Postman.

<span style="color:#ccc">7.2.2.2</span> In Postman, click **Import** from the main menu and browse to the `skill-sample-smarthome-iot.postman_collection` file or drag it onto the _Import_ dialog.

##### <span style="color:#aaa">7.2.3</span> Import the Postman environment
To fill out the variable values of the configuration use a Postman environment to store configuration-specific values. The keys defined in double curly braces like `{{endpoint_api_id}}` will be auto-expanded in the URLs for the imported collection.

<span style="color:#ccc">7.2.3.1</span> In the top right of Postman, click the gear icon to open the _Environment options_ drop down menu and select **Manage Environments**.

![Postman - Manage Environments](img/7.2.3.1-postman-manage-environments.png "Postman - Manage Environments")

<span style="color:#ccc">7.2.3.2</span> In opened _Manage Environments_ dialog, click the **Import** button in the bottom right.

<span style="color:#ccc">7.2.3.3</span> Click the **Choose Files** button and open the `skill-sample-smarthome-iot.postman_environment.json` file downloaded into the `Alexa-SmartHome-Sample` directory.

<span style="color:#ccc">7.2.3.4</span> Click the *Alexa Smart Home (smarthome-iot)* environment and then select the value of the **Variable** value called `endpoint_api_id` and set its **Current Value** to the [EndpointApiId] value from the `setup.txt` file.

<span style="color:#ccc">7.2.3.5</span> Replace the `userId` current value (with a default of `0`) with your `user_id` value from the `setup.txt` file. This will associate the created thing with an Amazon account for device discovery.

> Note that the `user_id` defaults to 0 because this is useful for development and identifying a device created programmatically. However, Discovery for the Smart Home Skill would not find this device since it is expecting a `user_id` in the form of a profile from Login with Amazon.

<span style="color:#ccc">7.2.3.6</span> Click the **Update** button and then close the _MANAGE ENVIRONMENTS_ dialog and in the top right of Postman select the newly created *Alexa Smart Home (smarthome-iot)* environment from the  environment drop down menu.


#### <span style="color:#aaa">7.3</span> Create Endpoints
Use Postman to generate endpoints by selecting and sending stored requests from the Alexa Smart Home (sample_backend) collection.

<span style="color:#ccc">7.3.1</span> In Postman, from the left _Collections_ menu select and open the *Alexa Smart Home (smarthome-iot)* folder. In the *Endpoints* sub-folder, open the **POST** _/endpoints (Black Sample Switch)_ resource from the left menu.

<span style="color:#ccc">7.3.2</span> In Postman, select the **POST** _/endpoints (Black Sample Switch)_ resource from the left menu and then select the Body tab to show the raw body that would be sent from this request.

![Postman - Collections > Endpoints > Body](img/7.3.2-postman-collections-endpoints.png "Postman - Collections > Endpoints > Body")



<span style="color:#ccc">7.3.4</span> Once you have added your User Id value, click the **Send** button in the top right to send and create the endpoint.

<span style="color:#ccc">7.3.5</span> Return to the [AWS IoT Things console](https://console.aws.amazon.com/iotv2/home?region=us-east-1#/thinghub) and refresh the page. A new thing of the type `SAMPLESWITCH` should be available. It's name will be a generated GUID.

<span style="color:#ccc">7.3.6</span> Click on the thing identified with a thing type of `SAMPLESWITCH` to inspect its attributes. They should look something like the following:

![AWS IoT - SAMPLESWITCH](img/7.3.6-thing-sampleswitch.png "AWS IoT - SAMPLESWITCH")

The Globally Unique ID (GUID) representing the name of this device will correspond to an entry in the **SampleEndpointDetails** table that holds the details of the device for discovery. You can browse to the [SampleEndpointDetails DynamoDB Table](https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:selected=SampleEndpointDetails) and view the items entry to see the details stored in AWS.

With this Sample Switch Thing defined in the account you are using for Alexa, you should now be able to discover it as a virtual device.

> If you want to create other devices, look at the other options in the samples provided in the Postman collection and update the userId value in the POST body of the resource. Click **Send** to POST it to the endpoint API

<br>

____
Go to [Step 8: Test the Endpoints](08-test-endpoints.md).

____
Return to the [Instructions](README.md)