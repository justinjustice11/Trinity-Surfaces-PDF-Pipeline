import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient

def main(msg: func.QueueMessage) -> None:
    try:
        logging.info("JsonFlattener function triggered.")
        
        body = msg.get_body().decode('utf-8')
        logging.info(f"Received message body: {body}")
        data = json.loads(body)

        # Read from environment
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        cosmos_key = os.getenv("COSMOS_KEY")

        if not cosmos_endpoint or not cosmos_key:
            raise ValueError("Missing Cosmos DB endpoint or key.")

        client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
        db = client.get_database_client("PdfDataDB")
        container = db.get_container_client("FlattenedOrders")

        # Create a simple document
        doc = {
            "id": data.get("file", "unknown.pdf"),
            "fields": data.get("formFields", {}),
            "source": "JsonFlattener"
        }

        container.upsert_item(doc)
        logging.info(f"Document {doc['id']} successfully written to Cosmos DB.")

    except Exception as e:
        logging.exception(f"JsonFlattener failed with {type(e).__name__}: {e}")
        raise
