import boto3
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def get_opensearch_endpoint():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        status = response['DomainStatus']
        
        if status['Processing']:
            print("OpenSearch domain still creating...")
            return None
        else:
            endpoint = status.get('Endpoint')
            print(f"OpenSearch ready! Endpoint: {endpoint}")
            return endpoint
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_opensearch_client(endpoint):
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    return OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

def index_fuel_data(client, data):
    # Create index
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
        print("Created fuel_quality index")
    except Exception as e:
        if "already exists" in str(e):
            print("Index already exists")
        else:
            print(f"Index creation error: {e}")
    
    # Index documents
    indexed = 0
    for i, doc in enumerate(data):
        try:
            client.index(index="fuel_quality", id=i+1, body=doc)
            indexed += 1
            if indexed % 10 == 0:
                print(f"Indexed {indexed} documents...")
        except Exception as e:
            print(f"Error indexing doc {i}: {e}")
    
    print(f"Successfully indexed {indexed} documents")

def main():
    print("=== Indexing Collected Fuel Data ===")
    
    # Check if OpenSearch is ready
    endpoint = get_opensearch_endpoint()
    if not endpoint:
        print("OpenSearch not ready yet. Try again in a few minutes.")
        return
    
    # Load collected data
    try:
        with open('fuel_data_collected.json', 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} fuel samples")
    except FileNotFoundError:
        print("No collected data found. Run collect_fuel_data.py first.")
        return
    
    # Create OpenSearch client and index data
    client = create_opensearch_client(endpoint)
    index_fuel_data(client, data)
    
    print("\n=== Ready for RAG Queries! ===")

if __name__ == "__main__":
    main()