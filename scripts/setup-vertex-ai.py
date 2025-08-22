#!/usr/bin/env python3
"""
Vertex AI Setup Script for Gemini Enterprise Architect
Deploys embedding models and configures endpoints
"""

import os
import sys
import json
from pathlib import Path
from google.cloud import aiplatform
from google.oauth2 import service_account
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")

# Configuration from environment
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'mgm-digitalconcierge')
LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
SERVICE_ACCOUNT_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Model configurations
MODELS_TO_DEPLOY = {
    "text-embedding-004": {
        "model_name": "text-embedding-004",
        "endpoint_name": "gemini-embedding-endpoint",
        "machine_type": "n1-standard-2",
        "min_replica_count": 1,
        "max_replica_count": 3
    },
    "gemini-1.5-pro": {
        "model_name": "gemini-1.5-pro",
        "endpoint_name": "gemini-chat-endpoint", 
        "machine_type": "n1-standard-4",
        "min_replica_count": 1,
        "max_replica_count": 5
    }
}

def setup_vertex_ai_client():
    """Initialize Vertex AI client with service account"""
    print(f"🔧 Setting up Vertex AI client...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"   Service Account: {SERVICE_ACCOUNT_PATH}")
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)
        aiplatform.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    else:
        print("   Using default credentials")
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    print("✅ Vertex AI client initialized")
    return True

def list_available_models():
    """List available models in Vertex AI"""
    print("📋 Listing available models...")
    
    try:
        models = aiplatform.Model.list()
        print(f"   Found {len(models)} models:")
        for model in models[:10]:  # Show first 10
            print(f"   - {model.display_name} ({model.name})")
        return True
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False

def check_existing_endpoints():
    """Check for existing endpoints"""
    print("🔍 Checking existing endpoints...")
    
    try:
        endpoints = aiplatform.Endpoint.list()
        existing_endpoints = {}
        
        for endpoint in endpoints:
            print(f"   Found endpoint: {endpoint.display_name}")
            existing_endpoints[endpoint.display_name] = endpoint
            
        return existing_endpoints
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")
        return {}

def deploy_embedding_model():
    """Deploy text embedding model"""
    print("🚀 Deploying text embedding model...")
    
    try:
        # Check if embedding endpoint already exists
        existing_endpoints = check_existing_endpoints()
        embedding_endpoint_name = MODELS_TO_DEPLOY["text-embedding-004"]["endpoint_name"]
        
        if embedding_endpoint_name in existing_endpoints:
            print(f"✅ Embedding endpoint '{embedding_endpoint_name}' already exists")
            endpoint = existing_endpoints[embedding_endpoint_name]
        else:
            print(f"📦 Creating new embedding endpoint...")
            endpoint = aiplatform.Endpoint.create(
                display_name=embedding_endpoint_name,
                project=PROJECT_ID,
                location=LOCATION
            )
            print(f"✅ Created embedding endpoint: {endpoint.name}")
        
        # Save endpoint info for application use
        endpoint_info = {
            "embedding_endpoint_id": endpoint.name.split('/')[-1],
            "embedding_endpoint_name": endpoint.display_name,
            "project_id": PROJECT_ID,
            "location": LOCATION
        }
        
        # Save to file for application to use
        config_file = Path(__file__).parent.parent / "vertex-ai-config.json"
        with open(config_file, 'w') as f:
            json.dump(endpoint_info, f, indent=2)
        
        print(f"💾 Saved configuration to: {config_file}")
        return endpoint
        
    except Exception as e:
        print(f"❌ Error deploying embedding model: {e}")
        return None

def test_vertex_ai_connection():
    """Test connection to Vertex AI"""
    print("🧪 Testing Vertex AI connection...")
    
    try:
        # Try to list models as a connectivity test
        models = aiplatform.Model.list()
        print(f"✅ Connection successful - found {len(models)} models")
        
        # Test generating embeddings
        print("🧪 Testing text embedding...")
        from vertexai.language_models import TextEmbeddingModel
        
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = model.get_embeddings(["Hello world test"])
        
        if embeddings and len(embeddings) > 0:
            print(f"✅ Embedding test successful - got {len(embeddings[0].values)} dimensions")
            return True
        else:
            print("❌ Embedding test failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("💡 Make sure:")
        print("   1. Your service account has Vertex AI permissions")
        print("   2. Vertex AI API is enabled in your GCP project")
        print("   3. The service account JSON file is valid")
        return False

def setup_iam_permissions():
    """Display IAM permissions setup instructions"""
    print("🔐 Required IAM Permissions:")
    print("   Your service account needs these roles:")
    print("   - Vertex AI User (roles/aiplatform.user)")
    print("   - Vertex AI Developer (roles/aiplatform.developer)")
    print("   - Service Account Token Creator (roles/iam.serviceAccountTokenCreator)")
    print("")
    print("🛠️  To add these permissions:")
    print(f"   gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print("     --member='serviceAccount:YOUR_SERVICE_ACCOUNT@mgm-digitalconcierge.iam.gserviceaccount.com' \\")
    print("     --role='roles/aiplatform.user'")
    print("")
    print(f"   gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print("     --member='serviceAccount:YOUR_SERVICE_ACCOUNT@mgm-digitalconcierge.iam.gserviceaccount.com' \\")
    print("     --role='roles/aiplatform.developer'")

def enable_apis():
    """Display API enablement instructions"""
    print("🔌 Required APIs to enable:")
    print("   gcloud services enable aiplatform.googleapis.com")
    print("   gcloud services enable ml.googleapis.com")
    print("   gcloud services enable compute.googleapis.com")

def main():
    parser = argparse.ArgumentParser(description='Setup Vertex AI for Gemini Enterprise Architect')
    parser.add_argument('--test-only', action='store_true', help='Only test connection')
    parser.add_argument('--setup-iam', action='store_true', help='Show IAM setup instructions')
    parser.add_argument('--enable-apis', action='store_true', help='Show API enablement instructions')
    
    args = parser.parse_args()
    
    print("🚀 Gemini Enterprise Architect - Vertex AI Setup")
    print("=" * 60)
    
    if args.setup_iam:
        setup_iam_permissions()
        return
    
    if args.enable_apis:
        enable_apis()
        return
    
    # Check service account file
    if not SERVICE_ACCOUNT_PATH or not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"❌ Service account file not found: {SERVICE_ACCOUNT_PATH}")
        print("💡 Update GOOGLE_APPLICATION_CREDENTIALS in your .env file")
        sys.exit(1)
    
    # Setup client
    if not setup_vertex_ai_client():
        sys.exit(1)
    
    # Test connection
    if not test_vertex_ai_connection():
        print("\n🛠️  If you see permission errors, run:")
        print(f"   python {__file__} --setup-iam")
        print(f"   python {__file__} --enable-apis")
        sys.exit(1)
    
    if args.test_only:
        print("✅ Test completed successfully!")
        return
    
    # Deploy models
    print("\n🚀 Deploying models...")
    embedding_endpoint = deploy_embedding_model()
    
    if embedding_endpoint:
        print("\n🎉 Vertex AI setup completed successfully!")
        print("\n📋 Summary:")
        print(f"   Project: {PROJECT_ID}")
        print(f"   Location: {LOCATION}")
        print(f"   Embedding Endpoint: {embedding_endpoint.display_name}")
        print(f"   Configuration saved to: vertex-ai-config.json")
        print("\n✅ Your application can now use Vertex AI without API keys!")
    else:
        print("❌ Setup failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()