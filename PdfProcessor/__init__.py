import logging
import json
import io
from pdfminer.high_level import extract_text
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read the PDF content
        pdf_data = inputBlob.read()

        # Extract text from the PDF
        text = extract_text(io.BytesIO(pdf_data))

        # Format result
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "text": text
        }

        # Write to output blob as JSON
        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name}")

    except Exception as e:
        logging.error(f"Error processing {inputBlob.name}: {str(e)}", exc_info=True)
        raise  # re-throw so Azure Functions runtime knows it failed
