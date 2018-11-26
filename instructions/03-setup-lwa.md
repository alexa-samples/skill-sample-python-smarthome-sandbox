# Step 3: Set Up Login with Amazon
For the sample environment, a development Login with Amazon (LWA) security profile will be used for configuring Account Linking, which is required for a Smart Home Skill. 

#### <span style="color:#aaa">3.1</span> Create a Login with Amazon Security Profile

<span style="color:#ccc">3.1.1</span> In your web browser, go to [https://developer.amazon.com/lwa/sp/overview.html](https://developer.amazon.com/lwa/sp/overview.html) and make sure _APPS & SERVICES_ is selected in the top menu and _Login with Amazon_ is selected in the sub menu.

<span style="color:#ccc">3.1.2</span> On the _Login with Amazon_ page, click the **Create a New Security Profile** button.

<span style="color:#ccc">3.1.3</span> On the Security Profile Management page, enter `Sample Alexa Smart Home` for the **Security Profile Name**.

<span style="color:#ccc">3.1.4</span> For the **Security Profile Description** enter `A sample security profile for Alexa Smart Home Skill development`.

<span style="color:#ccc">3.1.5</span> For the **Consent Privacy Notice URL** enter `http://example.com/privacy.html` for illustrative purposes or use your own if you already have a public consent privacy policy.

> For a production Smart Home Skill, a valid consent privacy notice will be required.

<span style="color:#ccc">3.1.6</span> For the **Consent Logo Image** download [https://github.com/alexa/skill-sample-python-smarthome-iot/raw/master/instructions/img/alexa-sample-smarthome-150x.png](https://github.com/alexa/skill-sample-python-smarthome-iot/raw/master/instructions/img/alexa-sample-smarthome-150x.png) into the `Alexa-SmartHome-Sample` directory created on your Desktop and then click the **Upload Image** area to load the file from where you saved it.

<span style="color:#ccc">3.1.7</span> If your profile configuration looks like the following, click **Save** on the Security Profile Management page.

![Security Profile Configuration](img/3.1.7-lwa-profile-configuration.png "Security Profile Configuration")


> If successful, a message similar to 'Login with Amazon successfully enabled for Security Profile. Click (gear) to manage Security Profile.' will be returned.

<span style="color:#ccc">3.1.8</span> From the list of Security Profiles, click the **Show Client ID and Client Secret** link for the _Sample Alexa Smart Home_ profile.

<span style="color:#ccc">3.1.9</span> Copy the displayed Client ID and Client Secret values to the `setup.txt` file replacing the template entries for [Login with Amazon Client ID] and [Login with Amazon Client Secret] respectively:

```
[Login with Amazon Client ID]
amzn1.application-oa2-client.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[Login with Amazon Client Secret]
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
> Further configuration of the Security Profile Allowed Return URLs will be done during configuration of the Alexa Smart Home Skill.

<br>

____
Go to [Step 4: Create the Alexa Smart Home Skill](04-create-skill-smarthome.md).

____
Return to the [Instructions](README.md)