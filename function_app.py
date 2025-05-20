import os
import json
import logging

import azure.functions as func
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# ── GLOBAL COLD-START CLIENTS ────────────────────────────────────────────────

# Form Recognizer
FORM_ENDPOINT = os.getenv("COGNITIVE_ENDPOINT")
FORM_KEY      = os.getenv("COGNITIVE_KEY")
_form_recognizer = DocumentAnalysisClient(
    endpoint=FORM_ENDPOINT,
    credential=AzureKeyCredential(FORM_KEY)
)

def _get_cosmos_container():
    """
    Lazily create/get our Cosmos DB database & container.
    Uses '/id' as the partition key.
    """
    conn_str = os.getenv("CosmosDB")
    client   = CosmosClient.from_connection_string(conn_str)

    # ensure database exists
    db = client.create_database_if_not_exists(id="PdfPipelineDB")

    # ensure container exists
    container = db.create_container_if_not_exists(
        id="PdfResults",
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )
    return container

app = func.FunctionApp()

# ── 1) BLOB-TRIGGERED PDF PROCESSOR ────────────────────────────────────────────
@app.blob_trigger(
    arg_name="myblob",
    path="pdfupload/{name}",
    connection="AzureWebJobsStorage"
)
@app.blob_output(
    arg_name="outputBlob",
    path="pdfjson/{name}.json",
    connection="AzureWebJobsStorage"
)
def PdfProcessor(myblob: func.InputStream, outputBlob: func.Out[str]):
    logging.info(f"Processing blob {myblob.name} ({myblob.length} bytes)")

    # Analyze PDF
    poller = _form_recognizer.begin_analyze_document(
        "prebuilt-document",
        document=myblob.read()
    )
    result = poller.result()

    # Serialize & assign a safe id
    data = result.to_dict()
    filename = os.path.basename(myblob.name)
    safe_id = filename.replace(" ", "_")
    data["id"] = safe_id

    # Upsert into Cosmos
    container = _get_cosmos_container()
    container.upsert_item(data)

    # Also write JSON blob
    outputBlob.set(json.dumps(data))

    logging.info(f"Form Recognizer returned {len(result.pages)} pages")


# ── 2) HTTP CONSUMER: GET ONE PDF BY ID ────────────────────────────────────────
@app.route(route="pdf/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def GetPdfById(req: func.HttpRequest) -> func.HttpResponse:
    pdf_id = req.route_params.get("id")
    logging.info(f"HTTP GET /api/pdf/{pdf_id}")

    container = _get_cosmos_container()
    try:
        item = container.read_item(item=pdf_id, partition_key=pdf_id)
        return func.HttpResponse(
            json.dumps(item),
            status_code=200,
            mimetype="application/json"
        )
    except exceptions.CosmosResourceNotFoundError:
        return func.HttpResponse(status_code=404)


# ── 3) HTTP CONSUMER: LIST ALL PDF IDS ────────────────────────────────────────
@app.route(route="pdf", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ListPdfs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP GET /api/pdf")

    container = _get_cosmos_container()
    query = "SELECT c.id FROM c ORDER BY c.id"
    items = list(container.query_items(query, enable_cross_partition_query=True))

    return func.HttpResponse(
        json.dumps(items),
        status_code=200,
        mimetype="application/json"
    )
