import boto3
import json
import random
import time
from datetime import datetime

def generate_sample():
    NORMAL_RANGES = {
        "temperature_c": (15, 25),
        "density_kg_m3": (720, 780),
        "viscosity_cSt": (1.2, 2.5),
        "sulfur_ppm": (5, 15),
        "moisture_pct": (0.01, 0.05),
        "octane_rating": (87, 95)
    }

    CONTAMINATED_RANGES = {
        "temperature_c": (35, 50),
        "density_kg_m3": (650, 700),
        "viscosity_cSt": (4.0, 8.0),
        "sulfur_ppm": (50, 150),
        "moisture_pct": (0.15, 0.30),
        "octane_rating": (75, 85)
    }
    
    is_contaminated = random.random() < 0.15
    ranges = CONTAMINATED_RANGES if is_contaminated else NORMAL_RANGES
    fuel_tanks = [f"TANK-{i}" for i in range(1, 21)]
    
    return {
        "fuel_id": random.choice(fuel_tanks),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature_c": round(random.uniform(*ranges["temperature_c"]), 1),
        "density_kg_m3": round(random.uniform(*ranges["density_kg_m3"]), 1),
        "viscosity_cSt": round(random.uniform(*ranges["viscosity_cSt"]), 2),
        "sulfur_ppm": round(random.uniform(*ranges["sulfur_ppm"]), 1),
        "moisture_pct": round(random.uniform(*ranges["moisture_pct"]), 3),
        "octane_rating": round(random.uniform(*ranges["octane_rating"]), 1),
        "batch_quality": "CONTAMINATED" if is_contaminated else "CLEAN"
    }

def main():
    iot_client = boto3.client('iot-data', region_name='us-east-1')
    
    print("=== Generating Live IoT Data ===")
    print("This will populate IoT Core analytics graphs")
    print("Go to: IoT Core -> Monitor to see live metrics")
    print("Go to: IoT Core -> Test -> MQTT test client")
    print("Subscribe to: fuel/quality/readings")
    print("\nPress Ctrl+C to stop\n")
    
    count = 0
    contaminated_count = 0
    
    try:
        while True:
            sample = generate_sample()
            
            if sample["batch_quality"] == "CONTAMINATED":
                contaminated_count += 1
            
            try:
                iot_client.publish(
                    topic='fuel/quality/readings',
                    qos=1,
                    payload=json.dumps(sample)
                )
                count += 1
                print(f"Sent #{count}: {sample['fuel_id']} - {sample['batch_quality']} (temp: {sample['temperature_c']}C)")
                
                if count % 20 == 0:
                    contamination_pct = (contaminated_count / count) * 100
                    print(f"\n--- SUMMARY: {count} messages sent, {contaminated_count} contaminated ({contamination_pct:.1f}%) ---\n")
                    
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
                
            time.sleep(2)  # Send every 2 seconds for faster analytics
            
    except KeyboardInterrupt:
        print(f"\nStopped. Total: {count} messages sent")
        print("Check IoT Core Monitor for analytics graphs!")

if __name__ == "__main__":
    main()