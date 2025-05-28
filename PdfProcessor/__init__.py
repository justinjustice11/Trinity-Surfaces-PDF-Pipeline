import logging
import json
import io
import re

from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read blob content
        pdf_bytes = inputBlob.read()

        # Extract text from PDF
        text = extract_text(io.BytesIO(pdf_bytes))

        # Extract data points using regex
        order_number = re.search(r"(?:PO\s*Number|SO\s*Number)[:\s]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        order_type = re.search(r"\b(PO|SO)\b", text)
        conf_number = re.search(r"(?:Confirmation\s*Number)[:\s]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        conf_type = re.search(r"\b(PO|SO)\s*Confirmation\b", text, re.IGNORECASE)

        # Build payload
        result = {
            "file": inputBlob.name,
            "orderNumber": order_number.group(1) if order_number else "Not Found",
            "orderType": order_type.group(1) if order_type else "Not Found",
            "confirmationNumber": conf_number.group(1) if conf_number else "Not Found",
            "confirmationType": conf_type.group(1) if conf_type else "Not Found",
            "text": text or "No text extracted"
        }

        # Output to blob
        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name}")

    except Exception as e:
        logging.exception(f"Error processing blob {inputBlob.name}: {str(e)}")
        raise
