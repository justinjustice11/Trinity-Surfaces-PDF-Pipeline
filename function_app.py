import logging
import os
import json

import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

# 1) Blob‐triggered PDF → JSON processor
@app.function_name(name="PdfProcessor")
@app.blob_trigger(arg_name="inputBlob",
                  path="pdfupload/{name}",
                  connection="AzureWebJobsStorage")
@app.blob_output(arg_name="outputBlob",
                 path="pdfjson/{name}.json",
                 connection="AzureWebJobsStorage")
def PdfProcessor(inputBlob: func.InputStream, outputBlob: func.Out[str]):
    logging.info(f"Blob trigger fired for {inputBlob.name} ({inputBlob.length} bytes)")
    # TODO: replace this with your real PDF→JSON logic
    result = {
        "file": inputBlob.name,
        "size": inputBlob.length
    }
    outputBlob.set(json.dumps(result))
    logging.info(f"Wrote JSON to pdfjson/{inputBlob.name}.json")


# 2) HTTP GET /api/pdf/{id} → returns the JSON blob for one PDF
@app.function_name(name="GetPdfById")
@app.route(route="pdf/{id}",
           methods=["GET"],
           auth_level=func.AuthLevel.FUNCTION)
def GetPdfById(req: func.HttpRequest) -> func.HttpResponse:
    file_id = req.route_params.get("id")
    logging.info(f"HTTP trigger GetPdfById for id: {file_id}")

    try:
        blob_service    = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
        container_client = blob_service.get_container_client("pdfjson")
        blob_client      = container_client.get_blob_client(f"{file_id}.json")
        blob_data        = blob_client.download_blob().readall()
        return func.HttpResponse(
            body=blob_data,
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error fetching blob: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)


# 3) HTTP GET /api/pdf → lists all JSON filenames
@app.function_name(name="ListPdfs")
@app.route(route="pdf",
           methods=["GET"],
           auth_level=func.AuthLevel.FUNCTION)
def ListPdfs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger ListPdfs")

    try:
        blob_service     = BlobServiceClient.from_connection_string(os.getenv("AzureWebJobsStorage"))
        container_client = blob_service.get_container_client("pdfjson")
        names = [b.name for b in container_client.list_blobs()]
        return func.HttpResponse(
            json.dumps(names),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error listing blobs: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)


# 4) HTTP GET/POST /api/cosmos?file=... → queries Cosmos DB
@app.function_name(name="QueryCosmos")
@app.route(route="cosmos",
           methods=["GET","POST"],
           auth_level=func.AuthLevel.FUNCTION)
def QueryCosmos(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger QueryCosmos")

    COSMOS_CONN_STR = os.getenv("CosmosDB")
    DB_NAME         = os.getenv("COSMOS_DB_NAME", "PdfPipelineDB")
    CONT_NAME       = os.getenv("COSMOS_CONTAINER_NAME", "PdfResults")

    # connect
    try:
        client    = CosmosClient.from_connection_string(COSMOS_CONN_STR)
        container = client.get_database_client(DB_NAME).get_container_client(CONT_NAME)
    except Exception as e:
        logging.error(f"Cosmos DB connection failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Connection failed", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    # check for ?file= param or JSON body { "file": "..." }
    file_name = req.params.get("file")
    if not file_name:
        try:
            body = req.get_json()
            file_name = body.get("file")
        except ValueError:
            pass

    # if they requested one file
    if file_name:
        pk = file_name.replace(" ", "_")
        try:
            item = container.read_item(item=pk, partition_key=pk)
            return func.HttpResponse(
                json.dumps(item, indent=2),
                status_code=200,
                mimetype="application/json"
            )
        except exceptions.CosmosResourceNotFoundError:
            return func.HttpResponse(
                json.dumps({"error": f"'{pk}' not found"}),
                status_code=404,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error reading '{pk}': {e}")
            return func.HttpResponse(
                json.dumps({"error": "Read error", "details": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

    # otherwise list up to 10 items
    try:
        items = [
            {"id": i["id"], **{k: i[k] for k in i if k != "id"}}
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
            json.dumps({"error": "List error", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
