import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def search_fuel_data(query):
    # OpenSearch client setup (will need actual endpoint)
    host = 'fuel-quality-opensearch-domain-endpoint'
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
    
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["content", "batch_quality", "fuel_id"]
            }
        },
        "size": 5
    }
    
    try:
        response = client.search(index="fuel_quality", body=search_body)
        docs = [hit["_source"]["content"] for hit in response["hits"]["hits"]]
        return docs
    except Exception as e:
        print(f"Search error: {e}")
        return []

def query_bedrock_with_context(query, context_docs):
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    context = "\n".join(context_docs)
    prompt = f"""Based on the following fuel quality data, answer the question:

Context:
{context}

Question: {query}

Answer:"""
    
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                'inputText': prompt,
                'textGenerationConfig': {
                    'maxTokenCount': 300,
                    'temperature': 0.1
                }
            })
        )
        
        result = json.loads(response['body'].read())
        return result['results'][0]['outputText']
        
    except Exception as e:
        return f"Bedrock error: {e}"

def rag_query(question):
    print(f"Question: {question}")
    print("Searching fuel quality database...")
    
    # Search OpenSearch for relevant documents
    context_docs = search_fuel_data(question)
    
    if not context_docs:
        return "No relevant fuel quality data found."
    
    print(f"Found {len(context_docs)} relevant documents")
    
    # Query Bedrock with context
    answer = query_bedrock_with_context(question, context_docs)
    return answer

def main():
    test_questions = [
        "What indicates contaminated fuel?",
        "What are normal temperature ranges for fuel?",
        "How does high sulfur content affect fuel quality?",
        "What density values suggest fuel contamination?"
    ]
    
    print("=== RAG Query Test ===")
    
    for question in test_questions:
        print(f"\n{'='*50}")
        answer = rag_query(question)
        print(f"Answer: {answer}")

if __name__ == "__main__":
    main()