import boto3
import json
import time

def setup_kinesis_stream():
    kinesis = boto3.client('kinesis', region_name='us-east-1')
    
    try:
        kinesis.create_stream(
            StreamName='fuel-quality-stream',
            ShardCount=1
        )
        print("✅ Kinesis stream created")
        
        # Wait for stream to be active
        waiter = kinesis.get_waiter('stream_exists')
        waiter.wait(StreamName='fuel-quality-stream')
        print("✅ Kinesis stream is active")
        
    except Exception as e:
        if "already exists" in str(e):
            print("✅ Kinesis stream already exists")
        else:
            print(f"❌ Kinesis error: {e}")

def setup_iot_rule():
    iot = boto3.client('iot', region_name='us-east-1')
    
    # Create IAM role for IoT rule
    iam = boto3.client('iam')
    
    role_doc = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "iot.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["kinesis:PutRecord", "kinesis:PutRecords"],
            "Resource": "arn:aws:kinesis:us-east-1:267714371628:stream/fuel-quality-stream"
        }]
    }
    
    try:
        # Create role
        iam.create_role(
            RoleName='FuelQualityIoTRole',
            AssumeRolePolicyDocument=json.dumps(role_doc)
        )
        
        # Attach policy
        iam.put_role_policy(
            RoleName='FuelQualityIoTRole',
            PolicyName='KinesisAccess',
            PolicyDocument=json.dumps(policy_doc)
        )
        
        time.sleep(10)  # Wait for role propagation
        print("✅ IAM role created")
        
    except Exception as e:
        if "already exists" in str(e):
            print("✅ IAM role already exists")
        else:
            print(f"❌ IAM error: {e}")
    
    try:
        # Create IoT rule
        iot.create_topic_rule(
            ruleName='fuel_quality_data_rule',
            topicRulePayload={
                'sql': "SELECT * FROM 'fuel/quality/readings'",
                'actions': [{
                    'kinesis': {
                        'roleArn': 'arn:aws:iam::267714371628:role/FuelQualityIoTRole',
                        'streamName': 'fuel-quality-stream',
                        'partitionKey': '${fuel_id}'
                    }
                }]
            }
        )
        print("✅ IoT rule created")
        
    except Exception as e:
        if "already exists" in str(e):
            print("✅ IoT rule already exists")
        else:
            print(f"❌ IoT rule error: {e}")

def main():
    print("Setting up Fuel Quality Data Pipeline...")
    setup_kinesis_stream()
    setup_iot_rule()
    print("\n🚀 Pipeline setup complete!")
    print("Now run: python fuel_data_generator.py")
    print("Data will flow: IoT Core → Kinesis → Ready for processing")

if __name__ == "__main__":
    main()