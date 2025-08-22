#!/usr/bin/env node
/**
 * Demo script for Operationalized RAG System
 * Shows knowledge-augmented agent responses with Scout integration
 */

const { AgentFactory, KnowledgeUI, ScoutUI } = require('../packages/cli/src/agents');
const path = require('path');

async function runRAGDemo() {
  console.log('🚀 Starting RAG System Demo\n');
  
  const factory = new AgentFactory({
    autoStartServer: true,
    enableScoutUI: true,
    processConfig: {
      serverPath: path.join(__dirname, '../src/start_server.py'),
      port: 8000
    }
  });

  try {
    // Initialize the factory (starts Python server and connects)
    console.log('Initializing RAG-enabled agent factory...');
    await factory.initialize({
      project: 'rag-demo',
      workingDirectory: process.cwd()
    });

    // Wait for server to fully start
    await new Promise(resolve => setTimeout(resolve, 8000));

    console.log('\n=== RAG System Demo ===\n');

    // 1. Test Knowledge Base Statistics
    console.log('1. Getting Knowledge Base Statistics...');
    await factory.getKnowledgeStats();

    // 2. Test Direct Knowledge Query
    console.log('\n2. Direct Knowledge Query...');
    await factory.queryKnowledge(
      'What are the best practices for deploying microservices on Google Cloud Platform?',
      {
        queryType: 'architecture',
        maxResults: 3,
        temperature: 0.2
      }
    );

    // 3. Test Knowledge Search
    console.log('\n3. Knowledge Document Search...');
    await factory.searchKnowledge('GKE autoscaling', {
      limit: 5,
      service: 'kubernetes'
    });

    // 4. Test Architect Agent with Knowledge Context
    console.log('\n4. Testing Architect Agent with Knowledge Context...');
    const architect = factory.architect();
    
    const architectResponse = await architect.design(
      'Design a scalable e-commerce platform on GCP that can handle 10,000 concurrent users',
      { budget: 'medium', region: 'us-central1' }
    );

    console.log('\n📋 Architect Response:');
    console.log('Success:', architectResponse.success);
    if (architectResponse.metadata?.knowledge_context) {
      console.log('Knowledge Context Applied:', architectResponse.metadata.knowledge_context.knowledge_enabled);
    }

    // 5. Test Developer Agent with Both Scout and Knowledge
    console.log('\n5. Testing Developer Agent with Scout + Knowledge...');
    const developer = factory.developer();
    
    const devResponse = await developer.generateCode(
      'Create a Kubernetes deployment for a Node.js microservice with auto-scaling',
      'yaml'
    );

    console.log('\n📋 Developer Response:');
    console.log('Success:', devResponse.success);
    if (devResponse.metadata) {
      console.log('Scout Results:', devResponse.metadata.scout_results?.scout_enabled);
      console.log('Knowledge Context:', devResponse.metadata.knowledge_context?.knowledge_enabled);
    }

    // 6. Test Query with Different Types
    console.log('\n6. Testing Different Query Types...');
    
    // Code-specific query
    console.log('\n6a. Code Query:');
    await factory.queryKnowledge(
      'Show me how to implement OAuth2 authentication in a Python Flask application',
      { queryType: 'code', temperature: 0.1 }
    );

    // Troubleshooting query
    console.log('\n6b. Troubleshooting Query:');
    await factory.queryKnowledge(
      'My GKE pods keep getting OOMKilled, how do I fix this?',
      { queryType: 'troubleshooting', maxResults: 4 }
    );

    // 7. Test Knowledge Context Bypass
    console.log('\n7. Testing Knowledge Bypass...');
    const bypassResponse = await developer.request('generate_code', {
      specification: 'Create a simple REST API',
      language: 'python'
    }, {
      bypassScout: false,
      bypassKnowledge: true  // This should be a new option
    });

    console.log('Bypass Response - Knowledge Context:', bypassResponse.metadata?.knowledge_context);

    // 8. Add Custom Document (if API key available)
    console.log('\n8. Adding Custom Document to Knowledge Base...');
    const docAdded = await factory.addKnowledgeDocument(
      'Custom GCP Best Practices',
      'Here are some custom best practices for GCP deployment: Always use managed services when possible, implement proper monitoring with Cloud Monitoring, use IAM roles following principle of least privilege.',
      {
        service: 'gcp',
        category: 'best-practices',
        url: 'https://example.com/custom-practices'
      }
    );

    if (docAdded) {
      console.log('✅ Document added successfully');
    } else {
      console.log('⚠️  Document addition requires API key');
    }

    // 9. Start Knowledge Browser (show interface)
    console.log('\n9. Knowledge Browser Interface...');
    await factory.startKnowledgeBrowser();

    // 10. Performance Comparison
    console.log('\n10. Performance Analysis...');
    const startTime = Date.now();
    
    await Promise.all([
      factory.queryKnowledge('What is Cloud Run?'),
      factory.queryKnowledge('How to optimize BigQuery costs?'),
      factory.queryKnowledge('GKE networking best practices?')
    ]);
    
    const endTime = Date.now();
    console.log(`⚡ Parallel knowledge queries completed in ${endTime - startTime}ms`);

    console.log('\n✅ RAG System Demo completed successfully!');
    console.log('\n🎯 Key Features Demonstrated:');
    console.log('   ✓ Direct knowledge base querying');
    console.log('   ✓ Document search with filtering');
    console.log('   ✓ Knowledge-augmented agent responses');
    console.log('   ✓ Scout-First + Knowledge integration');
    console.log('   ✓ Response caching and performance');
    console.log('   ✓ Multiple query types (general, code, architecture, troubleshooting)');
    console.log('   ✓ Knowledge context visualization');

  } catch (error) {
    console.error('❌ RAG Demo failed:', error);
  } finally {
    await factory.destroy();
  }
}

// Handle process signals
process.on('SIGINT', async () => {
  console.log('\n⏹️  Stopping RAG demo...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n⏹️  Stopping RAG demo...');
  process.exit(0);
});

// Run the demo
if (require.main === module) {
  runRAGDemo().catch(console.error);
}

module.exports = { runRAGDemo };