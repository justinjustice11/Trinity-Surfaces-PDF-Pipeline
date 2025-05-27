import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

# (same regex from before...)
_ORDER_RE = re.compile(
    r'\b(?:Order\s*Number|Order\s*No|PO\s*Number|PO\s*No|SO\s*Number|SO\s*No)\s*[:#]?\s*([\w-]+)',
    re.IGNORECASE
)

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    file_id = inputBlob.name
    size    = inputBlob.length

    # 1) Always read the blob
    data = inputBlob.read()

    # 2) Attempt text extraction, but never throw
    try:
        text = extract_text(io.BytesIO(data))
    except Exception as ex:
        logging.error(f"PDF parsing failed for {file_id}: {ex}", exc_info=True)
        text = ""

    # 3) Attempt to pull out an order/PO/SO number
    m = _ORDER_RE.search(text)
    order_number = m.group(1) if m else "Not Found"

    # 4) Write a JSON result no matter what
    result = {
        "file": file_id,
        "size": size,
        "orderNumber": order_number,
        "text": text
    }

    outputBlob.set(json.dumps(result))
    logging.info(f"Wrote JSON for {file_id} (orderNumber={order_number})")
