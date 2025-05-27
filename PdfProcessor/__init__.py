import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

# PO/SO regex: captures “PO” or “SO” (with or without dots) and the following alpha‐num value
ORDER_RE = re.compile(
    r'\b((?:P\.?O|S\.?O))\s*(?:Number)?[:\s]*([A-Za-z0-9-]+)',
    re.IGNORECASE
)

# Confirmation regex: captures “Confirmation” (with optional “Number”) and the following alpha‐num value
CONF_RE = re.compile(
    r'\bConfirmation\s*(?:Number)?[:\s]*([A-Za-z0-9-]+)',
    re.IGNORECASE
)

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # extract raw text
        pdf_data = inputBlob.read()
        text = extract_text(io.BytesIO(pdf_data)) or ""

        # find order (PO/SO)
        m_order = ORDER_RE.search(text)
        if m_order:
            raw_type, raw_num = m_order.group(1), m_order.group(2)
            order_type = raw_type.replace(".", "").upper()   # “PO” or “SO”
            order_number = raw_num
        else:
            order_type = "Not Found"
            order_number = ""

        # find confirmation #
        m_conf = CONF_RE.search(text)
        if m_conf:
            conf_number = m_conf.group(1)
            conf_type = "Confirmation"
        else:
            conf_type = "Not Found"
            conf_number = ""

        # build JSON result
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "orderNumber": order_number,
            "orderType": order_type,
            "confirmationNumber": conf_number,
            "confirmationType": conf_type,
            "text": text
        }

        outputBlob.set(json.dumps(result, ensure_ascii=False))
        logging.info(
            f"Wrote JSON for {inputBlob.name} (orderType={order_type}, orderNumber={order_number}, "
            f"confType={conf_type}, confNumber={conf_number})"
        )

    except Exception as e:
        logging.error(f"Error processing {inputBlob.name}: {e}", exc_info=True)
        raise
