# Create the Smart Home Sample Sandbox
These instructions create the backend services needed by the Smart Home Skill using a Cloud Formation stack.

> You will need an Amazon Web Services account and and Amazon Developer account. For Boto3, you will need valid AWS credentials configured. Review the Boto3 Credentials documentation at https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html.

### <span style="color:#aaa">1</span> Get your Vendor ID
To see your Vendor ID, go to https://developer.amazon.com/mycid.html and sign in with your Amazon Developer account if prompted.

### <span style="color:#aaa">2</span> Create a Login With Amazon Profile
<span style="color:#ccc">2.1</span> Go to https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html and sign in with your Amazon Developer account if prompted.
<span style="color:#ccc">2.2</span> Click on **Create a New Security Profile** and enter the following values:

For the Security Profile Name: `Smart Home Sandbox`

For the Security Profile Description: `A sample sandbox for Alexa skill development`.

For the Consent Privacy Notice URL: `https://example.com/privacy.html`

<span style="color:#ccc">2.3</span> Click the **Save** button.
<span style="color:#ccc">2.4</span> Click the gear icon and select Web Settings.
<span style="color:#ccc">2.5</span> Click the **Edit** button.
<span style="color:#ccc">2.6</span> Replace VENDOR_ID with your unique Vendor ID and add 4 Allowed Return URLs:
``` 
https://pitangui.amazon.com/api/skill/link/VENDOR_ID
https://layla.amazon.com/api/skill/link/VENDOR_ID
https://alexa.amazon.co.jp/api/skill/link/VENDOR_ID
http://127.0.0.1:9090/cb
``` 
<span style="color:#ccc">2.7</span> Click the **Save** button.
> Leave the page open to copy the Client ID and Secret

### <span style="color:#aaa">3</span> Download the Source
3.1 Clone the source into a working directory using the command: `git clone https://github.com/alexa/skill-sample-python-smarthome-sandbox` 
> Optionally [download the master branch as a zip](https://github.com/alexa/skill-sample-python-smarthome-sandbox/archive/master.zip) and extract it to a working directory.

### <span style="color:#aaa">4</span> Run the client script
4.1 From the command line, navigate to the cloned repository `skill-sample-python-smarthome-sandbox/client` folder.

4.2 Within the */client* folder, run `pip install boto3`

4.3 To run the sandbox, then run `python sandbox.py`

4.4 Enter the Vendor ID, LWA Client ID, and LWA Client Secret when prompted
	 
### <span style="color:#aaa">5</span> Enable the skill
5.1 When the sandbox setup is complete, you can then enable the skill via alexa.amazon.com by going to https://alexa.amazon.com/spa/index.html#skills/your-skills/?ref-suffix=ysa_gw and selecting **DEV SKILLS** from the menu.

### <span style="color:#aaa">6</span> Test the skill
6.1 Go to https://developer.amazon.com/alexa/console/ask/ and open the **Smart Home Sandbox** skill.

6.2 Navigate to the **Test** tab and try some of the following commands with Alexa:
```
turn on black switch
turn on white switch
turn off black swtich
turn off white switch
set sample toaster heat to six
turn on bagel mode of sample toaster
turn off sample toaster frozen mode 
```

Look through the CloudWatch logs for flow and the related AWS IoT Things for state.


____
Return to the [Instructions](README.md)
