import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

class FuelQualityRAG:
    def __init__(self, opensearch_endpoint):
        self.opensearch_endpoint = opensearch_endpoint
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.opensearch = self._get_opensearch_client()
    
    def _get_opensearch_client(self):
        region = 'us-east-1'
        service = 'es'
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
        
        return OpenSearch(
            hosts=[{'host': self.opensearch_endpoint, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
    
    def search_fuel_data(self, query):
        search_body = {
            "query": {"multi_match": {"query": query, "fields": ["content", "batch_quality"]}},
            "size": 3
        }
        
        try:
            response = self.opensearch.search(index="fuel_quality", body=search_body)
            return [hit["_source"]["content"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def query_bedrock(self, query, context_docs):
        context = "\n".join(context_docs)
        prompt = f"Based on fuel quality data: {context}\n\nQuestion: {query}\nAnswer:"
        
        try:
            response = self.bedrock.invoke_model(
                modelId='amazon.titan-text-express-v1',
                body=json.dumps({
                    'inputText': prompt,
                    'textGenerationConfig': {'maxTokenCount': 300, 'temperature': 0.1}
                })
            )
            result = json.loads(response['body'].read())
            return result['results'][0]['outputText']
        except Exception as e:
            return f"Error: {e}"
    
    def ask(self, question):
        print(f"Question: {question}")
        
        # Search OpenSearch
        docs = self.search_fuel_data(question)
        if not docs:
            return "No relevant fuel data found."
        
        # Query Bedrock with context
        answer = self.query_bedrock(question, docs)
        return answer

def main():
    # Will update with actual endpoint when ready
    endpoint = "fuel-quality-opensearch-endpoint"
    
    rag = FuelQualityRAG(endpoint)
    
    questions = [
        "What indicates contaminated fuel?",
        "What are normal fuel temperature ranges?",
        "How does sulfur content affect fuel quality?"
    ]
    
    for q in questions:
        print(f"\n{'='*50}")
        answer = rag.ask(q)
        print(f"Answer: {answer}")

if __name__ == "__main__":
    main()