# Step 1: Verify Requirements
These are the required accounts and resources needed for working through these instructions.

#### <span style="color:#aaa">1.0</span> Verify the Required Accounts
To work with these instructions, you will need both an Amazon Developer account and an Amazon Web Services account.

##### Amazon Developer Account
Go to [https://developer.amazon.com](https://developer.amazon.com) and establish an account if you do not already have one.

##### Amazon Web Services Account
Go to [https://aws.amazon.com](https://aws.amazon.com) and register for an Amazon Web Services (AWS) account if you do not already have one.

#### <span style="color:#aaa">1.1</span> Open a Setup File
This setup file is useful to store temporary IDs and other values during configuration of the environment.
 
<span style="color:#ccc">1.1.1</span> Create a folder on your Desktop called `Alexa-SmartHome-Sample`.

<span style="color:#ccc">1.1.2</span> Download the [setup.txt](https://raw.githubusercontent.com/alexa/skill-sample-python-smarthome-iot/master/instructions/setup.txt) file into the `Alexa-SmartHome-Sample` folder.  

<span style="color:#ccc">1.1.3</span> Open and review the `setup.txt` file:

```
Set in Step 2 - A unique API ID and name for the Alexa Smart Home Skill Lambda function
[EndpointApiId]
XXXXXXXXXX

[SkillLambdaArn]
arn:aws:lambda:us-east-1:XXXXXXXXXXXX:function:SampleSkillAdapter

Set in Step 3 - The Client ID and Secret from the LWA Security Profile
[Login with Amazon Client ID]
amzn1.application-oa2-client.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[Login with Amazon Client Secret]
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Set in Step 4 - A unique ID for the Alexa Smart Home Skill
[Alexa Skill Application Id]
amzn1.ask.skill.XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

Set in Step 5 - The Messaging Client and Secret from the Alexa Smart Home Skill
[Alexa Skill Messaging Client Id]
amzn1.application-oa2-client.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[Alexa Skill Messaging Client Secret]
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Set in Step 7 - The profile user_id of the User
[user_id]
amzn1.account.XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

These placeholders represent the configuration entities to be collected or created for the environment.

> TIP Keep secrets safe. If a Client Secret is compromised or needs to be reset, you will have to discard the secret and regenerate the Client ID and Secret again or recreate the profile. This will immediately sever the existing access relationships and customers will have to re-authenticate or re-link their account or skill.

<br>

____
Go to [Step 2: Create the Smart Home Skill Backend](02-create-the-backend.md).

____
Return to the [Instructions](README.md)
