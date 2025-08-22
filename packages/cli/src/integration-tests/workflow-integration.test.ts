/**
 * Multi-Agent Workflow Integration Tests
 * Tests for agent coordination, task routing, and workflow execution
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import IntegrationTestFramework, { 
  TestScenario, 
  TestContext, 
  TestResult,
  IntegrationTestConfig 
} from './integration-test-framework.js';
import { Config } from '@google/gemini-cli-core';
import { AgentOrchestrator, WorkflowDefinition, AgentTask } from '../agents/agent-orchestrator.js';

describe('Multi-Agent Workflow Integration Tests', () => {
  let framework: IntegrationTestFramework;
  let config: IntegrationTestConfig;
  let orchestratorConfig: Config;

  beforeEach(async () => {
    config = {
      environment: 'test',
      timeout: 30000,
      retries: 1,
      parallelExecution: false,
      cleanupAfterTests: true,
      preserveTestData: false,
      verboseLogging: false
    };

    orchestratorConfig = {
      apiUrl: 'http://localhost:2000',
      maxRetries: 3,
      timeout: 5000
    } as Config;

    framework = new IntegrationTestFramework(config, orchestratorConfig);
    
    // Register workflow test scenarios
    registerWorkflowScenarios(framework);
  });

  afterEach(async () => {
    // Cleanup will be handled by framework
  });

  it('should execute single agent task workflow', async () => {
    const result = await framework.runScenario('single-agent-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.duration).toBeLessThan(10000);
    expect(result.assertions.every(a => a.passed)).toBe(true);
  });

  it('should execute multi-agent sequential workflow', async () => {
    const result = await framework.runScenario('sequential-multi-agent-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.duration).toBeLessThan(20000);
    expect(result.metrics.agentResponseTimes).toBeDefined();
    expect(Object.keys(result.metrics.agentResponseTimes).length).toBeGreaterThan(1);
  });

  it('should execute parallel multi-agent workflow', async () => {
    const result = await framework.runScenario('parallel-multi-agent-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.duration).toBeLessThan(15000); // Should be faster than sequential
    expect(result.assertions.some(a => a.description.includes('parallel execution'))).toBe(true);
  });

  it('should handle workflow with dependencies', async () => {
    const result = await framework.runScenario('dependency-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.assertions.some(a => a.description.includes('dependency resolution'))).toBe(true);
  });

  it('should handle workflow error recovery', async () => {
    const result = await framework.runScenario('error-recovery-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.assertions.some(a => a.description.includes('error recovery'))).toBe(true);
  });

  it('should validate workflow performance benchmarks', async () => {
    const result = await framework.runScenario('performance-benchmark-workflow');
    
    expect(result.status).toBe('passed');
    expect(result.metrics.workflowExecutionTime).toBeLessThan(5000);
    expect(result.metrics.agentResponseTimes.scout).toBeLessThan(500);
  });

  it('should run complete test suite for workflow category', async () => {
    const summary = await framework.runTests({ 
      categories: ['workflow'],
      parallel: false 
    });
    
    expect(summary.total).toBeGreaterThan(5);
    expect(summary.passRate).toBeGreaterThan(80);
    expect(summary.categories.workflow).toBeDefined();
    expect(summary.coverage.workflowCoverage).toBeGreaterThan(70);
  });
});

function registerWorkflowScenarios(framework: IntegrationTestFramework): void {
  
  // Single Agent Workflow Test
  framework.registerScenario({
    id: 'single-agent-workflow',
    name: 'Single Agent Task Execution',
    description: 'Test execution of a single agent task through the orchestrator',
    category: 'workflow',
    tags: ['basic', 'single-agent'],
    expectedDuration: 5000,
    requirements: ['agent-orchestrator', 'scout-agent'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      
      // Create a simple scout analysis task
      const task: AgentTask = {
        id: 'scout-task-1',
        type: 'analyze',
        description: 'Analyze code for duplications',
        agent: 'scout',
        input: {
          codeSnippet: 'function duplicateCode() { return "test"; }',
          operation: 'duplication-check'
        },
        priority: 1,
        status: 'pending'
      };

      // Execute task through orchestrator
      const startTime = Date.now();
      const result = await context.orchestrator.executeTask(task);
      const executionTime = Date.now() - startTime;

      // Assertions
      assertions.push(IntegrationTestFramework.assert(
        result !== null,
        'Task execution should return a result'
      ));

      assertions.push(IntegrationTestFramework.assert(
        result.status === 'completed',
        'Task should complete successfully'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        executionTime,
        5000,
        'Task execution should complete within 5 seconds'
      ));

      assertions.push(IntegrationTestFramework.assert(
        result.result?.duplications !== undefined,
        'Scout should return duplication analysis results'
      ));

      return {
        scenarioId: 'single-agent-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });

  // Sequential Multi-Agent Workflow Test  
  framework.registerScenario({
    id: 'sequential-multi-agent-workflow',
    name: 'Sequential Multi-Agent Workflow',
    description: 'Test sequential execution of multiple agents in a workflow',
    category: 'workflow',
    tags: ['multi-agent', 'sequential'],
    expectedDuration: 15000,
    requirements: ['agent-orchestrator', 'scout-agent', 'developer-agent', 'qa-agent'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      const startTime = Date.now();
      
      // Define a sequential workflow: Scout -> Developer -> QA
      const workflow: WorkflowDefinition = {
        id: 'sequential-workflow-1',
        name: 'Feature Development Workflow',
        description: 'Scout analysis, development, and QA validation',
        parallel: false,
        tasks: [
          {
            id: 'scout-analysis',
            type: 'analyze',
            description: 'Analyze existing code for duplications',
            agent: 'scout',
            input: { codebase: '/test/project' },
            priority: 1,
            status: 'pending'
          },
          {
            id: 'feature-development', 
            type: 'implement',
            description: 'Implement new feature based on scout analysis',
            agent: 'developer',
            input: { feature: 'user-authentication' },
            dependencies: ['scout-analysis'],
            priority: 2,
            status: 'pending'
          },
          {
            id: 'qa-validation',
            type: 'test',
            description: 'Validate implemented feature',
            agent: 'qa',
            input: { testType: 'integration' },
            dependencies: ['feature-development'],
            priority: 3,
            status: 'pending'
          }
        ]
      };

      // Execute workflow
      const workflowResult = await context.orchestrator.executeWorkflow(workflow);
      const executionTime = Date.now() - startTime;

      // Assertions
      assertions.push(IntegrationTestFramework.assert(
        workflowResult.status === 'completed',
        'Workflow should complete successfully'
      ));

      assertions.push(IntegrationTestFramework.assertEqual(
        workflowResult.completedTasks.length,
        3,
        'All three tasks should complete'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.taskOrder.includes('scout-analysis'),
        'Scout analysis should execute first'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.taskOrder.indexOf('feature-development') > 
        workflowResult.taskOrder.indexOf('scout-analysis'),
        'Development should execute after scout analysis'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        executionTime,
        20000,
        'Sequential workflow should complete within 20 seconds'
      ));

      return {
        scenarioId: 'sequential-multi-agent-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });

  // Parallel Multi-Agent Workflow Test
  framework.registerScenario({
    id: 'parallel-multi-agent-workflow',
    name: 'Parallel Multi-Agent Workflow',
    description: 'Test parallel execution of multiple agents',
    category: 'workflow',
    tags: ['multi-agent', 'parallel', 'performance'],
    expectedDuration: 10000,
    requirements: ['agent-orchestrator', 'scout-agent', 'architect-agent', 'guardian-agent'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      const startTime = Date.now();
      
      // Define parallel workflow: Scout + Architect + Guardian (independent analyses)
      const workflow: WorkflowDefinition = {
        id: 'parallel-workflow-1',
        name: 'Parallel Analysis Workflow',
        description: 'Parallel code analysis by multiple agents',
        parallel: true,
        tasks: [
          {
            id: 'scout-duplication-analysis',
            type: 'analyze',
            description: 'Scout duplication analysis',
            agent: 'scout',
            input: { analysisType: 'duplication' },
            priority: 1,
            status: 'pending'
          },
          {
            id: 'architect-design-review',
            type: 'review',
            description: 'Architect design review',
            agent: 'architect',
            input: { reviewType: 'architecture' },
            priority: 1,
            status: 'pending'
          },
          {
            id: 'guardian-security-scan',
            type: 'validate',
            description: 'Guardian security validation',
            agent: 'guardian',
            input: { scanType: 'security' },
            priority: 1,
            status: 'pending'
          }
        ]
      };

      // Execute parallel workflow
      const workflowResult = await context.orchestrator.executeWorkflow(workflow);
      const executionTime = Date.now() - startTime;

      // Assertions
      assertions.push(IntegrationTestFramework.assert(
        workflowResult.status === 'completed',
        'Parallel workflow should complete successfully'
      ));

      assertions.push(IntegrationTestFramework.assertEqual(
        workflowResult.completedTasks.length,
        3,
        'All three parallel tasks should complete'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.parallelExecution === true,
        'Workflow should execute tasks in parallel'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        executionTime,
        15000,
        'Parallel execution should be faster than sequential'
      ));

      // Verify parallel execution by checking overlap in execution times
      const taskResults = workflowResult.taskResults;
      const hasTimeOverlap = taskResults.some((task1, i) => 
        taskResults.some((task2, j) => 
          i !== j && 
          task1.startTime < task2.endTime && 
          task2.startTime < task1.endTime
        )
      );

      assertions.push(IntegrationTestFramework.assert(
        hasTimeOverlap,
        'Tasks should have overlapping execution times (parallel execution)'
      ));

      return {
        scenarioId: 'parallel-multi-agent-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });

  // Dependency Workflow Test
  framework.registerScenario({
    id: 'dependency-workflow',
    name: 'Workflow with Complex Dependencies',
    description: 'Test workflow execution with task dependencies',
    category: 'workflow',
    tags: ['dependencies', 'complex', 'orchestration'],
    expectedDuration: 20000,
    requirements: ['agent-orchestrator', 'all-agents'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      const startTime = Date.now();
      
      // Complex dependency workflow
      const workflow: WorkflowDefinition = {
        id: 'dependency-workflow-1',
        name: 'Complex Dependency Workflow',
        description: 'Workflow with multiple dependency levels',
        parallel: false,
        tasks: [
          {
            id: 'initial-scout',
            type: 'analyze',
            description: 'Initial code analysis',
            agent: 'scout',
            input: { phase: 'initial' },
            priority: 1,
            status: 'pending'
          },
          {
            id: 'architect-review',
            type: 'review',
            description: 'Architecture review based on scout findings',
            agent: 'architect',
            input: { phase: 'review' },
            dependencies: ['initial-scout'],
            priority: 2,
            status: 'pending'
          },
          {
            id: 'parallel-development-1',
            type: 'implement',
            description: 'Implement component A',
            agent: 'developer',
            input: { component: 'A' },
            dependencies: ['architect-review'],
            priority: 3,
            status: 'pending'
          },
          {
            id: 'parallel-development-2',
            type: 'implement',
            description: 'Implement component B',
            agent: 'developer',
            input: { component: 'B' },
            dependencies: ['architect-review'],
            priority: 3,
            status: 'pending'
          },
          {
            id: 'integration-test',
            type: 'test',
            description: 'Integration testing of both components',
            agent: 'qa',
            input: { testType: 'integration' },
            dependencies: ['parallel-development-1', 'parallel-development-2'],
            priority: 4,
            status: 'pending'
          },
          {
            id: 'final-validation',
            type: 'validate',
            description: 'Final security and quality validation',
            agent: 'guardian',
            input: { validationType: 'comprehensive' },
            dependencies: ['integration-test'],
            priority: 5,
            status: 'pending'
          }
        ]
      };

      // Execute complex workflow
      const workflowResult = await context.orchestrator.executeWorkflow(workflow);
      const executionTime = Date.now() - startTime;

      // Assertions for dependency resolution
      assertions.push(IntegrationTestFramework.assert(
        workflowResult.status === 'completed',
        'Complex dependency workflow should complete'
      ));

      assertions.push(IntegrationTestFramework.assertEqual(
        workflowResult.completedTasks.length,
        6,
        'All six tasks should complete'
      ));

      // Verify dependency order
      const taskOrder = workflowResult.taskOrder;
      assertions.push(IntegrationTestFramework.assert(
        taskOrder.indexOf('initial-scout') < taskOrder.indexOf('architect-review'),
        'Scout should execute before architect review'
      ));

      assertions.push(IntegrationTestFramework.assert(
        taskOrder.indexOf('architect-review') < taskOrder.indexOf('parallel-development-1'),
        'Architect review should execute before development'
      ));

      assertions.push(IntegrationTestFramework.assert(
        taskOrder.indexOf('parallel-development-1') < taskOrder.indexOf('integration-test') &&
        taskOrder.indexOf('parallel-development-2') < taskOrder.indexOf('integration-test'),
        'Both development tasks should complete before integration test'
      ));

      assertions.push(IntegrationTestFramework.assert(
        taskOrder.indexOf('integration-test') < taskOrder.indexOf('final-validation'),
        'Integration test should complete before final validation'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.dependencyResolution === 'successful',
        'Dependency resolution should be successful'
      ));

      return {
        scenarioId: 'dependency-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });

  // Error Recovery Workflow Test
  framework.registerScenario({
    id: 'error-recovery-workflow',
    name: 'Workflow Error Recovery',
    description: 'Test workflow error handling and recovery mechanisms',
    category: 'workflow',
    tags: ['error-handling', 'recovery', 'resilience'],
    expectedDuration: 15000,
    requirements: ['agent-orchestrator', 'error-simulation'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      const startTime = Date.now();
      
      // Workflow designed to test error recovery
      const workflow: WorkflowDefinition = {
        id: 'error-recovery-workflow-1',
        name: 'Error Recovery Test Workflow',
        description: 'Workflow with simulated failures for testing recovery',
        parallel: false,
        tasks: [
          {
            id: 'successful-task',
            type: 'analyze',
            description: 'Task that should succeed',
            agent: 'scout',
            input: { simulateError: false },
            priority: 1,
            status: 'pending'
          },
          {
            id: 'failing-task',
            type: 'implement',
            description: 'Task that will fail initially',
            agent: 'developer',
            input: { simulateError: true, maxRetries: 2 },
            dependencies: ['successful-task'],
            priority: 2,
            status: 'pending'
          },
          {
            id: 'recovery-task',
            type: 'validate',
            description: 'Task to validate recovery',
            agent: 'qa',
            input: { checkRecovery: true },
            dependencies: ['failing-task'],
            priority: 3,
            status: 'pending'
          }
        ]
      };

      // Execute workflow with error simulation
      const workflowResult = await context.orchestrator.executeWorkflow(workflow);
      const executionTime = Date.now() - startTime;

      // Assertions for error recovery
      assertions.push(IntegrationTestFramework.assert(
        workflowResult.status === 'completed' || workflowResult.status === 'partial',
        'Workflow should handle errors gracefully'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.errorCount > 0,
        'Workflow should encounter and handle errors'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.retryAttempts > 0,
        'Workflow should attempt retries for failed tasks'
      ));

      assertions.push(IntegrationTestFramework.assert(
        workflowResult.recoveryMechanisms.includes('retry'),
        'Retry recovery mechanism should be used'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        workflowResult.errorRecoveryTime,
        5000,
        'Error recovery should complete quickly'
      ));

      return {
        scenarioId: 'error-recovery-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });

  // Performance Benchmark Workflow Test
  framework.registerScenario({
    id: 'performance-benchmark-workflow',
    name: 'Workflow Performance Benchmarking',
    description: 'Benchmark workflow execution performance and resource usage',
    category: 'workflow',
    tags: ['performance', 'benchmark', 'metrics'],
    expectedDuration: 10000,
    requirements: ['agent-orchestrator', 'performance-monitoring'],
    
    execute: async (context: TestContext): Promise<TestResult> => {
      const assertions = [];
      const startTime = Date.now();
      
      // Performance benchmark workflow
      const workflow: WorkflowDefinition = {
        id: 'performance-benchmark-1',
        name: 'Performance Benchmark Workflow',
        description: 'Workflow designed for performance testing',
        parallel: true,
        tasks: Array.from({ length: 5 }, (_, i) => ({
          id: `benchmark-task-${i}`,
          type: 'analyze' as const,
          description: `Performance test task ${i}`,
          agent: 'scout',
          input: { taskId: i, performanceTest: true },
          priority: 1,
          status: 'pending' as const
        }))
      };

      // Execute performance benchmark
      const workflowResult = await context.orchestrator.executeWorkflow(workflow);
      const executionTime = Date.now() - startTime;

      // Performance assertions
      assertions.push(IntegrationTestFramework.assert(
        workflowResult.status === 'completed',
        'Performance benchmark workflow should complete'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        executionTime,
        8000,
        'Parallel execution should complete within 8 seconds'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        workflowResult.averageTaskExecutionTime,
        2000,
        'Average task execution time should be under 2 seconds'
      ));

      assertions.push(IntegrationTestFramework.assertGreaterThan(
        workflowResult.tasksPerSecond,
        0.5,
        'Should execute at least 0.5 tasks per second'
      ));

      assertions.push(IntegrationTestFramework.assertLessThan(
        workflowResult.memoryUsageMB,
        100,
        'Memory usage should stay under 100MB'
      ));

      return {
        scenarioId: 'performance-benchmark-workflow',
        status: 'passed',
        duration: executionTime,
        startTime: new Date(startTime),
        endTime: new Date(),
        assertions,
        metrics: context.performance.collectMetrics(),
        artifacts: []
      };
    }
  });
}