# PdfProcessor/__init__.py
import logging
import json
import io
import os

from pdfminer.high_level import extract_text
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str], queueOutput: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read blob content
        pdf_bytes = inputBlob.read()

        # (Optional) Extract raw text preview for debugging only
        #text_preview = extract_text(io.BytesIO(pdf_bytes))
        #logging.debug(f"Extracted text preview (first 500 chars): {text_preview[:500]}")

        # Azure Form Recognizer setup
        endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("FORM_RECOGNIZER_KEY")
        form_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        # Invoke prebuilt-document model
        poller = form_client.begin_analyze_document(
            "prebuilt-document",
            document=io.BytesIO(pdf_bytes)
        )
        result = poller.result()

        # Pull out all key/value pairs
        form_fields = {}
        for kv in result.key_value_pairs:
            if kv.key and kv.value:
                form_fields[kv.key.content.strip()] = kv.value.content.strip()

        # Build your payload
        result_payload = {
            "file": inputBlob.name,
            "formFields": form_fields,
            "textPreview": text_preview[:500] or "No text extracted"
        }

        # Persist JSON to blob
        outputBlob.set(json.dumps(result_payload))

        # Enqueue for downstream flattening / Cosmos write
        queueOutput.set(json.dumps(result_payload))

        logging.info(f"Successfully processed and queued: {inputBlob.name}")

    except Exception as e:
        logging.exception(f"Error processing blob {inputBlob.name}: {e}")
        # bubble up so Azure logs the failure and can retry
        raise
