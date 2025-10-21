import boto3

def check_opensearch_status():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        status = response['DomainStatus']
        
        print(f"Domain Status: {status['DomainProcessingStatus']}")
        print(f"Processing: {status['Processing']}")
        
        if not status['Processing']:
            endpoint = status.get('Endpoint')
            print(f"SUCCESS: Domain ready! Endpoint: {endpoint}")
            return endpoint
        else:
            print("WAITING: Domain still being created...")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("=== Pipeline Status Check ===")
    
    endpoint = check_opensearch_status()
    
    print("\n=== Next Steps ===")
    if endpoint:
        print("1. Update scripts with OpenSearch endpoint")
        print("2. Create fuel quality index")
        print("3. Test RAG queries")
        print("4. Deploy Lambda function")
    else:
        print("1. Wait 5-10 more minutes")
        print("2. Run this script again")
        print("3. Meanwhile, collect fuel data with generator")

if __name__ == "__main__":
    main()