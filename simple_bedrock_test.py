import boto3
import json

def test_bedrock():
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    try:
        # Test Bedrock access
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                'inputText': 'Analyze this fuel quality data: temperature 45C, density 680 kg/m3, sulfur 120ppm. Is this fuel contaminated?',
                'textGenerationConfig': {
                    'maxTokenCount': 200,
                    'temperature': 0.1
                }
            })
        )
        
        result = json.loads(response['body'].read())
        print("✅ Bedrock Test Success:")
        print(result['results'][0]['outputText'])
        
    except Exception as e:
        print(f"❌ Bedrock error: {e}")

def test_sagemaker():
    sagemaker = boto3.client('sagemaker', region_name='us-east-1')
    
    try:
        # List existing endpoints
        response = sagemaker.list_endpoints()
        print(f"✅ SageMaker access: {len(response['Endpoints'])} endpoints found")
        
    except Exception as e:
        print(f"❌ SageMaker error: {e}")

def main():
    print("Testing AWS Services Access...")
    test_bedrock()
    test_sagemaker()

if __name__ == "__main__":
    main()