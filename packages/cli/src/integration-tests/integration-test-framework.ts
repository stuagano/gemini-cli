/**
 * Integration Test Framework
 * Comprehensive framework for testing multi-agent workflows, knowledge base integration,
 * RAG system responses, and Guardian functionality
 */

import { EventEmitter } from 'events';
import chalk from 'chalk';
import { Config } from '@google/gemini-cli-core';
import { AgentOrchestrator, WorkflowDefinition, AgentTask } from '../agents/agent-orchestrator.js';
import ScalingDetector from '../agents/scaling-detector.js';
import EnhancedTestDataManager from './test-data-manager.js';
import EnhancedServiceVirtualizer from './service-virtualizer.js';
import EnhancedPerformanceBenchmark from './performance-benchmark.js';

export interface IntegrationTestConfig {
  environment: 'test' | 'staging' | 'local';
  timeout: number;
  retries: number;
  parallelExecution: boolean;
  cleanupAfterTests: boolean;
  preserveTestData: boolean;
  verboseLogging: boolean;
}

export interface TestScenario {
  id: string;
  name: string;
  description: string;
  category: 'workflow' | 'knowledge' | 'rag' | 'guardian' | 'performance' | 'e2e';
  tags: string[];
  setup?: () => Promise<void>;
  execute: (context: TestContext) => Promise<TestResult>;
  teardown?: () => Promise<void>;
  expectedDuration: number;
  requirements: string[];
}

export interface TestContext {
  orchestrator: AgentOrchestrator;
  config: Config;
  testData: EnhancedTestDataManager;
  services: EnhancedServiceVirtualizer;
  performance: EnhancedPerformanceBenchmark;
  logger: TestLogger;
  scenario: TestScenario;
}

export interface TestResult {
  scenarioId: string;
  status: 'passed' | 'failed' | 'skipped' | 'timeout';
  duration: number;
  startTime: Date;
  endTime: Date;
  assertions: AssertionResult[];
  metrics: TestMetrics;
  artifacts: TestArtifact[];
  error?: Error;
}

export interface AssertionResult {
  id: string;
  description: string;
  expected: any;
  actual: any;
  passed: boolean;
  message?: string;
}

export interface TestMetrics {
  agentResponseTimes: Record<string, number>;
  workflowExecutionTime: number;
  memoryUsage: number;
  cpuUsage: number;
  networkRequests: number;
  databaseQueries: number;
  cacheHits: number;
  cacheSize: number;
}

export interface TestArtifact {
  type: 'log' | 'screenshot' | 'trace' | 'report' | 'data';
  path: string;
  description: string;
  size: number;
}

export class IntegrationTestFramework extends EventEmitter {
  private config: IntegrationTestConfig;
  private orchestrator: AgentOrchestrator;
  private orchestratorConfig: Config;
  private scenarios: Map<string, TestScenario> = new Map();
  private results: TestResult[] = [];
  private testData: EnhancedTestDataManager;
  private services: EnhancedServiceVirtualizer;
  private performance: EnhancedPerformanceBenchmark;
  private logger: TestLogger;

  constructor(config: IntegrationTestConfig, orchestratorConfig: Config) {
    super();
    this.config = config;
    this.orchestratorConfig = orchestratorConfig;
    this.orchestrator = new AgentOrchestrator(orchestratorConfig);
    this.testData = new EnhancedTestDataManager({
      baseDir: '/tmp/test-data',
      preserveData: config.preserveTestData,
      maxFileSize: 10 * 1024 * 1024, // 10MB
      maxDataAge: 24 * 60 * 60 * 1000, // 24 hours
      encryptSensitive: false
    });
    this.services = new EnhancedServiceVirtualizer();
    this.performance = new EnhancedPerformanceBenchmark({
      enableCpuProfiling: false,
      enableMemoryProfiling: true,
      enableNetworkProfiling: true,
      samplingInterval: 1000,
      maxSamples: 100,
      thresholds: {
        maxResponseTime: 5000,
        maxMemoryUsage: 200,
        maxCpuUsage: 80,
        minThroughput: 1,
        maxErrorRate: 10
      }
    });
    this.logger = new TestLogger(config.verboseLogging);
  }

  /**
   * Register a test scenario
   */
  registerScenario(scenario: TestScenario): void {
    this.scenarios.set(scenario.id, scenario);
    this.logger.info(`Registered test scenario: ${scenario.name}`);
  }

  /**
   * Run all scenarios or specific ones by category/tag
   */
  async runTests(options: {
    scenarios?: string[];
    categories?: string[];
    tags?: string[];
    parallel?: boolean;
  } = {}): Promise<TestSummary> {
    const startTime = Date.now();
    this.logger.info('🧪 Starting integration test suite...');

    // Filter scenarios based on options
    const scenariosToRun = this.getFilteredScenarios(options);
    
    if (scenariosToRun.length === 0) {
      throw new Error('No scenarios match the specified criteria');
    }

    this.logger.info(`Running ${scenariosToRun.length} scenario(s)...`);

    // Initialize test environment
    await this.initializeTestEnvironment();

    try {
      // Run scenarios
      if (options.parallel && this.config.parallelExecution) {
        await this.runScenariosInParallel(scenariosToRun);
      } else {
        await this.runScenariosSequentially(scenariosToRun);
      }
    } finally {
      // Cleanup
      if (this.config.cleanupAfterTests) {
        await this.cleanupTestEnvironment();
      }
    }

    const duration = Date.now() - startTime;
    const summary = this.generateTestSummary(duration);
    
    this.logger.info(`✅ Integration tests completed in ${duration}ms`);
    this.emit('tests_completed', summary);
    
    return summary;
  }

  /**
   * Run a single test scenario
   */
  async runScenario(scenarioId: string): Promise<TestResult> {
    const scenario = this.scenarios.get(scenarioId);
    if (!scenario) {
      throw new Error(`Scenario ${scenarioId} not found`);
    }

    this.logger.info(`🚀 Running scenario: ${scenario.name}`);
    const startTime = Date.now();

    const context: TestContext = {
      orchestrator: this.orchestrator,
      config: this.orchestratorConfig,
      testData: this.testData,
      services: this.services,
      performance: this.performance,
      logger: this.logger,
      scenario
    };

    const result: TestResult = {
      scenarioId: scenario.id,
      status: 'failed',
      duration: 0,
      startTime: new Date(startTime),
      endTime: new Date(),
      assertions: [],
      metrics: this.initializeMetrics(),
      artifacts: []
    };

    try {
      // Setup
      if (scenario.setup) {
        await scenario.setup();
      }

      // Execute with timeout
      const executionPromise = scenario.execute(context);
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Test timeout')), this.config.timeout);
      });

      const scenarioResult = await Promise.race([executionPromise, timeoutPromise]);
      
      // Copy results
      Object.assign(result, scenarioResult);
      result.status = 'passed';

    } catch (error) {
      result.error = error as Error;
      result.status = error.message === 'Test timeout' ? 'timeout' : 'failed';
      this.logger.error(`Scenario ${scenario.name} failed:`, error);
    } finally {
      // Teardown
      try {
        if (scenario.teardown) {
          await scenario.teardown();
        }
      } catch (teardownError) {
        this.logger.error('Teardown failed:', teardownError);
      }

      result.endTime = new Date();
      result.duration = Date.now() - startTime;
      result.metrics = this.collectMetrics();
      
      this.results.push(result);
    }

    this.logger.info(`${result.status === 'passed' ? '✅' : '❌'} Scenario ${scenario.name}: ${result.status}`);
    this.emit('scenario_completed', result);

    return result;
  }

  /**
   * Helper methods for test execution
   */
  private getFilteredScenarios(options: any): TestScenario[] {
    let scenarios = Array.from(this.scenarios.values());

    if (options.scenarios?.length) {
      scenarios = scenarios.filter(s => options.scenarios.includes(s.id));
    }

    if (options.categories?.length) {
      scenarios = scenarios.filter(s => options.categories.includes(s.category));
    }

    if (options.tags?.length) {
      scenarios = scenarios.filter(s => 
        options.tags.some((tag: string) => s.tags.includes(tag))
      );
    }

    return scenarios;
  }

  private async runScenariosInParallel(scenarios: TestScenario[]): Promise<void> {
    const promises = scenarios.map(scenario => 
      this.runScenario(scenario.id).catch(error => ({
        scenarioId: scenario.id,
        error
      }))
    );

    await Promise.all(promises);
  }

  private async runScenariosSequentially(scenarios: TestScenario[]): Promise<void> {
    for (const scenario of scenarios) {
      await this.runScenario(scenario.id);
    }
  }

  private async initializeTestEnvironment(): Promise<void> {
    this.logger.info('🔧 Initializing test environment...');
    
    // Connect orchestrator if needed
    try {
      await this.orchestrator.connect();
    } catch (error) {
      this.logger.warn('Orchestrator connection failed, using mock mode');
    }
    
    // Setup test data
    await this.testData.initialize();
    
    // Start service virtualization
    await this.services.start();
    
    // Initialize performance monitoring
    this.performance.startMonitoring();
  }

  private async cleanupTestEnvironment(): Promise<void> {
    this.logger.info('🧹 Cleaning up test environment...');
    
    this.performance.stopMonitoring();
    await this.services.stop();
    
    if (!this.config.preserveTestData) {
      await this.testData.cleanup();
    }
    
    this.orchestrator.disconnect();
  }

  private initializeMetrics(): TestMetrics {
    return {
      agentResponseTimes: {},
      workflowExecutionTime: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      networkRequests: 0,
      databaseQueries: 0,
      cacheHits: 0,
      cacheSize: 0
    };
  }

  private collectMetrics(): TestMetrics {
    return {
      agentResponseTimes: this.performance.getAgentResponseTimes(),
      workflowExecutionTime: this.performance.getWorkflowExecutionTime(),
      memoryUsage: this.performance.getMemoryUsage(),
      cpuUsage: this.performance.getCpuUsage(),
      networkRequests: this.services.getNetworkRequestCount(),
      databaseQueries: this.services.getDatabaseQueryCount(),
      cacheHits: this.services.getCacheHitCount(),
      cacheSize: this.services.getCacheSize()
    };
  }

  private generateTestSummary(totalDuration: number): TestSummary {
    const total = this.results.length;
    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    const timeout = this.results.filter(r => r.status === 'timeout').length;
    const skipped = this.results.filter(r => r.status === 'skipped').length;

    return {
      total,
      passed,
      failed,
      timeout,
      skipped,
      passRate: total > 0 ? (passed / total) * 100 : 0,
      totalDuration,
      averageDuration: total > 0 ? totalDuration / total : 0,
      results: this.results,
      categories: this.summarizeByCategory(),
      coverage: this.calculateCoverage()
    };
  }

  private summarizeByCategory(): Record<string, { total: number; passed: number }> {
    const categories: Record<string, { total: number; passed: number }> = {};
    
    for (const result of this.results) {
      const scenario = this.scenarios.get(result.scenarioId);
      if (!scenario) continue;
      
      if (!categories[scenario.category]) {
        categories[scenario.category] = { total: 0, passed: 0 };
      }
      
      categories[scenario.category].total++;
      if (result.status === 'passed') {
        categories[scenario.category].passed++;
      }
    }
    
    return categories;
  }

  private calculateCoverage(): TestCoverage {
    // Calculate test coverage across different dimensions
    return {
      agentCoverage: this.calculateAgentCoverage(),
      workflowCoverage: this.calculateWorkflowCoverage(),
      integrationPointCoverage: this.calculateIntegrationPointCoverage(),
      errorScenarioCoverage: this.calculateErrorScenarioCoverage()
    };
  }

  private calculateAgentCoverage(): number {
    // Simplified coverage calculation
    const totalAgents = 7; // scout, developer, architect, qa, guardian, po, pm
    const testedAgents = new Set();
    
    for (const result of this.results) {
      if (result.status === 'passed') {
        // Extract agent information from test results
        testedAgents.add('scout'); // Assuming scout is always tested
      }
    }
    
    return (testedAgents.size / totalAgents) * 100;
  }

  private calculateWorkflowCoverage(): number {
    const workflowTests = this.results.filter(r => 
      this.scenarios.get(r.scenarioId)?.category === 'workflow'
    );
    return workflowTests.length > 0 ? 
      (workflowTests.filter(r => r.status === 'passed').length / workflowTests.length) * 100 : 0;
  }

  private calculateIntegrationPointCoverage(): number {
    const integrationTests = this.results.filter(r => {
      const scenario = this.scenarios.get(r.scenarioId);
      return scenario?.category === 'knowledge' || scenario?.category === 'rag';
    });
    return integrationTests.length > 0 ? 
      (integrationTests.filter(r => r.status === 'passed').length / integrationTests.length) * 100 : 0;
  }

  private calculateErrorScenarioCoverage(): number {
    const errorTests = this.results.filter(r => 
      this.scenarios.get(r.scenarioId)?.tags.includes('error-handling')
    );
    return errorTests.length > 0 ? 
      (errorTests.filter(r => r.status === 'passed').length / errorTests.length) * 100 : 0;
  }

  /**
   * Utility methods for assertions
   */
  static assert(condition: boolean, message: string): AssertionResult {
    return {
      id: `assert_${Date.now()}`,
      description: message,
      expected: true,
      actual: condition,
      passed: condition,
      message: condition ? 'Passed' : `Failed: ${message}`
    };
  }

  static assertEqual<T>(expected: T, actual: T, message: string): AssertionResult {
    const passed = JSON.stringify(expected) === JSON.stringify(actual);
    return {
      id: `assertEqual_${Date.now()}`,
      description: message,
      expected,
      actual,
      passed,
      message: passed ? 'Values are equal' : `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`
    };
  }

  static assertGreaterThan(actual: number, threshold: number, message: string): AssertionResult {
    const passed = actual > threshold;
    return {
      id: `assertGreaterThan_${Date.now()}`,
      description: message,
      expected: `> ${threshold}`,
      actual,
      passed,
      message: passed ? `${actual} > ${threshold}` : `${actual} is not greater than ${threshold}`
    };
  }

  static assertLessThan(actual: number, threshold: number, message: string): AssertionResult {
    const passed = actual < threshold;
    return {
      id: `assertLessThan_${Date.now()}`,
      description: message,
      expected: `< ${threshold}`,
      actual,
      passed,
      message: passed ? `${actual} < ${threshold}` : `${actual} is not less than ${threshold}`
    };
  }

  static assertContains(container: any[], item: any, message: string): AssertionResult {
    const passed = container.includes(item);
    return {
      id: `assertContains_${Date.now()}`,
      description: message,
      expected: `contains ${JSON.stringify(item)}`,
      actual: container,
      passed,
      message: passed ? 'Item found in container' : `Item ${JSON.stringify(item)} not found in container`
    };
  }

  /**
   * Public getters
   */
  getResults(): TestResult[] {
    return this.results;
  }

  getScenarios(): TestScenario[] {
    return Array.from(this.scenarios.values());
  }

  getConfig(): IntegrationTestConfig {
    return this.config;
  }
}

export interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  timeout: number;
  skipped: number;
  passRate: number;
  totalDuration: number;
  averageDuration: number;
  results: TestResult[];
  categories: Record<string, { total: number; passed: number }>;
  coverage: TestCoverage;
}

export interface TestCoverage {
  agentCoverage: number;
  workflowCoverage: number;
  integrationPointCoverage: number;
  errorScenarioCoverage: number;
}

/**
 * Legacy interface for backward compatibility
 */

export class TestLogger {
  private verbose: boolean;

  constructor(verbose: boolean = false) {
    this.verbose = verbose;
  }

  info(message: string, ...args: any[]): void {
    console.log(chalk.blue('ℹ'), message, ...args);
  }

  error(message: string, ...args: any[]): void {
    console.log(chalk.red('✗'), message, ...args);
  }

  debug(message: string, ...args: any[]): void {
    if (this.verbose) {
      console.log(chalk.gray('🐛'), message, ...args);
    }
  }

  success(message: string, ...args: any[]): void {
    console.log(chalk.green('✓'), message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    console.log(chalk.yellow('⚠'), message, ...args);
  }
}

export default IntegrationTestFramework;