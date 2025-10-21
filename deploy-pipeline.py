import boto3
import time

def deploy_pipeline():
    cf = boto3.client('cloudformation', region_name='us-east-1')
    
    try:
        print("Deploying data pipeline...")
        
        with open('data-pipeline.yaml', 'r') as f:
            template = f.read()
        
        cf.create_stack(
            StackName='fuel-quality-pipeline',
            TemplateBody=template,
            Capabilities=['CAPABILITY_IAM']
        )
        
        print("Stack creation initiated. Waiting for completion...")
        
        waiter = cf.get_waiter('stack_create_complete')
        waiter.wait(StackName='fuel-quality-pipeline')
        
        print("✅ Pipeline deployed successfully!")
        
        # Get outputs
        response = cf.describe_stacks(StackName='fuel-quality-pipeline')
        outputs = response['Stacks'][0].get('Outputs', [])
        
        for output in outputs:
            print(f"{output['OutputKey']}: {output['OutputValue']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    deploy_pipeline()