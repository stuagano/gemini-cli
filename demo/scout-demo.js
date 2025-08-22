#!/usr/bin/env node
/**
 * Demo script for Scout-First Architecture
 * Shows how Scout prevents code duplication and provides analysis
 */

const { AgentFactory, ScoutUI } = require('../packages/cli/src/agents');
const path = require('path');

async function runScoutDemo() {
  console.log('🚀 Starting Scout-First Architecture Demo\n');
  
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
    console.log('Initializing agent factory...');
    await factory.initialize({
      project: 'scout-demo',
      workingDirectory: process.cwd()
    });

    // Wait for server to fully start
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('\n1. Getting Scout statistics...');
    await factory.getScoutStats();

    console.log('\n2. Checking for duplicates...');
    await factory.getDuplicates(0.8);

    console.log('\n3. Testing Scout-First Architecture with code generation...');
    const developer = factory.developer();
    
    // This should trigger Scout pre-check
    const response = await developer.generateCode(
      'Create a function to validate user email addresses',
      'javascript'
    );

    console.log('\n📋 Generated Code Response:');
    console.log('Success:', response.success);
    if (response.metadata?.scout_results) {
      console.log('Scout Results:', JSON.stringify(response.metadata.scout_results, null, 2));
    }

    console.log('\n4. Testing with Scout bypass...');
    const bypassResponse = await developer.request('generate_code', {
      specification: 'Create another email validation function',
      language: 'javascript'
    }, {
      bypassScout: true
    });

    console.log('Bypass Response - Scout Results:', bypassResponse.metadata?.scout_results);

    console.log('\n5. Analyzing a specific file...');
    const serverFile = path.join(__dirname, '../src/api/agent_server.py');
    await factory.analyzeFile(serverFile);

    console.log('\n✅ Scout Demo completed successfully!');

  } catch (error) {
    console.error('❌ Demo failed:', error);
  } finally {
    await factory.destroy();
  }
}

// Handle process signals
process.on('SIGINT', async () => {
  console.log('\n⏹️  Stopping demo...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n⏹️  Stopping demo...');
  process.exit(0);
});

// Run the demo
if (require.main === module) {
  runScoutDemo().catch(console.error);
}

module.exports = { runScoutDemo };