import boto3
import json
import sqlite3
import os
from datetime import datetime

class FuelRAGSimulator:
    def __init__(self):
        self.db_path = 'fuel_quality.db'
        self.opensearch_available = False
        self.setup_local_db()
        
    def setup_local_db(self):
        """Create local SQLite database to simulate OpenSearch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fuel_data (
                id INTEGER PRIMARY KEY,
                fuel_id TEXT,
                timestamp TEXT,
                temperature_c REAL,
                density_kg_m3 REAL,
                viscosity_cSt REAL,
                sulfur_ppm REAL,
                moisture_pct REAL,
                octane_rating REAL,
                batch_quality TEXT,
                content TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Local database initialized")
    
    def index_data(self, data):
        """Index data to local DB (simulates OpenSearch indexing)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO fuel_data 
                (fuel_id, timestamp, temperature_c, density_kg_m3, viscosity_cSt, 
                 sulfur_ppm, moisture_pct, octane_rating, batch_quality, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['fuel_id'], item['timestamp'], item['temperature_c'],
                item['density_kg_m3'], item['viscosity_cSt'], item['sulfur_ppm'],
                item['moisture_pct'], item['octane_rating'], item['batch_quality'],
                item.get('content', '')
            ))
        
        conn.commit()
        conn.close()
        print(f"Indexed {len(data)} records to local database")
    
    def search_data(self, query):
        """Search local DB (simulates OpenSearch search)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple text search
        cursor.execute('''
            SELECT content FROM fuel_data 
            WHERE content LIKE ? OR batch_quality LIKE ?
            LIMIT 5
        ''', (f'%{query}%', f'%{query}%'))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def query_rag(self, question):
        """Complete RAG query with local search + Bedrock"""
        print(f"\nQuestion: {question}")
        
        # Search local database
        context_docs = self.search_data(question)
        
        if not context_docs:
            context = "No specific fuel data found in database."
        else:
            context = "\n".join(context_docs)
        
        # Query Bedrock with context
        prompt = f"""You are a fuel quality expert. Answer based on the fuel data and standards.

Fuel Data Context:
{context}

Standards:
- Normal temperature: 15-25°C (contaminated >30°C)
- Normal density: 720-780 kg/m³ (contaminated <700)
- Normal sulfur: 5-15 ppm (contaminated >50)
- Normal moisture: 0.01-0.05% (contaminated >0.1%)

Question: {question}
Answer:"""
        
        try:
            # Create fresh bedrock client to avoid token expiration
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            response = bedrock.invoke_model(
                modelId='amazon.titan-text-express-v1',
                body=json.dumps({
                    'inputText': prompt,
                    'textGenerationConfig': {'maxTokenCount': 300, 'temperature': 0.1}
                })
            )
            result = json.loads(response['body'].read())
            answer = result['results'][0]['outputText']
            print(f"Answer: {answer}")
            return answer
        except Exception as e:
            print(f"Error: {e}")
            return str(e)
    
    def load_sample_data(self):
        """Load collected fuel data into local database"""
        try:
            with open('fuel_data_collected.json', 'r') as f:
                data = json.load(f)
            self.index_data(data)
            return len(data)
        except FileNotFoundError:
            print("No fuel_data_collected.json found. Run collect_fuel_data.py first.")
            return 0
    
    def check_opensearch_status(self):
        """Check if OpenSearch is ready and switch if available"""
        try:
            opensearch = boto3.client('opensearch', region_name='us-east-1')
            response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
            
            if not response['DomainStatus']['Processing']:
                endpoint = response['DomainStatus'].get('Endpoint')
                if endpoint:
                    print(f"OpenSearch is ready! Endpoint: {endpoint}")
                    self.opensearch_available = True
                    return True
        except:
            pass
        return False

def main():
    print("=" * 60)
    print("🛢️  FUEL QUALITY RAG SIMULATOR")
    print("=" * 60)
    
    rag = FuelRAGSimulator()
    
    # Load sample data
    data_count = rag.load_sample_data()
    print(f"Loaded {data_count} fuel samples into local database")
    
    # Check OpenSearch status
    if rag.check_opensearch_status():
        print("🔄 OpenSearch is ready! You can upgrade to full system.")
    else:
        print("⏳ OpenSearch still creating. Using local simulation.")
    
    print("\n" + "=" * 60)
    
    # Test queries
    test_questions = [
        "What indicates contaminated fuel?",
        "Is 45°C temperature normal for fuel?",
        "What causes high sulfur content?",
        "How do I detect fuel contamination?"
    ]
    
    for question in test_questions:
        rag.query_rag(question)
        print("-" * 60)
    
    # Interactive mode
    print("\n🔍 Interactive Mode (type 'quit' to exit):")
    while True:
        try:
            user_question = input("\nYour question: ").strip()
            if user_question.lower() in ['quit', 'exit', 'q']:
                break
            if user_question:
                rag.query_rag(user_question)
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()