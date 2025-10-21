import boto3
import json

def create_iot_to_s3_rule():
    iot = boto3.client('iot', region_name='us-east-1')
    
    rule_payload = {
        'sql': "SELECT * FROM 'fuel/quality/readings'",
        'actions': [{
            's3': {
                'roleArn': 'arn:aws:iam::267714371628:role/service-role/IoTToS3Role',
                'bucketName': 'fuel-quality-data-267714371628',
                'key': 'fuel-data/${fuel_id}/${timestamp()}.json'
            }
        }]
    }
    
    try:
        iot.create_topic_rule(
            ruleName='fuel_data_to_s3',
            topicRulePayload=rule_payload
        )
        print("IoT Rule created: fuel_data_to_s3")
        print("Now IoT data will flow to S3 in real-time")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_iot_to_s3_rule()