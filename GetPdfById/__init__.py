import os
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    file_id = req.route_params.get("id")
    logging.info(f"HTTP trigger GetPdfById for id: {file_id}")

    try:
        blob_service = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
        container_client = blob_service.get_container_client("pdfjson")
        blob_client = container_client.get_blob_client(f"{file_id}.json")
        blob_data = blob_client.download_blob().readall()
        return func.HttpResponse(blob_data, mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error fetching blob: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)