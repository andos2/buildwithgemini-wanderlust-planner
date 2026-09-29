import vertexai

PROJECT_ID = "qwiklabs-gcp-04-15689d1f930e"
LOCATION   = "us-east1"

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print("Creating memory bank...")
memory_bank = client.agent_engines.create()
resource_name = memory_bank.api_resource.name
memory_bank_id = resource_name.split("/")[-1]
print("MEMORY_BANK_ID:", memory_bank_id)
print("resource name :", resource_name)
