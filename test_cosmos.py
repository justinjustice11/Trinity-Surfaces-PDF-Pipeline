import os
from azure.cosmos import CosmosClient

# 1. Read the connection string from the environment
conn = os.getenv("CosmosDB")
print("Connection string starts with:", conn[:60] + "…")

# 2. Try to connect and list your databases
try:
    client = CosmosClient.from_connection_string(conn)
    dbs = list(client.list_databases())
    print("✅ Connected! Databases you have:")
    for db in dbs:
        print("   •", db["id"])
except Exception as e:
    print("❌ Connection failed:", type(e).__name__, e)
