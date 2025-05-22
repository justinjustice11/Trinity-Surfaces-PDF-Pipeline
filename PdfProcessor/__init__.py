import logging
import json
import azure.functions as func

def main(inputBlob: func.InputStream, outputBlob: func.Out[str]):
    logging.info(f"Blob trigger fired for {inputBlob.name} ({inputBlob.length} bytes)")
    result = {
        "file": inputBlob.name,
        "size": inputBlob.length
    }
    outputBlob.set(json.dumps(result))
    logging.info(f"Wrote JSON to pdfjson/{inputBlob.name}.json")