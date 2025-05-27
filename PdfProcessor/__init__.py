import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

# pre‐compile a regex that will catch any of the labels you care about
_ORDER_RE = re.compile(
    r'\b(?:Order\s*Number|Order\s*No|PO\s*Number|PO\s*No|SO\s*Number|SO\s*No)\s*[:#]?\s*([\w-]+)',
    re.IGNORECASE
)

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # 1. Extract the PDF text
        pdf_data = inputBlob.read()
        text = extract_text(io.BytesIO(pdf_data))

        # 2. Look for an order/PO/SO number
        m = _ORDER_RE.search(text or "")
        order_number = m.group(1) if m else "Not Found"

        # 3. Build your output record
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "orderNumber": order_number,
            "text": text
        }

        # 4. Write it back out
        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name} (orderNumber={order_number})")

    except Exception as e:
        logging.error(f"Error processing {inputBlob.name}: {e}", exc_info=True)
        # re-throw so Azure Functions marks the invocation as failed
        raise
