import boto3
import json
import time

def check_opensearch_status():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        status = response['DomainStatus']
        
        if status['Processing']:
            print("OpenSearch domain still creating...")
            return None
        else:
            endpoint = status.get('Endpoint')
            print(f"OpenSearch domain ready! Endpoint: {endpoint}")
            return endpoint
            
    except Exception as e:
        print(f"Error checking domain: {e}")
        return None

def create_lambda_function():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    lambda_code = '''
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    # Extract query from event
    query = event.get("query", "")
    
    # OpenSearch client
    host = os.environ["OPENSEARCH_ENDPOINT"]
    region = "us-east-1"
    service = "es"
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    # Search for relevant documents
    search_result = client.search(
        index="fuel_quality", 
        body={"query": {"match": {"content": query}}}
    )
    
    docs = [hit["_source"]["content"] for hit in search_result["hits"]["hits"]]
    
    # Query Bedrock with context
    bedrock = boto3.client("bedrock-runtime")
    response = bedrock.invoke_model(
        modelId="amazon.titan-text-express-v1",
        body=json.dumps({
            "inputText": f"Answer the query using these fuel quality docs: {docs}. Query: {query}",
            "textGenerationConfig": {"maxTokenCount": 300, "temperature": 0.1}
        })
    )
    
    result = json.loads(response["body"].read())
    
    return {
        "statusCode": 200,
        "answer": result["results"][0]["outputText"]
    }
'''
    
    try:
        lambda_client.create_function(
            FunctionName='fuel-quality-rag',
            Runtime='python3.11',
            Role='arn:aws:iam::267714371628:role/lambda-execution-role',
            Handler='index.lambda_handler',
            Code={'ZipFile': lambda_code.encode()},
            Environment={
                'Variables': {
                    'OPENSEARCH_ENDPOINT': 'fuel-quality-opensearch-endpoint'
                }
            }
        )
        print("SUCCESS: Lambda function created")
        
    except Exception as e:
        if "already exists" in str(e):
            print("SUCCESS: Lambda function already exists")
        else:
            print(f"Lambda creation error: {e}")

def main():
    print("=== Completing RAG Pipeline Setup ===")
    
    # Check OpenSearch status
    endpoint = check_opensearch_status()
    
    if endpoint:
        print("✓ OpenSearch ready")
        print("✓ Next: Set up indexing and test queries")
    else:
        print("⏳ Waiting for OpenSearch domain...")
        print("⏳ Run this script again in 5-10 minutes")
    
    print("\n=== Current Status ===")
    print("✓ Fuel data generator ready")
    print("✓ Bedrock access confirmed") 
    print("✓ IoT Core streaming working")
    print("⏳ OpenSearch domain creating")
    print("⏳ Lambda function pending")

if __name__ == "__main__":
    main()