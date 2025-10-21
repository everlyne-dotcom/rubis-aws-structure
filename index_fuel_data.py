import boto3
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def get_opensearch_client():
    host = 'fuel-quality-opensearch-domain-endpoint'  # Will be updated after domain is ready
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    return client

def create_fuel_index():
    client = get_opensearch_client()
    
    index_mapping = {
        "mappings": {
            "properties": {
                "fuel_id": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "temperature_c": {"type": "float"},
                "density_kg_m3": {"type": "float"},
                "viscosity_cSt": {"type": "float"},
                "sulfur_ppm": {"type": "float"},
                "moisture_pct": {"type": "float"},
                "octane_rating": {"type": "float"},
                "batch_quality": {"type": "keyword"},
                "content": {"type": "text"}
            }
        }
    }
    
    try:
        client.indices.create(index="fuel_quality", body=index_mapping)
        print("SUCCESS: fuel_quality index created")
    except Exception as e:
        if "already exists" in str(e):
            print("SUCCESS: fuel_quality index already exists")
        else:
            print("ERROR:", str(e))

def index_sample_data():
    client = get_opensearch_client()
    
    sample_docs = [
        {
            "fuel_id": "TANK-1",
            "timestamp": "2024-01-15T10:00:00Z",
            "temperature_c": 22.5,
            "density_kg_m3": 750.0,
            "viscosity_cSt": 2.1,
            "sulfur_ppm": 10.0,
            "moisture_pct": 0.03,
            "octane_rating": 91.0,
            "batch_quality": "CLEAN",
            "content": "Clean fuel sample from TANK-1 with normal temperature 22.5C, density 750 kg/m3, low sulfur content 10ppm"
        },
        {
            "fuel_id": "TANK-2", 
            "timestamp": "2024-01-15T10:05:00Z",
            "temperature_c": 45.0,
            "density_kg_m3": 680.0,
            "viscosity_cSt": 6.5,
            "sulfur_ppm": 120.0,
            "moisture_pct": 0.25,
            "octane_rating": 78.0,
            "batch_quality": "CONTAMINATED",
            "content": "Contaminated fuel sample from TANK-2 with high temperature 45C, low density 680 kg/m3, high sulfur 120ppm, excessive moisture"
        }
    ]
    
    for i, doc in enumerate(sample_docs):
        try:
            client.index(index="fuel_quality", id=i+1, body=doc)
            print(f"Indexed document {i+1}: {doc['fuel_id']} - {doc['batch_quality']}")
        except Exception as e:
            print(f"Error indexing document {i+1}: {e}")

def main():
    print("=== Setting up OpenSearch Index ===")
    create_fuel_index()
    index_sample_data()
    print("\n=== Ready for RAG queries ===")

if __name__ == "__main__":
    main()