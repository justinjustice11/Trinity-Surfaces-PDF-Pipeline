import logging
import json
import io
import os

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str], queueOutput: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read blob content
        pdf_bytes = inputBlob.read()

        # Load environment variables
        endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("FORM_RECOGNIZER_KEY")

        if not endpoint or not key:
            raise ValueError("Missing FORM_RECOGNIZER_ENDPOINT or FORM_RECOGNIZER_KEY in environment variables")

        # Azure Form Recognizer client
        form_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        # Analyze PDF with Form Recognizer
        try:
            poller = form_client.begin_analyze_document("prebuilt-document", document=io.BytesIO(pdf_bytes))
            result = poller.result()
        except Exception as fr_error:
            logging.error(f"Form Recognizer API call failed: {fr_error}")
            raise

        # Extract key-value pairs
        form_fields = {}
        for kv in result.key_value_pairs:
            if kv.key and kv.value:
                form_fields[kv.key.content.strip()] = kv.value.content.strip()

        # Build result payload
        result_payload = {
            "file": inputBlob.name,
            "formFields": form_fields
        }

        # Write to blob
        outputBlob.set(json.dumps(result_payload))

        # Send to queue for flattening
        queueOutput.set(json.dumps(result_payload))

        logging.info(f"Successfully processed and queued: {inputBlob.name}")

    except Exception as e:
        logging.exception(f"Error processing blob {inputBlob.name}: {e}")
        raise
