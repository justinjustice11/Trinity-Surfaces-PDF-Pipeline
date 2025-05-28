import logging
import json
import io

from PyPDF2 import PdfReader
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]) -> None:
    try:
        logging.info(f"Triggered by blob: {inputBlob.name}, size: {inputBlob.length} bytes")

        # Read the PDF bytes
        pdf_bytes = inputBlob.read()

        # Extract text with PyPDF2
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        full_text = "\n\n".join(pages)

        # Build your JSON payload
        result = {
            "file": inputBlob.name,
            "size": inputBlob.length,
            "text": full_text or "No text extracted"
        }

        # Write to the output blob
        outputBlob.set(json.dumps(result))
        logging.info(f"Successfully wrote JSON for: {inputBlob.name}")

    except Exception:
        logging.exception(f"Error processing {inputBlob.name}")
        # re-raise so Functions runtime knows we failed and will retry
        raise
