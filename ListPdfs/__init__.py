import os
import json
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger ListPdfs")

    try:
        blob_service = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
        container_client = blob_service.get_container_client("pdfjson")
        names = [b.name for b in container_client.list_blobs()]
        return func.HttpResponse(json.dumps(names), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error listing blobs: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)