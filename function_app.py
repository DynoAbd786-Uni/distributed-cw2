import azure.functions as func
from azure.cosmos import CosmosClient
import os
import logging
from reset_to_default_db import reset_to_default_db
from stock_warning import stock_warning
from collections import Counter

DATABASE_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")
CONTAINER_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_blueprint(reset_to_default_db) 
app.register_blueprint(stock_warning) 


@app.function_name(name="http_trigger_product_input")
@app.route(route="http_trigger_product_input", auth_level=func.AuthLevel.ANONYMOUS)
@app.queue_output(arg_name="msg", queue_name="outqueue", connection="AzureWebJobsStorage")
@app.cosmos_db_output(arg_name="outputDocument", database_name=DATABASE_NAME, container_name=CONTAINER_NAME, connection="CompanyInventoryCosmosDBConnectionString")

def product_request_input(req: func.HttpRequest, msg: func.Out[func.QueueMessage],
    outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function (product input) processed a request.')
    logging.info(f"Request Headers: {req.headers}")
    logging.info(f"Request Origin: {req.headers.get('User-Agent', 'Unknown')}")


    # Get product list
    try:
        req_body = req.get_json()
        product_list = req_body.get('products', [])
    except ValueError:
        logging.info('Product request failed. Reason: JSON input format is incorrect')
        return func.HttpResponse(
            "Please provide a list of products in correct JSON format.",
            status_code=400
        )
    except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return func.HttpResponse(
            "An unexpected error occurred",
            status_code=400
        )

    # Check inputs for correct formatting
    # logging.info(product_list)
    if not product_list or not isinstance(product_list, list):
        logging.info('Product request failed. Reason: Products list not supplied or in incorrect format.')
        return func.HttpResponse(
            "Please provide a list of products, each with an id and quantity.",
            status_code=400
        )

    # Checking for correct datatype formatting
    validated_products = []
    for product in product_list:
        product_id = product.get('id')
        quantity = product.get('quantity')
        if not product_id or not isinstance(quantity, (int)):
            logging.info('Invalid product entry detected. Reason: Missing id or quantity.')
            return func.HttpResponse(
                "Each product must have an 'id' and a numeric 'quantity'.",
                status_code=400
            )
        validated_products.append({"id": product_id, "quantity": quantity})

    # Initialize Cosmos DB client and container
    client = CosmosClient.from_connection_string(os.getenv("CompanyInventoryCosmosDBConnectionString"))
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)

    # Query DB and match products
    inventory_list_to_append = []
    product_matches = []
    for inventory_item in container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
        for product in validated_products:
            if product["id"] == inventory_item["id"]:
                product_matches.append(product)
                inventory_list_to_append.append(inventory_item)
                validated_products.remove(product)
                break

    # Check for unmatched products
    if validated_products:
        invalid_ids = [product['id'] for product in validated_products]
        logging.info(f"Invalid product entry detected: incorrect IDs supplied: {', '.join(invalid_ids)}")
        return func.HttpResponse(
            f"Product IDs not found in database: {', '.join(invalid_ids)}",
            status_code=400
        )

    # Check for duplicates
    id_counts = Counter([product['id'] for product in product_matches])
    duplicates = [id for id, count in id_counts.items() if count > 1]
    if duplicates:
        logging.info(f"Duplicate products detected: {', '.join(duplicates)}")
        return func.HttpResponse(
            f"Duplicate product IDs found: {', '.join(duplicates)}.",
            status_code=400
        )

    # Update inventory quantities
    zero_products = []
    for inventory_item in inventory_list_to_append:
        for product in product_matches:
            if product["id"] == inventory_item["id"]:
                inventory_item["quantity"] += product["quantity"]
                if inventory_item["quantity"] < 0:
                    zero_products.append(product["id"])

    # Handle negative stock
    if zero_products:
        logging.info(f"Not enough stock for IDs: {', '.join(zero_products)}")
        return func.HttpResponse(
            f"Not enough stock for the following IDs: {', '.join(zero_products)}.",
            status_code=400
        )

    # Write updates to DB
    for inventory_item in inventory_list_to_append:
        container.upsert_item(inventory_item)

    logging.info(f"DB updated for {len(inventory_list_to_append)} item(s)")
    return func.HttpResponse(
        f"DB successfully updated for {len(inventory_list_to_append)} item(s).",
        status_code=200
    )