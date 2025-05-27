import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read the PDF content
        pdf_data = inputBlob.read()

        # Extract text from the PDF
        text = extract_text(io.BytesIO(pdf_data))

        # Try to find an order number (Order No, Order Number, PO Number, SO Number…)
        order_patterns = [
            r'order\s*(?:number|no)\s*[:#]?\s*([A-Za-z0-9\-]+)',
            r'po\s*(?:number|no)\s*[:#]?\s*([A-Za-z0-9\-]+)',
            r'so\s*(?:number|no)\s*[:#]?\s*([A-Za-z0-9\-]+)'
        ]
        order_number = "Not Found"
        for pat in order_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                order_number = match.group(1)
                break

        # Build the JSON result
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "orderNumber": order_number,
            "text": text
        }

        # Write to the output blob
        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name} with OrderNumber={order_number}")

    except Exception as e:
        logging.error(f"Error processing {inputBlob.name}: {e}", exc_info=True)
        raise
