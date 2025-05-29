import logging
import json
import io
import re
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

        # Extract text from PDF
        text = extract_text(io.BytesIO(pdf_bytes))
        logging.debug(f"Extracted text preview: {text[:500]}")

        # Regex-based extraction
        order_number = re.search(r"(?:PO|SO)?\s*(?:Number|#)[:\s]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        order_type = re.search(r"\b(PO|SO)\b", text, re.IGNORECASE)
        conf_number = re.search(r"Confirmation\s*(?:Number|#)?[:\s]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        conf_type = re.search(r"(PO|SO)\s*Confirmation", text, re.IGNORECASE)

        # Azure Form Recognizer setup
        endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("FORM_RECOGNIZER_KEY")
        form_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        # Use Form Recognizer
        poller = form_client.begin_analyze_document("prebuilt-document", document=io.BytesIO(pdf_bytes))
        result = poller.result()

        # Extract fields
        form_fields = {}
        for kv in result.key_value_pairs:
            if kv.key and kv.value:
                form_fields[kv.key.content.strip()] = kv.value.content.strip()

        # Build payload
        result_payload = {
            "file": inputBlob.name,
            "orderNumber": order_number.group(1) if order_number else "Not Found",
            "orderType": order_type.group(1) if order_type else "Not Found",
            "confirmationNumber": conf_number.group(1) if conf_number else "Not Found",
            "confirmationType": conf_type.group(1) if conf_type else "Not Found",
            "text": text or "No text extracted",
            "formFields": form_fields
        }

        # Write to Blob
        outputBlob.set(json.dumps(result_payload))

        # ✅ Send to queue for flattening
        queueOutput.set(json.dumps(result_payload))

        logging.info(f"Successfully wrote JSON and queued result for: {inputBlob.name}")

    except Exception as e:
        logging.exception(f"Error processing blob {inputBlob.name}: {str(e)}")
        raise
