import os, json
from azure.cosmos import CosmosClient

conn    = os.getenv("CosmosDB")
client  = CosmosClient.from_connection_string(conn)
db      = client.get_database_client("PdfPipelineDB")
cont    = db.get_container_client("PdfResults")

# list IDs
for item in cont.read_all_items(max_item_count=10):
    print(item["id"])
# fetch one
item = cont.read_item(item="YOUR_FILE_NAME.pdf".replace(" ", "_"), partition_key="YOUR_FILE_NAME.pdf".replace(" ", "_"))
print(json.dumps(item, indent=2))
