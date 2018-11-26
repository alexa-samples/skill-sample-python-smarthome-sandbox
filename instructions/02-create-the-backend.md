# Step 2: Create the Smart Home Skill Backend
These instructions create the backend services needed by the Smart Home Skill using a Cloud Formation stack.

#### <span style="color:#aaa">2.1</span> Create the Backend Stack

<span style="color:#ccc">2.1.1</span> Navigate to the Cloud Formation Console at [https://console.aws.amazon.com/cloudformation/home?region=us-east-1](https://console.aws.amazon.com/cloudformation/home?region=us-east-1) and authenticate using your AWS account.

<span style="color:#ccc">2.1.2</span> Verify you are in the N. Virginia (us-east-1) region and click the **Create Stack** button.

<span style="color:#ccc">2.1.3</span> In the _Specify Template_ section, select the **Amazon S3 template URL** radio button and enter the following URL `https://s3.amazonaws.com/endpoint-code-us/backend.template` into the S3 URL field.

<span style="color:#ccc">2.1.4</span> Click **Next** on the bottom right of the page.

<span style="color:#ccc">2.1.5</span> On the _Create Stack_ page and in the **Stack name** text input box, enter `Smart-Home-Sample-Backend` and then click **Next**.

<span style="color:#ccc">2.1.6</span> When on the _Configure stack options_ page, click **Next** without making any changes.

<span style="color:#ccc">2.1.7</span> On the _Review Smart-Home-Sample-Backend_ page, click the checkbox "I acknowledge that AWS CloudFormation might create IAM resources with custom names." and then click the **Create** button.

> This IAM resource warning comes from the need for the Stack to create an Execution Role for the created Lambda functions.

<span style="color:#ccc">2.1.8</span> In the Stacks list in the Cloud Formation console, the newly created Sample-Smart-Home-Backend stack will be created and initially have a status of _CREATE\_IN\_PROGRESS_. When the backend stack has been created and is ready, the status will change to _CREATE\_COMPLETE_. This may take 1-3 minutes.

> If any issues arise, you should see a ROLLBACK\_IN\_PROGRESS message and ultimately a ROLLBACK\_COMPLETE status.

#### <span style="color:#aaa">2.2</span> Locate the _Sample-Smart-Home-Backend_ Stack Outputs

<span style="color:#ccc">2.2.1</span> While still in the Cloud Formation console, select the check box for _Smart-Home-Sample-Backend_ and then select the _Outputs_ details tab.

<span style="color:#ccc">2.2.2</span> Locate the _EndpointApiId_ **Value** that will look something like the following example: `y053kmfr5m` and copy it to the `setup.txt` file into the [EndpointApiId] section.

<span style="color:#ccc">2.2.3</span> Locate the _SkillLambdaArn_ **Value** that is formatted like the following example: `arn:aws:lambda:us-east-1:############:function:SampleSkillAdapter` and copy it into the [SkillLambdaArn] section of `setup.txt`.

	
<br>

____
Go to [Step 3: Set Up Login with Amazon](03-setup-lwa.md).

____
Return to the [Instructions](README.md)