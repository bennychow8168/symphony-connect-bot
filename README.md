# Symphony Connect Bot

## Overview
This Python bot allows you to add / onboard a new contact to the Symphony WeChat & WhatsApp Connect platform.
This new contact will be added as a contact with the originating requestor.
Optionally, this new contact can also be added to a existing Room or a new Room.

Please follow the steps below to set up the bot to run in your Symphony pod. Once the bot is running, please open a 1-1 Chat with the bot and enter "/help" for further usage instructions.

## Environment Setup
This client is compatible with **Python 3.6 or above**

Create a virtual environment by executing the following command **(optional)**:
``python3 -m venv ./venv``

Activate the virtual environment **(optional)**:
``source ./venv/bin/activate``

Install dependencies required for this client by executing the command below.
``pip install -r requirements.txt``


## Getting Started
### 1 - Prepare RSA Key pair
You will first need to generate a **RSA Public/Private Key Pair**.
- Send the **Public** key to Symphony Support Team in order to set up 
- Private Key will be required in steps below
- In return, Symphony team will provide a publicKeyID which you will need to populate in the config.json file below

You will also need to set up a [Symphony Service Account](https://support.symphony.com/hc/en-us/articles/360000720863-Create-a-new-service-account), which is a type of account that applications use to work with Symphony APIs. Please contact with Symphony Admin in your company to get the account.

**RSA Public/Private Key Pair** is the recommended authentication mechanism by Symphony, due to its robust security and simplicity.


### 2 - Upload Service Account Private Key
Please copy the private key file (*.pem) to the **rsa** folder. You will need to configure this in the next step.

Please also upload the private key for Symphony Service Account created above in **rsa** folder.

### 3 - Update resources

To run the script, you will need to configure **bot_config.json** and **connect_config.json** provided in the **resources** directory. 

**Notes:**

You also need to update based on the service account created above:
- apiURL (please confirm this with Symphony team)
- privateKeyPath (ends with a trailing "/"))
- privateKeyName
- publicKeyId (please confirm this with Symphony team)
- podId (please confirm this with Symphony team)


Sample connect_config.json:

    {
      "apiURL": "xxx.symphony.com",
      "privateKeyPath":"./rsa/",
      "privateKeyName": "privateKey.pem",
      "publicKeyId": "xxx",
      "podId": "xxx",
      "proxyURL": "",
      "proxyUsername": "",
      "proxyPassword": "",
      "truststorePath": ""
    }



Sample bot_config.json:

    {
      "sessionAuthHost": "<POD>.symphony.com",
      "sessionAuthPort": 443,
      "keyAuthHost": "<POD-KM>.symphony.com",
      "keyAuthPort": 443,
      "podHost": "<POD>.symphony.com",
      "podPort": 443,
      "agentHost": "<POD-AGENT>.symphony.com",
      "agentPort": 443,
      "authType": "rsa",
      "botPrivateKeyPath":"./rsa/",
      "botPrivateKeyName": "<Service_Account>-private-key.pem",
      "botCertPath": "",
      "botCertName": "",
      "botCertPassword": "",
      "botUsername": "<Service_Account>",
      "botEmailAddress": "<Service_Account>@symphony.com",
      "appCertPath": "",
      "appCertName": "",
      "appCertPassword": "",
      "authTokenRefreshPeriod": "30",
      "proxyURL": "",
      "proxyUsername": "",
      "proxyPassword": "",
      "podProxyURL": "",
      "podProxyUsername": "",
      "podProxyPassword": "",
      "agentProxyURL": "",
      "agentProxyUsername": "",
      "agentProxyPassword": "",
      "keyManagerProxyURL": "",
      "keyManagerProxyUsername": "",
      "keyManagerProxyPassword": "",
      "truststorePath": ""
    }


### 5 - Run script
The script can be executed by running
``python3 main.py`` 


# Release Notes

## 0.1
- Initial Release
