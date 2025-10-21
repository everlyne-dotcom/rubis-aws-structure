import boto3
import json

def test_bedrock():
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                'inputText': 'Analyze fuel quality: temperature 45C, density 680 kg/m3, sulfur 120ppm. Is this contaminated?',
                'textGenerationConfig': {
                    'maxTokenCount': 200,
                    'temperature': 0.1
                }
            })
        )
        
        result = json.loads(response['body'].read())
        print("SUCCESS: Bedrock Test Passed")
        print("Response:", result['results'][0]['outputText'])
        return True
        
    except Exception as e:
        print("ERROR: Bedrock failed -", str(e))
        return False

def test_opensearch():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.list_domain_names()
        print("SUCCESS: OpenSearch access confirmed")
        print("Domains:", len(response['DomainNames']))
        return True
        
    except Exception as e:
        print("ERROR: OpenSearch failed -", str(e))
        return False

def main():
    print("=== Testing AWS Services ===")
    
    bedrock_ok = test_bedrock()
    opensearch_ok = test_opensearch()
    
    if bedrock_ok and opensearch_ok:
        print("\n=== READY TO PROCEED ===")
        print("Next: Deploy OpenSearch domain from dia.yaml")
    else:
        print("\n=== NEED TO FIX PERMISSIONS ===")

if __name__ == "__main__":
    main()