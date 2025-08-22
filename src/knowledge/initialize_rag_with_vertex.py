#!/usr/bin/env python3
"""
Initialize RAG system with real Vertex AI credentials from .env file
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.initialize_rag import RAGInitializer

async def main():
    """Initialize RAG with Vertex AI"""
    print("=" * 60)
    print("Initializing RAG System with Vertex AI")
    print("=" * 60)
    
    # Configure with environment variables
    config = {
        'project_id': os.environ.get('GOOGLE_CLOUD_PROJECT', 'mgm-digitalconcierge'),
        'region': os.environ.get('VERTEX_AI_LOCATION', 'us-central1'),
        'vector_store': {
            'store_type': 'faiss',
            'dimension': 768,  # text-embedding-004 dimension
            'faiss_index_type': 'IVF',
            'persist_path': str(Path(__file__).parent / 'data' / 'vector_store_vertex')
        },
        'vertex_ai': {
            'project_id': os.environ.get('GOOGLE_CLOUD_PROJECT', 'mgm-digitalconcierge'),
            'region': os.environ.get('VERTEX_AI_LOCATION', 'us-central1'),
            'embedding_model': os.environ.get('VERTEX_AI_EMBEDDING_MODEL', 'text-embedding-004'),
            'generation_model': os.environ.get('VERTEX_AI_MODEL', 'gemini-1.5-pro')
        }
    }
    
    # Check if credentials file exists
    creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_file and Path(creds_file).exists():
        print(f"✅ Using credentials from: {creds_file}")
    else:
        print(f"⚠️  Credentials file not found: {creds_file}")
        print("   Will attempt to use default credentials")
    
    print(f"\nConfiguration:")
    print(f"  Project: {config['project_id']}")
    print(f"  Region: {config['region']}")
    print(f"  Embedding Model: {config['vertex_ai']['embedding_model']}")
    print(f"  Generation Model: {config['vertex_ai']['generation_model']}")
    
    # Create custom initializer with the config
    class VertexRAGInitializer(RAGInitializer):
        def load_config(self, config_path=None):
            return config
    
    # Initialize
    print("\n" + "-" * 40)
    print("1. Initializing RAG system...")
    initializer = VertexRAGInitializer()
    
    try:
        await initializer.initialize_system()
        print("✅ System initialized with Vertex AI")
        
        # Check if we need to reload data
        existing_store = Path(config['vector_store']['persist_path'] + '_primary_documents.pkl')
        
        if existing_store.exists():
            print("\n2. Loading existing vector store...")
            await initializer.load_vector_store()
            stats = initializer.get_statistics()
            if 'vector_store' in stats:
                doc_count = stats['vector_store']['primary_stats'].get('total_documents', 0)
                print(f"✅ Loaded {doc_count} documents from existing store")
                
                if doc_count == 0:
                    print("\n3. Re-loading data with Vertex AI embeddings...")
                    await initializer.load_initial_data()
                    await initializer.save_vector_store()
                    print("✅ Data loaded with real embeddings")
        else:
            print("\n2. Loading initial data with Vertex AI embeddings...")
            await initializer.load_initial_data()
            await initializer.save_vector_store()
            print("✅ Initial data loaded and saved")
        
        # Test with real queries
        print("\n4. Testing RAG system with Vertex AI...")
        print("-" * 40)
        
        from knowledge.rag_system import RAGQuery
        
        test_queries = [
            "How do I deploy a Python FastAPI application on Cloud Run?",
            "What are the key principles of the BMAD methodology?",
            "Explain the difference between Cloud SQL and Cloud Spanner"
        ]
        
        for i, query_text in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query_text}")
            
            query = RAGQuery(
                query=query_text,
                query_type="general",
                max_context_chunks=3,
                temperature=0.3
            )
            
            try:
                response = await initializer.rag_system.query(query)
                print(f"✅ Response received")
                print(f"   Confidence: {response.confidence:.2f}")
                print(f"   Sources: {len(response.sources)} documents")
                print(f"   Preview: {response.answer[:150]}...")
                
                if response.suggested_followups:
                    print(f"   Suggested follow-ups:")
                    for followup in response.suggested_followups[:2]:
                        print(f"     - {followup}")
                        
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Final statistics
        print("\n" + "=" * 60)
        print("RAG System Statistics")
        print("-" * 40)
        
        final_stats = initializer.get_statistics()
        if 'vector_store' in final_stats:
            vs_stats = final_stats['vector_store']['primary_stats']
            print(f"Documents: {vs_stats.get('total_documents', 0)}")
            print(f"Index Size: {vs_stats.get('index_size', 0)}")
            print(f"Dimension: {vs_stats.get('dimension', 0)}")
            print(f"Has FAISS: {vs_stats.get('has_faiss', False)}")
        
        if 'rag_system' in final_stats:
            rag_stats = final_stats['rag_system']['rag_system']
            print(f"Has Generation Model: {rag_stats.get('has_generation_model', False)}")
            print(f"Has Code Model: {rag_stats.get('has_code_model', False)}")
            print(f"Cache Size: {rag_stats.get('cache_size', 0)}")
        
        print("\n✅ RAG system is ready with Vertex AI!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nTroubleshooting:")
        print("1. Check that GOOGLE_APPLICATION_CREDENTIALS points to a valid service account key")
        print("2. Ensure the service account has Vertex AI permissions")
        print("3. Verify the project ID and region are correct")
        print("4. Check that Vertex AI API is enabled in your project")

if __name__ == "__main__":
    # Set up Google Cloud credentials
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        os.environ['GOOGLE_CLOUD_PROJECT'] = os.environ.get('GOOGLE_CLOUD_PROJECT', 'mgm-digitalconcierge')
    
    asyncio.run(main())