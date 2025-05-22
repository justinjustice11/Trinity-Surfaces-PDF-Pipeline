import logging
import json
import io
from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

    # Extract text
    pdf_data = inputBlob.read()
    text = extract_text(io.BytesIO(pdf_data))

    result = {
        "file": inputBlob.name,
        "size": inputBlob.length,
        "text": text
    }

    outputBlob.set(json.dumps(result))
    logging.info(f"Wrote JSON to pdfjson/{inputBlob.name}.json")
