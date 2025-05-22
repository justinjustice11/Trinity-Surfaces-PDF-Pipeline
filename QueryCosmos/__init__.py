import os
import json
import logging
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger QueryCosmos")

    conn_str = os.getenv("CosmosDB")
    db_name = os.getenv("COSMOS_DB_NAME", "PdfPipelineDB")
    cont_name = os.getenv("COSMOS_CONTAINER_NAME", "PdfResults")

    try:
        client = CosmosClient.from_connection_string(conn_str)
        container = client.get_database_client(db_name).get_container_client(cont_name)
    except Exception as e:
        logging.error(f"Cosmos DB connection failed: {e}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

    file_name = req.params.get("file")
    if not file_name:
        try:
            file_name = req.get_json().get("file")
        except:
            pass

    if file_name:
        pk = file_name.replace(" ", "_")
        try:
            item = container.read_item(item=pk, partition_key=pk)
            return func.HttpResponse(json.dumps(item), status_code=200, mimetype="application/json")
        except exceptions.CosmosResourceNotFoundError:
            return func.HttpResponse(json.dumps({"error": f"'{pk}' not found"}), status_code=404, mimetype="application/json")
        except Exception as e:
            return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")

    try:
        items = list(container.read_all_items(max_item_count=10))
        return func.HttpResponse(json.dumps(items), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")