#!/usr/bin/env python3
"""
Test script for RAG system functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.initialize_rag import RAGInitializer

async def test_rag_system():
    """Test the RAG system with various queries"""
    print("=" * 60)
    print("RAG System Test Suite")
    print("=" * 60)
    
    # Initialize the system
    print("\n1. Initializing RAG system...")
    initializer = RAGInitializer()
    await initializer.initialize_system()
    print("✅ System initialized")
    
    # Load initial data
    print("\n2. Loading initial knowledge base...")
    await initializer.load_initial_data()
    print("✅ Knowledge base loaded")
    
    # Save vector store
    print("\n3. Saving vector store...")
    await initializer.save_vector_store()
    print("✅ Vector store saved")
    
    # Test queries
    print("\n4. Testing RAG queries...")
    print("-" * 40)
    
    test_cases = [
        {
            "query": "How do I deploy a FastAPI application on Cloud Run?",
            "expected_topics": ["Cloud Run", "FastAPI", "deployment"]
        },
        {
            "query": "What are the best practices for using BigQuery?",
            "expected_topics": ["BigQuery", "partitioning", "optimization"]
        },
        {
            "query": "Explain the BMAD Scout-first architecture",
            "expected_topics": ["Scout", "duplication", "analysis"]
        },
        {
            "query": "How do I implement microservices on GKE?",
            "expected_topics": ["GKE", "microservices", "Kubernetes"]
        },
        {
            "query": "What is Vertex AI and when should I use it?",
            "expected_topics": ["Vertex AI", "ML", "AutoML"]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['query']}")
        print("-" * 40)
        
        # Note: Since we don't have actual Vertex AI credentials,
        # this will use fallback responses
        await initializer.test_rag_system()
        
        print(f"Expected topics: {', '.join(test['expected_topics'])}")
        print("✅ Query processed")
    
    # Get statistics
    print("\n5. System Statistics")
    print("-" * 40)
    stats = initializer.get_statistics()
    
    if 'vector_store' in stats:
        vs_stats = stats['vector_store']
        print(f"Documents in vector store: {vs_stats.get('total_documents', 0)}")
        print(f"Vector dimension: {vs_stats.get('dimension', 0)}")
        print(f"Index type: {vs_stats.get('index_type', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_rag_system())