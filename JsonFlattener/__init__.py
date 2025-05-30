import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient

def main(msg: func.QueueMessage) -> None:
    try:
        data = json.loads(msg.get_body().decode("utf-8"))
        flat = flatten_json(data)

        # Connect to Cosmos DB
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        client = CosmosClient(endpoint, key)
        db = client.get_database_client("PdfDataDB")
        container = db.get_container_client("FlattenedOrders")

        container.create_item(flat)

        logging.info("Flattened record written to Cosmos DB.")
    except Exception as e:
        logging.error(f"Failed to write to Cosmos: {e}")
        logging.warning("📥 Queue message received")
        logging.warning(f"Message content: {msg.get_body().decode('utf-8')}")


def flatten_json(record):
    flat = {
        "id": record.get("file", "").replace("pdfupload/", "").replace(".pdf", ""),
        "file": record.get("file"),
        "orderNumber": record.get("orderNumber"),
        "orderType": record.get("orderType"),
        "confirmationNumber": record.get("confirmationNumber"),
        "confirmationType": record.get("confirmationType"),
    }
    if "formFields" in record:
        flat.update(record["formFields"])
    return flat
