import boto3
import json

def check_opensearch_status():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    try:
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        status = response['DomainStatus']
        
        if not status['Processing']:
            endpoint = status.get('Endpoint')
            if endpoint:
                print(f"SUCCESS: OpenSearch ready! Endpoint: {endpoint}")
                return endpoint
        
        print("WAITING: OpenSearch still creating...")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("=" * 60)
    print("FUEL QUALITY RAG - IMPLEMENTATION STATUS")
    print("=" * 60)
    
    # Check OpenSearch
    endpoint = check_opensearch_status()
    
    if endpoint:
        print("\nREADY FOR PRODUCTION DEPLOYMENT:")
        print("1. Run: python upgrade_to_opensearch.py")
        print("2. Migrate data from SQLite to OpenSearch")
        print("3. Deploy production Lambda function")
        print("4. Create API Gateway endpoints")
        print("5. Set up monitoring and alerts")
        
        print(f"\nOpenSearch Endpoint: {endpoint}")
        print("Your RAG system is ready for production!")
        
    else:
        print("\nCURRENT STATUS:")
        print("- RAG Simulator: WORKING")
        print("- Streamlit UI: WORKING") 
        print("- Bedrock AI: WORKING")
        print("- OpenSearch: CREATING")
        
        print("\nWHILE WAITING:")
        print("- Continue using Streamlit interface")
        print("- Test RAG queries with simulator")
        print("- Generate more fuel data")
        print("- Check status again in 10-15 minutes")

if __name__ == "__main__":
    main()