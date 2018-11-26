# Step 9: Send an Event
Send an external event into Alexa from the Endpoint Device backend. This simulates an external event on the endpoint that will need to be updated with Alexa.


#### <span style="color:#aaa">9.1</span> Send a Proactive State Update

<span style="color:#ccc">9.1.1</span> In Postman, and within the *Endpoints* sub-folder, open the **POST** _/events_ resource from the left menu.

<span style="color:#ccc">9.1.2</span> Select the _Body_ tab and view the raw JSON. It should look like the following:

```
{
    "event": {
        "type": "ChangeReport",
        "endpoint": {
            "userId": "{{user_id}}",
            "id": "{{endpoint_id}}",
            "state": "OFF",
            "type": "SWITCH",
            "sku": "SW00"
        }
    }
}
```
Note that the `user_id` and `endpoint_id` are variables that can be updated via the Postman environment variables.

<span style="color:#ccc">9.1.3</span> Update the Postman environment variables by replacing the `user_id` "0" value with the [user_id] stored in the `config.txt` file. Additionally, replace the `endpoint_id` value with the Thing name from AWS IoT for the Sample Black Switch created. When edited, it should something like the following:

```
{
  "event": {
    "endpoint": {
    	"userId" : "amzn1.account.XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    	"id": "b0dcb3f0-db26-4462-8cf1-15fc97972eac",
    	"state": "OFF",
    	"type": "SWITCH",
        "sku": "SW00"
    }
  }
}
```

<span style="color:#ccc">9.1.1</span> Click **Save** in the top right and then and then click the **Send** button.

<span style="color:#ccc">9.1.2</span> Return to the [AWS IoT Things console](https://console.aws.amazon.com/iotv2/home?region=us-east-1#/thinghub) and note the _state_ value of the created Black Sample Switch. The state should reflect the _"state"_ value passed in the body. For instance, if set to _"OFF"_, the attribute _state_ will be set to _OFF_.

Finally, while that method updates the Endpoint Cloud data, you can see the state of the response sent to the Alexa event gateway in Postman on the right of the Response section. A 202 value of `Accepted` indicates the message was received. For a full list of Success responses and errors, visit the documentation at [https://developer.amazon.com/docs/smarthome/send-events-to-the-alexa-event-gateway.html#success-response-and-errors](https://developer.amazon.com/docs/smarthome/send-events-to-the-alexa-event-gateway.html#success-response-and-errors). If ultimately successful, the state of the Black Sample Switch will change in the Alexa web and mobile applications.

<br>

____
Go to [Step 10: Clean Up](10-cleanup.md).

____
Return to the [Instructions](README.md)