import boto3
import json
import time

def create_opensearch_domain():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    domain_config = {
        'DomainName': 'fuel-quality-opensearch',
        'EngineVersion': 'OpenSearch_2.11',
        'ClusterConfig': {
            'InstanceType': 't3.small.search',
            'InstanceCount': 1
        },
        'EBSOptions': {
            'EBSEnabled': True,
            'VolumeSize': 20,
            'VolumeType': 'gp3'
        },
        'EncryptionAtRestOptions': {
            'Enabled': True
        },
        'NodeToNodeEncryptionOptions': {
            'Enabled': True
        },
        'DomainEndpointOptions': {
            'EnforceHTTPS': True
        },
        'AdvancedSecurityOptions': {
            'Enabled': True,
            'InternalUserDatabaseEnabled': True,
            'MasterUserOptions': {
                'MasterUserName': 'admin',
                'MasterUserPassword': 'FuelQuality123!'
            }
        },
        'AccessPolicies': json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:sts::267714371628:assumed-role/AWSReservedSSO_Rubis_LLm_3d6c9f28c65e627f/hosting"},
                "Action": "es:*",
                "Resource": "arn:aws:es:us-east-1:267714371628:domain/fuel-quality-opensearch/*"
            }]
        })
    }
    
    try:
        print("Creating OpenSearch domain...")
        response = opensearch.create_domain(**domain_config)
        print("SUCCESS: OpenSearch domain creation initiated")
        print("Domain ARN:", response['DomainStatus']['ARN'])
        print("This will take 10-15 minutes to complete...")
        
        return True
        
    except Exception as e:
        if "already exists" in str(e):
            print("SUCCESS: OpenSearch domain already exists")
            return True
        else:
            print("ERROR:", str(e))
            return False

def main():
    print("=== Creating OpenSearch Domain ===")
    
    if create_opensearch_domain():
        print("\n=== NEXT STEPS ===")
        print("1. Wait for OpenSearch domain to be active (10-15 mins)")
        print("2. Run fuel data generator to collect data")
        print("3. Index data into OpenSearch")
        print("4. Test RAG queries with Bedrock")

if __name__ == "__main__":
    main()