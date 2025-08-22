/**
 * Enhanced Test Data Management System
 * Comprehensive test data generation, management, and cleanup for integration tests
 */

import { randomBytes, randomUUID } from 'crypto';
import { promises as fs } from 'fs';
import * as path from 'path';

export interface TestDataConfig {
  baseDir: string;
  preserveData: boolean;
  maxFileSize: number;
  maxDataAge: number; // in milliseconds
  encryptSensitive: boolean;
}

export interface TestDataSet {
  id: string;
  name: string;
  description: string;
  category: 'workflow' | 'knowledge' | 'rag' | 'guardian' | 'performance';
  data: any;
  metadata: TestDataMetadata;
  dependencies?: string[];
}

export interface TestDataMetadata {
  created: Date;
  lastUsed: Date;
  useCount: number;
  size: number;
  checksums: Record<string, string>;
  tags: string[];
  sensitive: boolean;
}

export interface TestDataQuery {
  category?: string;
  tags?: string[];
  maxAge?: number;
  minSize?: number;
  maxSize?: number;
  sensitive?: boolean;
}

export class EnhancedTestDataManager {
  private config: TestDataConfig;
  private datasets: Map<string, TestDataSet> = new Map();
  private fixtures: Map<string, any> = new Map();
  private generators: Map<string, () => any> = new Map();
  private cleanupTasks: (() => Promise<void>)[] = [];

  constructor(config: TestDataConfig) {
    this.config = config;
    this.initializeGenerators();
  }

  /**
   * Initialize the test data manager
   */
  async initialize(): Promise<void> {
    await this.ensureDirectoryExists(this.config.baseDir);
    await this.loadExistingDatasets();
    await this.loadFixtures();
    await this.cleanupExpiredData();
  }

  /**
   * Initialize data generators
   */
  private initializeGenerators(): void {
    // User data generator
    this.generators.set('users', () => ({
      id: randomUUID(),
      name: this.generateName(),
      email: this.generateEmail(),
      role: this.randomChoice(['admin', 'user', 'guest', 'moderator']),
      created: new Date(),
      lastLogin: this.randomDate(),
      preferences: {
        theme: this.randomChoice(['light', 'dark', 'auto']),
        language: this.randomChoice(['en', 'es', 'fr', 'de']),
        notifications: Math.random() > 0.5
      }
    }));

    // Project data generator
    this.generators.set('projects', () => ({
      id: randomUUID(),
      name: this.generateProjectName(),
      description: this.generateDescription(),
      owner: randomUUID(),
      status: this.randomChoice(['active', 'inactive', 'archived', 'planning']),
      created: this.randomDate(),
      repository: {
        url: `https://github.com/testorg/${this.generateSlug()}.git`,
        branch: 'main',
        lastCommit: randomUUID().substring(0, 8)
      },
      technologies: this.randomChoices(['javascript', 'typescript', 'python', 'go', 'rust', 'java'], 2, 4),
      metrics: {
        linesOfCode: Math.floor(Math.random() * 100000) + 1000,
        contributors: Math.floor(Math.random() * 20) + 1,
        commits: Math.floor(Math.random() * 1000) + 100
      }
    }));

    // Code sample generator
    this.generators.set('code_samples', () => {
      const codeTypes = ['function', 'class', 'interface', 'component', 'service'];
      const codeType = this.randomChoice(codeTypes);
      
      return {
        id: randomUUID(),
        type: codeType,
        language: this.randomChoice(['typescript', 'javascript', 'python', 'java']),
        name: this.generateCodeName(codeType),
        content: this.generateCodeContent(codeType),
        complexity: this.randomChoice(['low', 'medium', 'high']),
        quality: Math.floor(Math.random() * 5) + 6, // 6-10 scale
        issues: this.generateCodeIssues(),
        dependencies: this.randomChoices(['react', 'lodash', 'axios', 'express', 'jest'], 0, 3)
      };
    });

    // Security test data generator
    this.generators.set('security_tests', () => ({
      id: randomUUID(),
      vulnerabilityType: this.randomChoice(['sql_injection', 'xss', 'csrf', 'path_traversal', 'insecure_direct_object_references']),
      severity: this.randomChoice(['low', 'medium', 'high', 'critical']),
      description: this.generateSecurityDescription(),
      affectedEndpoints: this.randomChoices(['/api/users', '/api/posts', '/api/admin', '/api/upload'], 1, 3),
      exploitCode: this.generateExploitCode(),
      remediation: this.generateRemediationSteps(),
      cvsScore: Math.random() * 10,
      discovered: this.randomDate(),
      status: this.randomChoice(['open', 'fixed', 'mitigated', 'accepted'])
    }));

    // Performance test data generator
    this.generators.set('performance_data', () => ({
      id: randomUUID(),
      testType: this.randomChoice(['load', 'stress', 'volume', 'spike', 'endurance']),
      endpoint: this.randomChoice(['/api/search', '/api/process', '/api/report', '/api/analytics']),
      metrics: {
        responseTime: Math.random() * 2000 + 50, // 50-2050ms
        throughput: Math.random() * 1000 + 100, // 100-1100 req/sec
        errorRate: Math.random() * 5, // 0-5%
        cpuUsage: Math.random() * 80 + 20, // 20-100%
        memoryUsage: Math.random() * 80 + 20 // 20-100%
      },
      testDuration: Math.floor(Math.random() * 3600) + 300, // 5min to 1hour
      concurrentUsers: Math.floor(Math.random() * 1000) + 10,
      passed: Math.random() > 0.2 // 80% pass rate
    }));

    // Knowledge base documents generator
    this.generators.set('knowledge_documents', () => ({
      id: randomUUID(),
      title: this.generateDocumentTitle(),
      content: this.generateDocumentContent(),
      type: this.randomChoice(['tutorial', 'reference', 'guide', 'api-doc', 'troubleshooting']),
      category: this.randomChoice(['frontend', 'backend', 'database', 'deployment', 'security']),
      tags: this.randomChoices(['javascript', 'react', 'node.js', 'docker', 'aws', 'testing'], 2, 5),
      author: this.generateName(),
      created: this.randomDate(),
      lastModified: this.randomDate(),
      version: `${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
      difficulty: this.randomChoice(['beginner', 'intermediate', 'advanced']),
      readTime: Math.floor(Math.random() * 30) + 5, // 5-35 minutes
      popularity: Math.random() * 100
    }));
  }

  /**
   * Generate test data for a specific category
   */
  generateTestData(category: string, count: number = 1): any[] {
    const generator = this.generators.get(category);
    if (!generator) {
      throw new Error(`No generator found for category: ${category}`);
    }

    const data = [];
    for (let i = 0; i < count; i++) {
      data.push(generator());
    }

    return data;
  }

  /**
   * Create and store a test dataset
   */
  async createDataset(
    name: string,
    category: 'workflow' | 'knowledge' | 'rag' | 'guardian' | 'performance',
    data: any,
    options: {
      description?: string;
      tags?: string[];
      sensitive?: boolean;
      dependencies?: string[];
    } = {}
  ): Promise<string> {
    const id = randomUUID();
    const dataset: TestDataSet = {
      id,
      name,
      description: options.description || `Test dataset for ${name}`,
      category,
      data,
      metadata: {
        created: new Date(),
        lastUsed: new Date(),
        useCount: 0,
        size: JSON.stringify(data).length,
        checksums: await this.calculateChecksums(data),
        tags: options.tags || [],
        sensitive: options.sensitive || false
      },
      dependencies: options.dependencies
    };

    this.datasets.set(id, dataset);
    
    if (!this.config.preserveData) {
      await this.persistDataset(dataset);
    }

    return id;
  }

  /**
   * Retrieve a test dataset
   */
  async getDataset(id: string): Promise<TestDataSet | null> {
    const dataset = this.datasets.get(id);
    if (!dataset) {
      return await this.loadDatasetFromDisk(id);
    }

    // Update usage statistics
    dataset.metadata.lastUsed = new Date();
    dataset.metadata.useCount++;

    return dataset;
  }

  /**
   * Query datasets by criteria
   */
  queryDatasets(query: TestDataQuery): TestDataSet[] {
    const datasets = Array.from(this.datasets.values());
    
    return datasets.filter(dataset => {
      // Category filter
      if (query.category && dataset.category !== query.category) {
        return false;
      }

      // Tags filter
      if (query.tags && query.tags.length > 0) {
        const hasMatchingTag = query.tags.some(tag => 
          dataset.metadata.tags.includes(tag)
        );
        if (!hasMatchingTag) return false;
      }

      // Age filter
      if (query.maxAge) {
        const age = Date.now() - dataset.metadata.created.getTime();
        if (age > query.maxAge) return false;
      }

      // Size filters
      if (query.minSize && dataset.metadata.size < query.minSize) {
        return false;
      }
      if (query.maxSize && dataset.metadata.size > query.maxSize) {
        return false;
      }

      // Sensitive data filter
      if (query.sensitive !== undefined && dataset.metadata.sensitive !== query.sensitive) {
        return false;
      }

      return true;
    });
  }

  /**
   * Create test fixture data
   */
  createFixture(name: string, data: any): void {
    this.fixtures.set(name, data);
  }

  /**
   * Get test fixture data
   */
  getFixture(name: string): any {
    return this.fixtures.get(name);
  }

  /**
   * Generate realistic test data for specific scenarios
   */
  generateScenarioData(scenario: string): any {
    switch (scenario) {
      case 'user-authentication-flow':
        return {
          users: this.generateTestData('users', 5),
          sessions: this.generateSessionData(5),
          authAttempts: this.generateAuthAttempts(20)
        };

      case 'code-analysis-workflow':
        return {
          codeFiles: this.generateTestData('code_samples', 15),
          dependencies: this.generateDependencyData(),
          metrics: this.generateCodeMetrics()
        };

      case 'security-audit-scenario':
        return {
          vulnerabilities: this.generateTestData('security_tests', 10),
          complianceChecks: this.generateComplianceData(),
          riskAssessment: this.generateRiskData()
        };

      case 'knowledge-base-population':
        return {
          documents: this.generateTestData('knowledge_documents', 50),
          categories: this.generateCategoryData(),
          searchQueries: this.generateSearchQueries()
        };

      case 'performance-testing-suite':
        return {
          benchmarks: this.generateTestData('performance_data', 20),
          loadProfiles: this.generateLoadProfiles(),
          environments: this.generateEnvironmentData()
        };

      default:
        throw new Error(`Unknown scenario: ${scenario}`);
    }
  }

  /**
   * Cleanup test data
   */
  async cleanup(): Promise<void> {
    // Execute cleanup tasks
    for (const task of this.cleanupTasks) {
      await task();
    }

    // Clear in-memory data
    this.datasets.clear();
    this.fixtures.clear();

    // Remove temporary files if not preserving data
    if (!this.config.preserveData) {
      await this.removeTemporaryFiles();
    }
  }

  /**
   * Helper methods for data generation
   */
  private generateName(): string {
    const firstNames = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'];
    const lastNames = ['Smith', 'Johnson', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor'];
    
    return `${this.randomChoice(firstNames)} ${this.randomChoice(lastNames)}`;
  }

  private generateEmail(): string {
    const domains = ['example.com', 'test.org', 'demo.net', 'sample.co'];
    const name = this.generateName().toLowerCase().replace(' ', '.');
    return `${name}@${this.randomChoice(domains)}`;
  }

  private generateProjectName(): string {
    const adjectives = ['Awesome', 'Super', 'Ultra', 'Mega', 'Advanced', 'Smart', 'Fast'];
    const nouns = ['Platform', 'System', 'Tool', 'Framework', 'Service', 'API', 'Dashboard'];
    
    return `${this.randomChoice(adjectives)} ${this.randomChoice(nouns)}`;
  }

  private generateDescription(): string {
    const templates = [
      'A comprehensive solution for modern development workflows',
      'Streamlined platform for enterprise-grade applications',
      'Innovative tool for enhanced productivity and collaboration',
      'Robust framework for scalable web applications',
      'Advanced system for automated testing and deployment'
    ];
    
    return this.randomChoice(templates);
  }

  private generateSlug(): string {
    return this.generateProjectName().toLowerCase().replace(/\s+/g, '-');
  }

  private generateCodeName(type: string): string {
    const prefixes = {
      function: ['calculate', 'process', 'validate', 'transform', 'generate'],
      class: ['User', 'Project', 'Service', 'Manager', 'Controller'],
      interface: ['IUser', 'IProject', 'IService', 'IManager', 'IController'],
      component: ['Button', 'Modal', 'Form', 'List', 'Card'],
      service: ['AuthService', 'DataService', 'ApiService', 'CacheService', 'LogService']
    };
    
    const suffix = type === 'function' ? this.randomChoice(['Data', 'Input', 'Result', 'Request', 'Response']) : '';
    return `${this.randomChoice(prefixes[type] || prefixes.function)}${suffix}`;
  }

  private generateCodeContent(type: string): string {
    const templates = {
      function: `function ${this.generateCodeName('function')}(input: any): any {
  // Implementation here
  return processedResult;
}`,
      class: `class ${this.generateCodeName('class')} {
  private data: any;
  
  constructor(data: any) {
    this.data = data;
  }
  
  public process(): any {
    return this.data;
  }
}`,
      interface: `interface ${this.generateCodeName('interface')} {
  id: string;
  name: string;
  process(): void;
}`,
      component: `const ${this.generateCodeName('component')} = ({ children }: Props) => {
  return <div>{children}</div>;
};`,
      service: `class ${this.generateCodeName('service')} {
  async execute(): Promise<any> {
    return await this.processRequest();
  }
}`
    };
    
    return templates[type] || templates.function;
  }

  private generateCodeIssues(): string[] {
    const issues = [
      'Missing error handling',
      'No input validation',
      'Performance bottleneck',
      'Memory leak potential',
      'Security vulnerability',
      'Code duplication',
      'Unused variables',
      'Complex cyclomatic complexity'
    ];
    
    return this.randomChoices(issues, 0, 3);
  }

  private generateSecurityDescription(): string {
    const descriptions = [
      'SQL injection vulnerability in user input processing',
      'Cross-site scripting (XSS) in comment rendering',
      'Cross-site request forgery (CSRF) token missing',
      'Path traversal vulnerability in file upload',
      'Insecure direct object reference in API endpoint'
    ];
    
    return this.randomChoice(descriptions);
  }

  private generateExploitCode(): string {
    return 'SELECT * FROM users WHERE id = 1 OR 1=1; --';
  }

  private generateRemediationSteps(): string[] {
    return [
      'Use parameterized queries',
      'Implement input validation',
      'Add rate limiting',
      'Update dependencies',
      'Enable security headers'
    ];
  }

  private generateDocumentTitle(): string {
    const templates = [
      'Getting Started with {technology}',
      'Advanced {technology} Techniques',
      '{technology} Best Practices Guide',
      'Troubleshooting {technology} Issues',
      '{technology} API Reference'
    ];
    
    const technologies = ['React', 'Node.js', 'Docker', 'AWS', 'GraphQL', 'TypeScript'];
    const template = this.randomChoice(templates);
    const technology = this.randomChoice(technologies);
    
    return template.replace('{technology}', technology);
  }

  private generateDocumentContent(): string {
    return `
# Introduction

This document provides comprehensive guidance on the topic.

## Overview

Key concepts and principles are covered in detail.

## Implementation

Step-by-step instructions for implementation.

## Best Practices

Recommended approaches and patterns.

## Troubleshooting

Common issues and solutions.
    `.trim();
  }

  private randomChoice<T>(items: T[]): T {
    return items[Math.floor(Math.random() * items.length)];
  }

  private randomChoices<T>(items: T[], min: number, max: number): T[] {
    const count = Math.floor(Math.random() * (max - min + 1)) + min;
    const shuffled = [...items].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
  }

  private randomDate(maxDaysAgo: number = 365): Date {
    const daysAgo = Math.floor(Math.random() * maxDaysAgo);
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return date;
  }

  // Additional helper methods for specialized data generation
  private generateSessionData(count: number): any[] {
    return Array.from({ length: count }, () => ({
      id: randomUUID(),
      userId: randomUUID(),
      token: randomBytes(32).toString('hex'),
      created: this.randomDate(7),
      expires: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      ipAddress: `192.168.1.${Math.floor(Math.random() * 255)}`,
      userAgent: 'Mozilla/5.0 (Test Browser)'
    }));
  }

  private generateAuthAttempts(count: number): any[] {
    return Array.from({ length: count }, () => ({
      id: randomUUID(),
      email: this.generateEmail(),
      success: Math.random() > 0.3, // 70% success rate
      timestamp: this.randomDate(30),
      ipAddress: `192.168.1.${Math.floor(Math.random() * 255)}`,
      method: this.randomChoice(['password', 'oauth', 'sso'])
    }));
  }

  private generateDependencyData(): any[] {
    const dependencies = ['react', 'lodash', 'axios', 'express', 'jest', 'webpack', 'babel'];
    return dependencies.map(name => ({
      name,
      version: `${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
      type: this.randomChoice(['production', 'development']),
      vulnerabilities: Math.floor(Math.random() * 3)
    }));
  }

  private generateCodeMetrics(): any {
    return {
      linesOfCode: Math.floor(Math.random() * 10000) + 1000,
      cyclomaticComplexity: Math.floor(Math.random() * 20) + 1,
      testCoverage: Math.random() * 100,
      maintainabilityIndex: Math.random() * 100,
      duplicateLines: Math.floor(Math.random() * 100),
      codeSmells: Math.floor(Math.random() * 10)
    };
  }

  private generateComplianceData(): any[] {
    const standards = ['OWASP', 'PCI-DSS', 'GDPR', 'SOX', 'HIPAA'];
    return standards.map(standard => ({
      standard,
      score: Math.random() * 100,
      issues: Math.floor(Math.random() * 5),
      lastAudit: this.randomDate(90)
    }));
  }

  private generateRiskData(): any {
    return {
      overallRisk: this.randomChoice(['low', 'medium', 'high', 'critical']),
      categories: {
        security: Math.random() * 10,
        compliance: Math.random() * 10,
        operational: Math.random() * 10,
        financial: Math.random() * 10
      },
      trends: {
        improving: Math.random() > 0.5,
        changePct: (Math.random() - 0.5) * 20 // -10% to +10%
      }
    };
  }

  private generateCategoryData(): any[] {
    const categories = ['Frontend', 'Backend', 'Database', 'DevOps', 'Security', 'Testing'];
    return categories.map(name => ({
      name,
      documentCount: Math.floor(Math.random() * 50) + 10,
      lastUpdated: this.randomDate(30)
    }));
  }

  private generateSearchQueries(): string[] {
    return [
      'how to implement authentication',
      'best practices for API design',
      'database optimization techniques',
      'react component patterns',
      'docker deployment guide',
      'security vulnerability scanning',
      'performance testing strategies',
      'CI/CD pipeline setup'
    ];
  }

  private generateLoadProfiles(): any[] {
    return [
      {
        name: 'Normal Load',
        concurrentUsers: 100,
        duration: 300, // 5 minutes
        rampUp: 60 // 1 minute
      },
      {
        name: 'Peak Load',
        concurrentUsers: 500,
        duration: 600, // 10 minutes
        rampUp: 120 // 2 minutes
      },
      {
        name: 'Stress Test',
        concurrentUsers: 1000,
        duration: 900, // 15 minutes
        rampUp: 180 // 3 minutes
      }
    ];
  }

  private generateEnvironmentData(): any[] {
    return [
      {
        name: 'development',
        resources: { cpu: '2 cores', memory: '4GB', storage: '50GB' }
      },
      {
        name: 'staging',
        resources: { cpu: '4 cores', memory: '8GB', storage: '100GB' }
      },
      {
        name: 'production',
        resources: { cpu: '8 cores', memory: '16GB', storage: '500GB' }
      }
    ];
  }

  /**
   * Persistence and file management methods
   */
  private async ensureDirectoryExists(dir: string): Promise<void> {
    try {
      await fs.access(dir);
    } catch {
      await fs.mkdir(dir, { recursive: true });
    }
  }

  private async loadExistingDatasets(): Promise<void> {
    try {
      const files = await fs.readdir(this.config.baseDir);
      const datasetFiles = files.filter(f => f.endsWith('.dataset.json'));
      
      for (const file of datasetFiles) {
        const filePath = path.join(this.config.baseDir, file);
        const content = await fs.readFile(filePath, 'utf-8');
        const dataset: TestDataSet = JSON.parse(content);
        this.datasets.set(dataset.id, dataset);
      }
    } catch (error) {
      // Directory doesn't exist or is empty
    }
  }

  private async loadFixtures(): Promise<void> {
    // Load basic fixtures
    this.fixtures.set('api_endpoints', [
      '/api/users',
      '/api/projects',
      '/api/auth/login',
      '/api/auth/logout',
      '/api/search'
    ]);

    this.fixtures.set('http_methods', ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']);

    this.fixtures.set('status_codes', [200, 201, 400, 401, 403, 404, 500]);

    this.fixtures.set('content_types', [
      'application/json',
      'text/html',
      'text/plain',
      'application/xml'
    ]);
  }

  private async persistDataset(dataset: TestDataSet): Promise<void> {
    const filePath = path.join(this.config.baseDir, `${dataset.id}.dataset.json`);
    await fs.writeFile(filePath, JSON.stringify(dataset, null, 2));
  }

  private async loadDatasetFromDisk(id: string): Promise<TestDataSet | null> {
    try {
      const filePath = path.join(this.config.baseDir, `${id}.dataset.json`);
      const content = await fs.readFile(filePath, 'utf-8');
      const dataset: TestDataSet = JSON.parse(content);
      this.datasets.set(id, dataset);
      return dataset;
    } catch {
      return null;
    }
  }

  private async calculateChecksums(data: any): Promise<Record<string, string>> {
    const crypto = await import('crypto');
    const content = JSON.stringify(data);
    
    return {
      md5: crypto.createHash('md5').update(content).digest('hex'),
      sha256: crypto.createHash('sha256').update(content).digest('hex')
    };
  }

  private async cleanupExpiredData(): Promise<void> {
    const now = Date.now();
    const expiredDatasets = Array.from(this.datasets.entries()).filter(
      ([_, dataset]) => now - dataset.metadata.created.getTime() > this.config.maxDataAge
    );

    for (const [id, _] of expiredDatasets) {
      this.datasets.delete(id);
      const filePath = path.join(this.config.baseDir, `${id}.dataset.json`);
      try {
        await fs.unlink(filePath);
      } catch {
        // File might not exist
      }
    }
  }

  private async removeTemporaryFiles(): Promise<void> {
    try {
      const files = await fs.readdir(this.config.baseDir);
      for (const file of files) {
        if (file.endsWith('.dataset.json') || file.endsWith('.temp')) {
          await fs.unlink(path.join(this.config.baseDir, file));
        }
      }
    } catch {
      // Directory might not exist
    }
  }
}

export default EnhancedTestDataManager;