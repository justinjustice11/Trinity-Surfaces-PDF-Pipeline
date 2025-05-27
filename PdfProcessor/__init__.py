import logging
import json
import io
from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    blob_name = inputBlob.name
    size = inputBlob.length
    try:
        logging.info(f"Processing blob: {blob_name}, {size} bytes")

        pdf_data = inputBlob.read()
        text = extract_text(io.BytesIO(pdf_data))

        result = {
            "file": blob_name,
            "size": size,
            "text": text or "",
            "orderNumber": find_order_number(text)
        }

    except Exception as ex:
        logging.error(f"Error in PdfProcessor for {blob_name}: {ex}", exc_info=True)
        result = {
            "file": blob_name,
            "size": size,
            "error": str(ex),
            "orderNumber": "Not Found"
        }

    outputBlob.set(json.dumps(result))


def find_order_number(text: str) -> str:
    """
    Look for “Order” or “PO Number” or “SO Number” in the text.
    Returns the first match, or “Not Found”.
    """
    import re
    patterns = [
        r"Order\s*Number[:\s]+([A-Za-z0-9\-]+)",
        r"PO\s*Number[:\s]+([A-Za-z0-9\-]+)",
        r"SO\s*Number[:\s]+([A-Za-z0-9\-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text or "", re.IGNORECASE)
        if m:
            return m.group(1)
    return "Not Found"
