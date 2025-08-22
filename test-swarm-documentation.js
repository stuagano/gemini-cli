#!/usr/bin/env node
/**
 * Test script for SwarmDocumentationService
 * This demonstrates the enhanced review board documentation with swarm integration
 */

import { SwarmDocumentationService } from './packages/cli/dist/src/services/SwarmDocumentationService.js';
import fs from 'fs';
import path from 'path';

// Mock config object for testing
const mockConfig = {
  // Add minimal config properties needed
};

async function testSwarmDocumentation() {
  console.log('🚀 Testing SwarmDocumentationService...');
  
  try {
    // Initialize the service
    const service = new SwarmDocumentationService(mockConfig, './test-output');
    
    // Create test output directory
    if (!fs.existsSync('./test-output')) {
      fs.mkdirSync('./test-output', { recursive: true });
    }
    
    // Define test requirements
    const requirements = {
      projectName: 'Enterprise AI Platform',
      projectType: 'enterprise',
      businessDomain: 'Financial Technology',
      technicalScope: 'full-stack',
      securityLevel: 'high',
      complianceRequirements: ['SOC 2', 'PCI DSS', 'GDPR'],
      stakeholders: {
        business: ['Chief Technology Officer', 'Product Manager', 'Business Analyst'],
        technical: ['Solution Architect', 'Lead Developer', 'DevOps Engineer'],
        external: ['Security Auditor', 'Compliance Officer', 'Third-party Integrator']
      },
      timeline: {
        duration: '16 weeks',
        phases: [
          { name: 'Discovery & Requirements', duration: '3 weeks' },
          { name: 'Architecture & Design', duration: '4 weeks' },
          { name: 'Core Development', duration: '6 weeks' },
          { name: 'Integration & Testing', duration: '2 weeks' },
          { name: 'Deployment & Go-Live', duration: '1 week' }
        ]
      }
    };
    
    console.log(`📋 Generating documentation for: ${requirements.projectName}`);
    console.log(`   Project Type: ${requirements.projectType}`);
    console.log(`   Business Domain: ${requirements.businessDomain}`);
    console.log(`   Security Level: ${requirements.securityLevel}`);
    
    // Generate documentation (using sequential mode for testing)
    const result = await service.generateReviewBoardDocumentation(
      requirements,
      {
        useSwarm: false, // Use sequential mode for testing
        validationLevel: 'comprehensive',
        outputPath: './test-output/test-review-board-documentation.md'
      }
    );
    
    console.log('✅ Documentation generated successfully!');
    console.log(`📄 Document path: ${result.documentPath}`);
    console.log(`📊 Sections generated: ${result.sections.length}`);
    console.log(`🤖 Agents used: ${result.metadata.agentsUsed.join(', ')}`);
    console.log(`⏱️ Generation time: ${result.metadata.generationTime}ms`);
    console.log(`🔍 Validation results: ${result.validationResults.length} reports`);
    
    // Display validation summary
    if (result.validationResults.length > 0) {
      console.log('\n📋 Validation Summary:');
      result.validationResults.forEach(validation => {
        console.log(`   ${validation.section}: ${validation.isValid ? '✅ Valid' : '❌ Issues'} (${(validation.confidence * 100).toFixed(1)}% confidence)`);
        if (validation.issues.length > 0) {
          console.log(`     Issues: ${validation.issues.length}`);
          validation.issues.forEach(issue => {
            console.log(`       • ${issue.message} (${issue.severity})`);
          });
        }
      });
    }
    
    // Show document preview
    console.log('\n📖 Document Preview:');
    const documentContent = fs.readFileSync(result.documentPath, 'utf8');
    const lines = documentContent.split('\n');
    const preview = lines.slice(0, 20).join('\n');
    console.log(preview);
    if (lines.length > 20) {
      console.log(`\n... and ${lines.length - 20} more lines`);
    }
    
    console.log('\n🎉 Test completed successfully!');
    console.log(`📁 Test output available in: ./test-output/`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run the test
testSwarmDocumentation().catch(error => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});