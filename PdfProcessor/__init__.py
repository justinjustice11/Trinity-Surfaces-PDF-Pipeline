import logging
import json
import io
from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read PDF data and extract text
        pdf_data = inputBlob.read()
        text = extract_text(io.BytesIO(pdf_data))

        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "text": text
        }

        # Write result as JSON
        outputBlob.set(json.dumps(result, ensure_ascii=False))
        logging.info(f"Wrote JSON to pdfjson/{inputBlob.name}.json")

    except Exception as e:
        logging.error(f"Failed to process blob {inputBlob.name}: {e}", exc_info=True)
