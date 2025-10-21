import boto3
import json

def query_bedrock(question):
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Load fuel data if available
    try:
        with open('fuel_data_collected.json', 'r') as f:
            fuel_data = json.load(f)
        context = f"Based on {len(fuel_data)} fuel samples collected: "
        context += " ".join([sample.get('content', '') for sample in fuel_data[:3]])
    except:
        context = "No local fuel data available."
    
    prompt = f"""You are a fuel quality expert. Answer questions about fuel contamination and quality.

Context: {context}

Fuel Quality Standards:
- Normal temperature: 15-25°C (contaminated if >30°C)
- Normal density: 720-780 kg/m³ (contaminated if <700)
- Normal sulfur: 5-15 ppm (contaminated if >50)
- Normal moisture: 0.01-0.05% (contaminated if >0.1%)

Question: {question}

Answer:"""
    
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                'inputText': prompt,
                'textGenerationConfig': {'maxTokenCount': 300, 'temperature': 0.1}
            })
        )
        result = json.loads(response['body'].read())
        return result['results'][0]['outputText']
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 60)
    print("🛢️  FUEL QUALITY RAG SYSTEM")
    print("=" * 60)
    print("Ask questions about fuel quality and contamination")
    print("Examples:")
    print("- What indicates contaminated fuel?")
    print("- Is 45°C temperature normal?")
    print("- What causes high sulfur content?")
    print("\nType 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            question = input("\n🔍 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
                
            if not question:
                continue
                
            print("\n🤖 Thinking...")
            answer = query_bedrock(question)
            print(f"\n💡 Answer: {answer}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()