
# Fuel Quality LLM System

AI-powered fuel quality monitoring system using AWS services and Streamlit dashboard.

## Overview

Real-time monitoring system for fuel quality in refinery and transport tanks using IoT sensors, machine learning, and LLM-powered analysis.

## Features

- **Real-time Monitoring**: Live sensor data streaming from fuel tanks
- **AI Analysis**: LLM-powered contamination detection and reasoning
- **Interactive Dashboard**: Professional dark-themed Streamlit interface
- **Alerts System**: Critical contamination alerts with recommendations
- **Data Analytics**: Viscosity, optical resolution, and quality metrics
- **Report Generation**: Export data in CSV, JSON, or PDF formats

## Architecture

```
Fuel Sensors → IoT Core → OpenSearch
                              ↓
User Query → API Gateway → Lambda → Bedrock + OpenSearch → Response
```

## AWS Services Used

- **IoT Core** - Sensor data ingestion
- **OpenSearch** - Data storage and search
- **Bedrock** - AI/LLM analysis (Titan model)
- **Lambda** - Serverless processing
- **SageMaker** - ML inference
- **CloudWatch** - Monitoring and logs

## Installation

### Prerequisites
- Python 3.10+
- AWS Account with configured credentials
- Git

### Setup

1. **Clone repository**
```bash
git clone <repository-url>
cd rubis-aws-structure
```

2. **Create virtual environment**
```bash
python -m venv fuel-rag-env
fuel-rag-env\Scripts\activate  # Windows
source fuel-rag-env/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements_streamlit.txt
```

4. **Configure AWS credentials**
```bash
aws configure
```

## Usage

### 1. Check OpenSearch Status
```bash
python check_status.py
```

### 2. Generate Fuel Data
```bash
python fuel_data_generator.py
```

### 3. Run Dashboard
```bash
streamlit run fuel_quality_dashboard.py
```

### 4. Access Dashboard
Open browser to `http://localhost:8501`

## Dashboard Pages

- **Dashboard** - Overview metrics and contamination trends
- **Live Feed** - Real-time sensor readings with viscosity/optical measurements
- **AI Reports** - LLM analysis and recommendations
- **Alerts** - Critical contamination alerts
- **System Logs** - Service monitoring and events

## Data Parameters

### Normal Ranges
- Temperature: 15-25°C
- Density: 720-780 kg/m³
- Viscosity: 1.2-2.5 cSt
- Sulfur: 5-15 ppm
- Moisture: 0.01-0.05%
- Optical Resolution: 0.85-0.95

### Contaminated Indicators
- Temperature: >35°C
- Density: <700 kg/m³
- Viscosity: >4.0 cSt
- Sulfur: >50 ppm
- Moisture: >0.15%
- Optical Resolution: <0.70

## Project Structure

```
rubis-aws-structure/
├── fuel_quality_dashboard.py    # Main Streamlit dashboard
├── fuel_data_generator.py       # IoT data generator
├── check_status.py              # AWS service status checker
├── requirements_streamlit.txt   # Python dependencies
├── dia.yaml                     # CloudFormation template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Configuration

### Database
- SQLite database: `fuel_quality_llm.db`
- Auto-generates sample data on first run

### AWS Region
Default: `us-east-1`
Change in scripts if needed

## Troubleshooting

### AWS Credentials Error
```bash
aws sts get-caller-identity  # Verify credentials
aws configure  # Reconfigure if needed
```

### Virtual Environment Issues (Windows PowerShell)
```bash
cmd  # Switch to Command Prompt
fuel-rag-env\Scripts\activate.bat
```

### Empty Dashboard
Click "Generate Sample Data" in sidebar

## Development

### Generate New Sample Data
```bash
python fuel_data_generator.py
```

### Test RAG Pipeline
```bash
python rag_query_test.py
```

### Deploy to AWS
```bash
python setup_pipeline.py
```

## License

MIT License

## Contributors

Fuel Quality Monitoring Team

## Version

v2.1 - Powered by AWS Bedrock & SageMaker
