import boto3

def create_simple_domain():
    opensearch = boto3.client('opensearch', region_name='us-east-1')
    
    # Much simpler configuration - faster creation
    simple_config = {
        'DomainName': 'fuel-quality-simple',
        'EngineVersion': 'OpenSearch_2.11',
        'ClusterConfig': {
            'InstanceType': 't3.small.search',
            'InstanceCount': 1
        },
        'EBSOptions': {
            'EBSEnabled': True,
            'VolumeSize': 10,
            'VolumeType': 'gp2'  # Simpler volume type
        },
        'AccessPolicies': '''{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "es:*",
                "Resource": "arn:aws:es:us-east-1:267714371628:domain/fuel-quality-simple/*"
            }]
        }'''
        # No encryption, no fine-grained access = faster creation
    }
    
    try:
        response = opensearch.create_domain(**simple_config)
        print("Simple domain creation started - should be ready in 10-15 minutes")
        print("Domain ARN:", response['DomainStatus']['ARN'])
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating simpler OpenSearch domain for faster setup...")
    create_simple_domain()