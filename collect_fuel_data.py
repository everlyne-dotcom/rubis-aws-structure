import boto3
import json
import random
import time
from datetime import datetime

# Store data locally while OpenSearch is being created
fuel_data_storage = []

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
    print("=== Collecting Fuel Data ===")
    print("Storing locally until OpenSearch is ready...")
    
    count = 0
    contaminated_count = 0
    
    try:
        while count < 50:  # Collect 50 samples
            sample = generate_sample()
            
            # Add content field for RAG
            sample["content"] = f"{sample['batch_quality']} fuel from {sample['fuel_id']}: temp {sample['temperature_c']}C, density {sample['density_kg_m3']} kg/m3, sulfur {sample['sulfur_ppm']}ppm"
            
            fuel_data_storage.append(sample)
            
            if sample["batch_quality"] == "CONTAMINATED":
                contaminated_count += 1
            
            count += 1
            print(f"Collected: {sample['fuel_id']} - {sample['batch_quality']}")
            time.sleep(1)
        
        # Save to file
        with open('fuel_data_collected.json', 'w') as f:
            json.dump(fuel_data_storage, f, indent=2)
        
        print(f"\n=== Collection Complete ===")
        print(f"Total samples: {count}")
        print(f"Contaminated: {contaminated_count} ({contaminated_count/count*100:.1f}%)")
        print(f"Saved to: fuel_data_collected.json")
        print("\nReady to index when OpenSearch is available!")
        
    except KeyboardInterrupt:
        print(f"\nStopped. Collected {count} samples")

if __name__ == "__main__":
    main()