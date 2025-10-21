import boto3
import json
import random
import time
from datetime import datetime

def generate_enhanced_sample():
    """Generate detailed fuel sample with human-readable comments"""
    
    # Sensor IDs
    sensor_ids = [f"FXD-TNK-{str(i).zfill(3)}" for i in range(1, 21)]
    
    # Determine if contaminated
    is_contaminated = random.random() < 0.15
    
    if is_contaminated:
        # Contaminated readings
        temperature = round(random.uniform(35, 50), 1)
        density = round(random.uniform(650, 700), 1)
        water_ppm = round(random.uniform(80, 200), 1)
        carbon_ppm = round(random.uniform(8, 15), 1)
        sediment_ppm = round(random.uniform(5, 12), 1)
        fuel_level = random.randint(15000, 55000)
        
        # Generate contamination comments
        comments = []
        if temperature > 40:
            comments.append(f"High temperature ({temperature}°C) indicates thermal stress")
        if density < 680:
            comments.append(f"Low density ({density} kg/m³) suggests fuel degradation")
        if water_ppm > 100:
            comments.append(f"Excessive water content ({water_ppm} ppm) - contamination risk")
        if carbon_ppm > 10:
            comments.append(f"Elevated carbon residue ({carbon_ppm} ppm) indicates poor quality")
        if sediment_ppm > 8:
            comments.append(f"High sediment levels ({sediment_ppm} ppm) require filtration")
        
        comment = ". ".join(comments) + ". IMMEDIATE ATTENTION REQUIRED."
        batch_quality = "CONTAMINATED"
        
    else:
        # Normal readings
        temperature = round(random.uniform(15, 25), 1)
        density = round(random.uniform(720, 780), 1)
        water_ppm = round(random.uniform(10, 50), 1)
        carbon_ppm = round(random.uniform(1, 4), 1)
        sediment_ppm = round(random.uniform(0.5, 2.5), 1)
        fuel_level = random.randint(20000, 60000)
        
        # Generate normal comments
        comments = []
        if 720 <= density <= 780:
            comments.append("Normal density range maintained")
        if water_ppm < 30:
            comments.append("Water content within acceptable limits")
        elif water_ppm > 40:
            comments.append("Slightly elevated water level - may indicate mild condensation in storage")
        if temperature < 20:
            comments.append("Optimal storage temperature")
        if carbon_ppm < 2:
            comments.append("Excellent carbon residue levels")
        if fuel_level < 25000:
            comments.append("Fuel level approaching minimum threshold - schedule refill")
        
        comment = ". ".join(comments) + ". All parameters within specification."
        batch_quality = "CLEAN"
    
    return {
        "sensor_id": random.choice(sensor_ids),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature_c": temperature,
        "density_kg_per_m3": density,
        "water_ppm": water_ppm,
        "carbon_ppm": carbon_ppm,
        "sediment_ppm": sediment_ppm,
        "fuel_level_liters": fuel_level,
        "batch_quality": batch_quality,
        "comments": comment,
        "content": f"{batch_quality} fuel from {random.choice(sensor_ids)}: temp {temperature}°C, density {density} kg/m³, water {water_ppm} ppm, carbon {carbon_ppm} ppm"
    }

def main():
    print("=== Enhanced Fuel Data Generator ===")
    print("Generating detailed readings with human-readable comments...")
    
    # Generate and save enhanced samples
    samples = []
    for i in range(50):
        sample = generate_enhanced_sample()
        samples.append(sample)
        print(f"Generated: {sample['sensor_id']} - {sample['batch_quality']}")
        print(f"Comment: {sample['comments'][:80]}...")
        print("-" * 60)
    
    # Save to file
    with open('enhanced_fuel_data.json', 'w') as f:
        json.dump(samples, f, indent=2)
    
    print(f"\n✅ Generated {len(samples)} enhanced fuel samples")
    print("Saved to: enhanced_fuel_data.json")
    
    # Show sample record
    print("\n📋 Sample Record:")
    print(json.dumps(samples[0], indent=2))

if __name__ == "__main__":
    main()