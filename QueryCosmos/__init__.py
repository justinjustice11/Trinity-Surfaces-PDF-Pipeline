import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

# Environment variables set in Azure Configuration
COSMOS_CONN_STR   = os.getenv("CosmosDB")
DATABASE_NAME     = os.getenv("COSMOS_DB_NAME", "PdfPipelineDB")
CONTAINER_NAME    = os.getenv("COSMOS_CONTAINER_NAME", "PdfResults")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger received for Cosmos DB lookup")

    # Connect to Cosmos DB
    try:
        client    = CosmosClient.from_connection_string(COSMOS_CONN_STR)
        database  = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
    except Exception as e:
        logging.error(f"Cosmos DB connection failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Connection failed", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    # Check ?file= query param
    file_name = req.params.get("file")
    if not file_name:
        try:
            body = req.get_json()
            file_name = body.get("file")
        except ValueError:
            pass

    # If file specified, fetch that one item
    if file_name:
        pk = file_name.replace(" ", "_")
        try:
            item = container.read_item(item=pk, partition_key=pk)
            return func.HttpResponse(json.dumps(item, indent=2), status_code=200, mimetype="application/json")
        except exceptions.CosmosResourceNotFoundError:
            return func.HttpResponse(json.dumps({"error": f"'{pk}' not found"}), status_code=404, mimetype="application/json")
        except Exception as e:
            logging.error(f"Error reading '{pk}': {e}")
            return func.HttpResponse(
                json.dumps({"error": "Read error", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

    # Otherwise list up to 10 items
    try:
        items = [
            { "id": i["id"], **{k: i[k] for k in i if k != "id"} }
            for i in container.read_all_items(max_item_count=10)
        ]
        return func.HttpResponse(json.dumps(items, indent=2), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error listing items: {e}")
        return func.HttpResponse(
            json.dumps({"error": "List error", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
