import boto3
import json
import random
import time
from datetime import datetime

# Configuration
BUCKET_NAME = "fuel-quality-data-267714371628"  # Using your account ID
DELAY_SECONDS = 3
CONTAMINATION_RATIO = 0.15
FUEL_TANKS = [f"TANK-{i}" for i in range(1, 21)]

# Data ranges
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

def generate_sample():
    is_contaminated = random.random() < CONTAMINATION_RATIO
    ranges = CONTAMINATED_RANGES if is_contaminated else NORMAL_RANGES
    
    return {
        "fuel_id": random.choice(FUEL_TANKS),
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
    s3 = boto3.client('s3', region_name='us-east-1')
    
    # Try to create bucket
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")
    except:
        print(f"Using existing bucket: {BUCKET_NAME}")
    
    count = 0
    contaminated_count = 0
    
    try:
        while True:
            sample = generate_sample()
            
            if sample["batch_quality"] == "CONTAMINATED":
                contaminated_count += 1
            
            # Store in S3
            key = f"fuel-data/{sample['fuel_id']}/{sample['timestamp']}.json"
            
            try:
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=key,
                    Body=json.dumps(sample),
                    ContentType='application/json'
                )
                count += 1
                print(f"Stored: {sample['fuel_id']} - {sample['batch_quality']}")
                
                if count % 50 == 0:
                    contamination_pct = (contaminated_count / count) * 100
                    print(f"Summary: {count} records stored — {contaminated_count} contaminated ({contamination_pct:.1f}%)")
                    
            except Exception as e:
                print(f"Error storing: {e}")
                time.sleep(5)
                
            time.sleep(DELAY_SECONDS)
            
    except KeyboardInterrupt:
        print(f"\nStopped. Total: {count} records, {contaminated_count} contaminated")
        print(f"Data stored in S3 bucket: {BUCKET_NAME}")

if __name__ == "__main__":
    main()