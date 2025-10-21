import boto3
import json
from datetime import datetime

# Test IoT connection
try:
    iot_client = boto3.client('iot-data', region_name='us-east-1')
    
    # Simple test message
    test_message = {
        "fuel_id": "TANK-1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature_c": 20.5,
        "batch_quality": "CLEAN"
    }
    
    print("Sending test message...")
    print(json.dumps(test_message, indent=2))
    
    response = iot_client.publish(
        topic='fuel/quality/readings',
        qos=1,
        payload=json.dumps(test_message)
    )
    
    print("SUCCESS: Message sent to IoT Core")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"ERROR: {e}")
    print("Check: 1) AWS credentials 2) Region 3) IoT permissions")