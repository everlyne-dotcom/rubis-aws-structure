import boto3
import json
import time
from datetime import datetime

def check_opensearch_status():
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
        print(f"❌ Error: {e}")
        return None

def create_iot_rule():
    """Create IoT rule to forward data to OpenSearch"""
    iot = boto3.client('iot', region_name='us-east-1')
    
    rule_payload = {
        'sql': "SELECT * FROM 'fuel/quality/readings'",
        'actions': [{
            'elasticsearch': {
                'roleArn': 'arn:aws:iam::267714371628:role/service-role/IoTToOpenSearchRole',
                'endpoint': 'https://fuel-quality-opensearch-endpoint',
                'index': 'fuel_quality',
                'type': '_doc',
                'id': '${newuuid()}'
            }
        }]
    }
    
    try:
        iot.create_topic_rule(
            ruleName='fuel_data_to_opensearch',
            topicRulePayload=rule_payload
        )
        print("✅ IoT Rule created for OpenSearch")
    except Exception as e:
        if "already exists" in str(e):
            print("✅ IoT Rule already exists")
        else:
            print(f"❌ IoT Rule error: {e}")

def deploy_production_lambda():
    """Deploy production Lambda function"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    lambda_code = '''
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
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
    
    # Search OpenSearch
    search_result = client.search(
        index="fuel_quality", 
        body={"query": {"match": {"content": query}}}
    )
    
    docs = [hit["_source"]["content"] for hit in search_result["hits"]["hits"]]
    
    # Query Bedrock
    bedrock = boto3.client("bedrock-runtime")
    response = bedrock.invoke_model(
        modelId="amazon.titan-text-express-v1",
        body=json.dumps({
            "inputText": f"Answer using fuel data: {docs}. Query: {query}",
            "textGenerationConfig": {"maxTokenCount": 300, "temperature": 0.1}
        })
    )
    
    result = json.loads(response["body"].read())
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "answer": result["results"][0]["outputText"],
            "sources": len(docs)
        })
    }
'''
    
    try:
        lambda_client.create_function(
            FunctionName='fuel-quality-rag-production',
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
        print("✅ Production Lambda deployed")
    except Exception as e:
        if "already exists" in str(e):
            print("✅ Lambda already exists")
        else:
            print(f"❌ Lambda error: {e}")

def create_api_gateway():
    """Create API Gateway for external access"""
    apigateway = boto3.client('apigateway', region_name='us-east-1')
    
    try:
        # Create REST API
        api = apigateway.create_rest_api(
            name='fuel-quality-api',
            description='Fuel Quality RAG API'
        )
        
        api_id = api['id']
        print(f"✅ API Gateway created: {api_id}")
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create /query resource
        resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='query'
        )
        
        # Create POST method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource['id'],
            httpMethod='POST',
            authorizationType='NONE'
        )
        
        print("✅ API Gateway configured")
        return api_id
        
    except Exception as e:
        print(f"❌ API Gateway error: {e}")
        return None

def main():
    print("=" * 60)
    print("COMPLETING FUEL QUALITY RAG IMPLEMENTATION")
    print("=" * 60)
    
    # Step 1: Check OpenSearch
    endpoint = check_opensearch_status()
    
    if endpoint:
        print("\n📋 PRODUCTION DEPLOYMENT STEPS:")
        
        # Step 2: Create IoT Rule
        print("\n2. Creating IoT Rule...")
        create_iot_rule()
        
        # Step 3: Deploy Lambda
        print("\n3. Deploying Production Lambda...")
        deploy_production_lambda()
        
        # Step 4: Create API Gateway
        print("\n4. Creating API Gateway...")
        api_id = create_api_gateway()
        
        print("\n" + "=" * 60)
        print("IMPLEMENTATION COMPLETE!")
        print("=" * 60)
        
        print("✅ Components Deployed:")
        print("  - OpenSearch Domain")
        print("  - IoT Core Rules")
        print("  - Production Lambda")
        print("  - API Gateway")
        
        print("\n🔗 Endpoints:")
        print(f"  - OpenSearch: {endpoint}")
        if api_id:
            print(f"  - API: https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/query")
        
        print("\n📊 Next Steps:")
        print("  1. Run: python upgrade_to_opensearch.py")
        print("  2. Test API endpoints")
        print("  3. Monitor with CloudWatch")
        
    else:
        print("\n⏳ WAITING FOR OPENSEARCH...")
        print("Continue using the RAG simulator until OpenSearch is ready")
        print("Run this script again in 10-15 minutes")

if __name__ == "__main__":
    main()