# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(reset_to_default_db) 
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints


import azure.functions as func
from azure.cosmos import CosmosClient
import json
import logging
import datetime
import os

DATABASE_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")
CONTAINER_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")

reset_to_default_db = func.Blueprint()

@reset_to_default_db.function_name(name="http_trigger_reset_to_default_db")
@reset_to_default_db.route(route="http_trigger_reset_to_default_db", auth_level=func.AuthLevel.ANONYMOUS)
@reset_to_default_db.cosmos_db_output(arg_name="outputDocument", database_name=DATABASE_NAME, container_name=CONTAINER_NAME, connection="CompanyInventoryCosmosDBConnectionString")

def reset_db(req: func.HttpRequest, outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info('Python HTTP trigger (Reset db) function processed a request.')

    username = req.params.get('username')
    password = req.params.get('password')

    logging.info('Request to log in at time {time} to reset DB'.format(time=datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')))

    # If parsing fails from the HTML parameters, check .JSON body for username and password
    if not username or not password:
        try:
            req_body = req.get_json()
        except ValueError:
            logging.info('Login failed. Reason: JSON input format is incorrect')
            return func.HttpResponse(
                "Please provide both username and password in correct JSON format.",
                status_code=400
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return func.HttpResponse(
            "An unexpected error occurred",
            status_code=400
        )
        # Extract the username and password from .JSON body
        username = req_body.get('username')
        password = req_body.get('password')

        # Check values have been supplied
        if username == None or password == None:
            logging.info('Login failed. Reason: Username and/or password not supplied')
            return func.HttpResponse(
                "Please provide both username and password.",
                status_code=400
            )

    # Fetch environment variables for login credentials
    stored_username = os.getenv("LOGIN_USERNAME")
    stored_password = os.getenv("LOGIN_PASSWORD")

     # Authenticate user
    if username == stored_username and password == stored_password:
        try:
            # Read the file and parse it as JSON
            with open('reset_db_entries.json', 'r') as file:  # Updated filename
                data = json.load(file)  # Convert file content to JSON

            # Initialize Cosmos DB client and container
            client = CosmosClient.from_connection_string(os.getenv("CompanyInventoryCosmosDBConnectionString"))
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(CONTAINER_NAME)

            # Step 1: Wipe all existing entries in the container
            logging.info("Deleting all existing items from the container.")
            for item in container.query_items(
                query="SELECT * FROM c", 
                enable_cross_partition_query=True):
                try:
                    container.delete_item(item['id'], partition_key=item['id'])
                    logging.info(f"Deleted item with id: {item['id']}")
                except Exception as e:
                    logging.error(f"Error deleting item with id {item['id']}: {e}")

            # Step 2: Insert the new default items
            logging.info("Inserting default items into the container.")
            for item in data:
                try:
                    # Insert each new item into the container
                    container.create_item(body=item)
                    logging.info(f"Inserted new item with id: {item['id']}")
                except Exception as e:
                    logging.error(f"Error inserting item with id {item['id']}: {e}")

            return func.HttpResponse(
                "Database reset successfully with default entries.",
                status_code=200
            )
        except Exception as e:
            logging.error(f"Error processing reset: {e}")
            return func.HttpResponse(
                "An error occurred while resetting the database.",
                status_code=500
            )
    else:
        logging.info('Login failed. Reason: Incorrect username and/or password supplied')
        return func.HttpResponse(
            "Invalid username or password.",
            status_code=401
        )