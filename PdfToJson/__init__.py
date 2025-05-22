import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

# Reads Cosmos connection info from the CosmosDB app setting
COSMOS_CONN_STR   = os.getenv("CosmosDB")
DATABASE_NAME     = os.getenv("COSMOS_DB_NAME", "PdfPipelineDB")
CONTAINER_NAME    = os.getenv("COSMOS_CONTAINER_NAME", "PdfResults")


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger received a request for Cosmos DB lookup")

    try:
        # Initialize Cosmos client
        client    = CosmosClient.from_connection_string(COSMOS_CONN_STR)
        database  = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
    except Exception as e:
        logging.error(f"Failed to connect to Cosmos DB: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Cosmos DB connection issue", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    # Check for a specific file query parameter
    file_name = req.params.get("file")
    if not file_name:
        try:
            req_body = req.get_json()
            file_name = req_body.get("file")
        except ValueError:
            pass

    # If a file name was provided, return just that document
    if file_name:
        pk = file_name.replace(" ", "_")  # match your key format
        try:
            item = container.read_item(item=pk, partition_key=pk)
            return func.HttpResponse(
                json.dumps(item, indent=2),
                status_code=200,
                mimetype="application/json"
            )
        except exceptions.CosmosResourceNotFoundError:
            return func.HttpResponse(
                json.dumps({"error": f"Item '{pk}' not found."}),
                status_code=404,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error fetching '{pk}': {e}")
            return func.HttpResponse(
                json.dumps({"error": "Error reading item", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

    # Otherwise, list up to 10 items
    try:
        items = [
            {"id": i.get("id"), **{k: i.get(k) for k in i.keys() if k != "id"}}
            for i in container.read_all_items(max_item_count=10)
        ]
        return func.HttpResponse(
            json.dumps(items, indent=2),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error listing items: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Error listing items", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
