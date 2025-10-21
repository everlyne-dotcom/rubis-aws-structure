# Fuel Quality Data Generator

## Setup
```bash
pip install -r requirements.txt
```

## Environment Variables
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## Run
```bash
python fuel_data_generator.py
```

## Output
- Streams to IoT topic: `fuel/quality/readings`
- 15% contaminated samples by default
- 3-second intervals between samples
- 20 fuel tanks (TANK-1 to TANK-20)