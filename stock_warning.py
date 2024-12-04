import azure.functions as func
import os
import logging
import json
import sendgrid
from sendgrid.helpers.mail import Mail

# Ensure you are using your correct database and container names.
DATABASE_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")
CONTAINER_NAME = os.getenv("DATABASE_AND_CONTAINER_NAME")

# Assign a value to activate stock alerts if stock drops below this value
THRESHOLD_FOR_ALERTS = 5

# Hypothetical case to show warnings via email
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Store your API key in environment variables
ALERT_SENDER_EMAIL = os.getenv("ALERT_SENDER_EMAIL")  # Replace with your notification email address
ALERT_RECEIVER_EMAIL = os.getenv("ALERT_RECEIVER_EMAIL")  # Replace with your notification email address


stock_warning = func.Blueprint()

def send_email_alert(product_alert_list):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    # Create the email content
    subject = "Low Stock Alert: Low Stock Detected for Products"
    content = "You are receiving this email because you have opted in for stock alerts \n\nThe following products have low stock:\n\n"
    
    for product in product_alert_list:
        product_id = product["id"]
        quantity = product["quantity"]
        content += f" - Product ID: {product_id}, Quantity: {quantity}\n"
    
    # Create the email message
    message = Mail(
        from_email=ALERT_SENDER_EMAIL,
        to_emails=ALERT_RECEIVER_EMAIL,
        subject=subject,
        plain_text_content=content
    )
    
    try:
        # Send the email
        response = sg.send(message)
        logging.info(f"Email sent with status code {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")



# Cosmos DB Trigger Function
@stock_warning.function_name(name="cosmosdb_trigger_stock_warning")
@stock_warning.cosmos_db_trigger(
    arg_name="azcosmosdb",  # Variable that will hold the list of documents changed
    container_name=CONTAINER_NAME,
    database_name=DATABASE_NAME,
    create_lease_container_if_not_exists=True,
    connection="CompanyInventoryCosmosDBConnectionString"
)
def cosmosdb_trigger_stock_warning(azcosmosdb: func.DocumentList):
    product_alerts_list = []
    
    if azcosmosdb:
        for doc in azcosmosdb:
            # Convert document to dictionary
            doc_dict = doc.to_dict()
            
            # Check for stock alerts
            if doc_dict["quantity"] <= THRESHOLD_FOR_ALERTS:
                product_alerts_list.append({"id": doc_dict["id"], "quantity":doc_dict["quantity"]})

    if product_alerts_list:
        logging.info(f"Stock has dropped below threshold for {len(product_alerts_list)} product(s). Attempting to send stock alert email")
        send_email_alert(product_alerts_list)
        
    else:
        logging.info("No changes detected.")
