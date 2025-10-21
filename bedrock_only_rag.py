import boto3
import json

class BedrockOnlyRAG:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Load our collected fuel data as knowledge base
        try:
            with open('fuel_data_collected.json', 'r') as f:
                self.fuel_data = json.load(f)
            print(f"Loaded {len(self.fuel_data)} fuel samples as knowledge base")
        except FileNotFoundError:
            print("No fuel data found. Run collect_fuel_data.py first.")
            self.fuel_data = []
    
    def search_fuel_data(self, query):
        # Simple keyword matching in our local data
        relevant_docs = []
        query_lower = query.lower()
        
        for sample in self.fuel_data:
            content = sample.get('content', '').lower()
            if any(word in content for word in ['contaminated', 'clean', 'temperature', 'sulfur', 'density']):
                relevant_docs.append(sample['content'])
        
        return relevant_docs[:5]  # Return top 5 matches
    
    def ask(self, question):
        print(f"\nQuestion: {question}")
        
        # Get relevant fuel data
        context_docs = self.search_fuel_data(question)
        
        if not context_docs:
            context = "No specific fuel data available."
        else:
            context = "\n".join(context_docs)
        
        # Create comprehensive prompt with fuel quality knowledge
        prompt = f"""You are a fuel quality expert. Answer the question based on the provided fuel data and your knowledge of fuel quality standards.

Fuel Quality Data:
{context}

General Fuel Quality Standards:
- Normal temperature: 15-25°C
- Normal density: 720-780 kg/m³
- Normal sulfur content: 5-15 ppm
- Normal moisture: 0.01-0.05%
- Normal octane rating: 87-95

Contamination indicators:
- High temperature (>30°C)
- Low density (<700 kg/m³)
- High sulfur (>50 ppm)
- High moisture (>0.1%)
- Low octane (<85)

Question: {question}

Answer:"""
        
        try:
            response = self.bedrock.invoke_model(
                modelId='amazon.titan-text-express-v1',
                body=json.dumps({
                    'inputText': prompt,
                    'textGenerationConfig': {
                        'maxTokenCount': 400,
                        'temperature': 0.1
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            answer = result['results'][0]['outputText']
            print(f"Answer: {answer}")
            return answer
            
        except Exception as e:
            error_msg = f"Error querying Bedrock: {e}"
            print(error_msg)
            return error_msg

def main():
    print("=== Bedrock-Only RAG System ===")
    print("Working without OpenSearch - using local fuel data + Bedrock AI")
    
    rag = BedrockOnlyRAG()
    
    test_questions = [
        "What indicates contaminated fuel?",
        "What are normal temperature ranges for fuel?",
        "How does high sulfur content affect fuel quality?",
        "What density values suggest fuel contamination?",
        "Is a temperature of 45°C normal for fuel?",
        "What should I do if moisture content is 0.25%?"
    ]
    
    print(f"\n{'='*60}")
    for question in test_questions:
        rag.ask(question)
        print(f"{'='*60}")
    
    print("\n=== Interactive Mode ===")
    print("Ask your own fuel quality questions (type 'quit' to exit):")
    
    while True:
        user_question = input("\nYour question: ").strip()
        if user_question.lower() in ['quit', 'exit', 'q']:
            break
        if user_question:
            rag.ask(user_question)

if __name__ == "__main__":
    main()