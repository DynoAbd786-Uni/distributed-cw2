# Distributed Systems Coursework 2

## Project Overview
This project implements a serverless workflow using Azure Functions, designed to demonstrate a distributed systems solution for an ERP-like inventory management system.

## Prerequisites

### Local Development Requirements
- [Visual Studio Code](https://code.visualstudio.com/)
- [Azure Functions extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
- [Azurite V3 extension](https://marketplace.visualstudio.com/items?itemName=Azurite.azurite) for local storage emulation
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
- [Python 3.8+](https://www.python.org/downloads/)
- [SendGrid Account](https://sendgrid.com/en-us/solutions/email-api)
- [Azure Cosmos DB Account](https://azure.microsoft.com/en-us/services/cosmos-db/)

## Instructions for activation


### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2. Create local.settings.json
Create a local.settings.json file in the project root with the following template:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<Your Azure WebJobs Storage Connection String>",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DATABASE_AND_CONTAINER_NAME": "<Your Cosmos DB Database and Container Name>",
    "CompanyInventoryCosmosDBConnectionString": "<Your Cosmos DB Connection String>",
    "LOGIN_USERNAME": "<Your Login Username>",
    "LOGIN_PASSWORD": "<Your Login Password>",
    "SENDGRID_API_KEY": "<Your SendGrid API Key>",
    "ALERT_SENDER_EMAIL": "<Your Sender Email>",
    "ALERT_RECEIVER_EMAIL": "<Your Receiver Email>"
  }
}
```
This will require an Azure Cosmos database to be able to run. My implemetation used a database container and database with the same name, so the `DATABASE_AND_CONTAINER_NAME` needs to be named the same or the code base needs to be adapted to reflect this change

For SendGrid, I used the same sender and receiver email. This needs to be registered on the SendGrid website and an API key needs to be in place in the `.json` file. 

The Login can be set by the user. Run this (reset_database) before testing the main functionality to set up the database and input the username and password

### 3. Run locally

Run the http trigger to initialise and/or reset the database. Input your username and password as follows
```json
{
  "username": "<Your Login Username>",
  "password": "<Your Login Password>",
}
```
The file `reset_db_entries.json` comtains the layout of the database. You can change this to reflect your testing

When complete, you may run the http trigger to input a list of products. An example is given in the sample.json file of a suitable input for this function. Copy and paste the content into the input arguement. Alternatively, the same sample is provided below

```json
{
    "products": [
        {
            "id": "P-0001",
            "quantity": -10
        },
        {
            "id": "P-0002",
            "quantity": -13
        },
        {
            "id": "P-0004",
            "quantity": -8
        }
    ]
}
```



