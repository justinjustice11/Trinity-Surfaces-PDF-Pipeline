import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

def extract_field(text: str, patterns: list, default: str = "Not Found") -> str:
    """
    Try each regex pattern in order, return first capturing group's value, or default.
    """
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return default


def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name} ({inputBlob.length} bytes)")

        # Extract text from PDF
        pdf_bytes = inputBlob.read()
        raw_text = extract_text(io.BytesIO(pdf_bytes)) or ""
        # normalize whitespace for easier regex
        text = re.sub(r"\s+", " ", raw_text)

        # Patterns for PO, SO, and Confirmation
        po_patterns = [
            r"\bPO[#:\s-]*([A-Za-z0-9\-]+)\b",
            r"\bPurchase Order[#:\s-]*([A-Za-z0-9\-]+)\b"
        ]
        so_patterns = [
            r"\bSO[#:\s-]*([A-Za-z0-9\-]+)\b",
            r"\bSales Order[#:\s-]*([A-Za-z0-9\-]+)\b"
        ]
        conf_patterns = [
            r"\bOrder Confirmation[#:\s-]*([A-Za-z0-9\-]+)\b",
            r"\bConfirmation[#:\s-]*([A-Za-z0-9\-]+)\b"
        ]

        # Extract fields
        po_num = extract_field(text, po_patterns)
        so_num = extract_field(text, so_patterns)
        conf_num = extract_field(text, conf_patterns)

        # Determine order number and type
        if so_num != "Not Found":
            order_number = so_num
            order_type = "SO"
        elif po_num != "Not Found":
            order_number = po_num
            order_type = "PO"
        else:
            order_number = "Not Found"
            order_type = "Not Found"

        # Confirmation
        confirmation_number = conf_num
        confirmation_type = "PO Confirmation" if conf_num != "Not Found" else "Not Found"

        # Assemble JSON result
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "orderNumber": order_number,
            "orderType": order_type,
            "confirmationNumber": confirmation_number,
            "confirmationType": confirmation_type,
            "text": raw_text
        }

        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name}")

    except Exception as ex:
        logging.error(f"Error processing {inputBlob.name}: {ex}", exc_info=True)
        fallback = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "error": str(ex)
        }
        outputBlob.set(json.dumps(fallback))
        raise
