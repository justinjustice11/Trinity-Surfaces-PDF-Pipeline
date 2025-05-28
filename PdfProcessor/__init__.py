import logging
import json
import io
import re
from pdfminer.high_level import extract_text
import azure.functions as func

def extract_with_patterns(text: str, patterns: list, default="Not Found") -> str:
    """
    Try each (regex, name) in patterns against text;
    return first capture group or default.
    """
    for regex, _ in patterns:
        m = re.search(regex, text, re.IGNORECASE | re.DOTALL)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return default

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name} ({inputBlob.length} bytes)")

        # 1) read & OCR
        pdf_bytes = inputBlob.read()
        text = extract_text(io.BytesIO(pdf_bytes))

        # 2) extract fields with fallbacks
        vendor = extract_with_patterns(text, [
            (r"^([^\r\n]{3,100})", "vendor")
        ])

        ship_to = extract_with_patterns(text, [
            (r"SHIP TO:\s*\n(.+?)\n", "shipTo"),
            (r"Ship to Address\s*\n(.+?)\n", "shipTo")
        ])

        order_number = extract_with_patterns(text, [
            (r"\bPO[#:\s]+(\d+)\b", "orderNumber"),
            (r"Sales Order\D*(\d+)\b", "orderNumber"),
            (r"Order\s+#?\s*(\d+)\b", "orderNumber")
        ])

        order_date = extract_with_patterns(text, [
            (r"Order Date\D*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})", "orderDate"),
            (r"DATED\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})", "orderDate")
        ])

        currency = extract_with_patterns(text, [
            (r"Currency\s*\n\s*([A-Z]{3})", "currency"),
            (r"\b(USD|EUR|CAD)\b", "currency")
        ])

        # 3) assemble result
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "vendor": vendor,
            "shipTo": ship_to,
            "orderNumber": order_number,
            "orderDate": order_date,
            "currency": currency,
            "text": text
        }

        outputBlob.set(json.dumps(result))
        logging.info(f"Wrote JSON for {inputBlob.name}")

    except Exception as ex:
        logging.error(f"Failed {inputBlob.name}: {ex}", exc_info=True)
        # emit minimal JSON so trigger doesn't poison-queue forever
        outputBlob.set(json.dumps({
            "file": inputBlob.name,
            "size": inputBlob.length,
            "error": str(ex)
        }))
        raise
