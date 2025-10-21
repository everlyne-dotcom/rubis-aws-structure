import boto3
import json
import sqlite3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def check_opensearch_ready():
    """Check if OpenSearch domain is ready"""
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        status = response['DomainStatus']
        
        if not status['Processing']:
            endpoint = status.get('Endpoint')
            if endpoint:
                print(f"✅ OpenSearch ready! Endpoint: {endpoint}")
                return endpoint
        
        print("⏳ OpenSearch still creating...")
        return None
    except Exception as e:
        print(f"❌ Error checking OpenSearch: {e}")
        return None

def migrate_data_to_opensearch(endpoint):
    """Migrate data from local SQLite to OpenSearch"""
    # Setup OpenSearch client
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    client = OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
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
        print("✅ Created fuel_quality index")
    except Exception as e:
        if "already exists" in str(e):
            print("✅ Index already exists")
        else:
            print(f"❌ Index creation error: {e}")
            return False
    
    # Migrate data from SQLite
    conn = sqlite3.connect('fuel_quality.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM fuel_data')
    rows = cursor.fetchall()
    
    migrated = 0
    for row in rows:
        doc = {
            "fuel_id": row[1],
            "timestamp": row[2],
            "temperature_c": row[3],
            "density_kg_m3": row[4],
            "viscosity_cSt": row[5],
            "sulfur_ppm": row[6],
            "moisture_pct": row[7],
            "octane_rating": row[8],
            "batch_quality": row[9],
            "content": row[10]
        }
        
        try:
            client.index(index="fuel_quality", id=row[0], body=doc)
            migrated += 1
        except Exception as e:
            print(f"❌ Error indexing doc {row[0]}: {e}")
    
    conn.close()
    print(f"✅ Migrated {migrated} documents to OpenSearch")
    return True

def main():
    print("=" * 60)
    print("🔄 UPGRADING TO OPENSEARCH")
    print("=" * 60)
    
    # Check if OpenSearch is ready
    endpoint = check_opensearch_ready()
    
    if endpoint:
        print("🚀 Starting migration...")
        if migrate_data_to_opensearch(endpoint):
            print("\n✅ UPGRADE COMPLETE!")
            print("Your RAG system now uses OpenSearch instead of local database")
            print(f"Endpoint: {endpoint}")
        else:
            print("\n❌ Migration failed. Check permissions and try again.")
    else:
        print("\n⏳ OpenSearch not ready yet. Try again later.")

if __name__ == "__main__":
    main()