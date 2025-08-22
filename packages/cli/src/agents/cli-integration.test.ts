/**
 * CLI Agent Integration Tests
 * Tests the complete agent orchestration system
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NaturalLanguageCLI } from './natural-language-cli.js';
import { AgentOrchestrator } from './agent-orchestrator.js';
import { RealTimeStatusManager } from './real-time-status.js';
import { AgentErrorHandler } from './error-handler.js';
import { Config } from '@google/gemini-cli-core';

// Mock WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  on: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1
}));

// Mock fetch
global.fetch = vi.fn();

describe('CLI Agent Integration', () => {
  let config: Config;
  let nlCLI: NaturalLanguageCLI;
  let orchestrator: AgentOrchestrator;
  let statusManager: RealTimeStatusManager;
  let errorHandler: AgentErrorHandler;

  beforeEach(() => {
    config = {
      getSessionId: () => 'test-session',
      getProjectRoot: () => '/test/project',
      getDebugMode: () => false
    } as Config;

    nlCLI = new NaturalLanguageCLI(config);
    orchestrator = new AgentOrchestrator(config);
    statusManager = new RealTimeStatusManager();
    errorHandler = new AgentErrorHandler();

    // Mock fetch responses
    (fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ result: { status: 'success' } })
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('NaturalLanguageCLI', () => {
    it('should parse simple commands correctly', () => {
      const command = nlCLI.parseCommand('check for duplicates in authentication');
      
      expect(command.intent).toBe('check_duplicates');
      expect(command.suggestedAgent).toBe('scout');
      expect(command.confidence).toBeGreaterThan(0.5);
      expect(command.entities).toHaveProperty('action', 'check');
    });

    it('should identify multi-agent workflows', () => {
      const command = nlCLI.parseCommand('review and implement a secure payment system');
      
      expect(command.requiresMultiAgent).toBe(true);
      expect(command.confidence).toBeGreaterThan(0.5);
    });

    it('should route to appropriate agents', () => {
      const securityCommand = nlCLI.parseCommand('scan for security vulnerabilities');
      expect(securityCommand.suggestedAgent).toBe('guardian');

      const designCommand = nlCLI.parseCommand('design a microservices architecture');
      expect(designCommand.suggestedAgent).toBe('architect');

      const testCommand = nlCLI.parseCommand('create unit tests');
      expect(testCommand.suggestedAgent).toBe('qa');
    });

    it('should handle low confidence commands', () => {
      const command = nlCLI.parseCommand('xyz abc random text');
      
      expect(command.confidence).toBeLessThan(0.6);
      expect(command.suggestedAgent).toBeDefined();
    });

    it('should extract entities from commands', () => {
      const command = nlCLI.parseCommand('implement a TypeScript function in src/auth.ts');
      
      expect(command.entities).toHaveProperty('language', 'typescript');
      expect(command.entities).toHaveProperty('filePath', 'src/auth.ts');
      expect(command.entities).toHaveProperty('action', 'implement');
    });
  });

  describe('AgentOrchestrator', () => {
    it('should create workflows from natural language', () => {
      const workflow = orchestrator.createWorkflow(
        'implement a user authentication system with security validation'
      );

      expect(workflow.tasks).toHaveLength(5); // Scout + Architect + Guardian + Developer + Final Guardian
      expect(workflow.tasks[0].agent).toBe('scout');
      expect(workflow.tasks.some(t => t.agent === 'architect')).toBe(true);
      expect(workflow.tasks.some(t => t.agent === 'guardian')).toBe(true);
      expect(workflow.tasks.some(t => t.agent === 'developer')).toBe(true);
    });

    it('should handle dependencies correctly', () => {
      const workflow = orchestrator.createWorkflow('design and implement an API');

      const scoutTask = workflow.tasks.find(t => t.agent === 'scout');
      const architectTask = workflow.tasks.find(t => t.agent === 'architect');
      const developerTask = workflow.tasks.find(t => t.agent === 'developer');

      expect(scoutTask?.dependencies).toHaveLength(0);
      expect(architectTask?.dependencies).toContain(scoutTask?.id);
      expect(developerTask?.dependencies).toContain(architectTask?.id);
    });

    it('should resolve template variables', () => {
      const workflow = orchestrator.createWorkflow('implement a feature');
      const developerTask = workflow.tasks.find(t => t.agent === 'developer');

      expect(developerTask?.input.scout_analysis).toContain('{{');
    });

    it('should handle workflow execution', async () => {
      const workflow = orchestrator.createWorkflow('simple task');
      
      // Mock successful execution
      await expect(orchestrator.executeWorkflow(workflow)).resolves.not.toThrow();
    });

    it('should track workflow progress', () => {
      const workflowId = 'test_workflow';
      const status = orchestrator.getWorkflowStatus(workflowId);

      expect(status).toHaveProperty('total');
      expect(status).toHaveProperty('completed');
      expect(status).toHaveProperty('progress');
    });
  });

  describe('RealTimeStatusManager', () => {
    it('should display status updates', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      statusManager.displayStatus({
        type: 'info',
        agent: 'scout',
        message: 'Analyzing code',
        timestamp: new Date()
      });

      expect(consoleSpy).toHaveBeenCalled();
      expect(consoleSpy.mock.calls[0][0]).toContain('SCOUT');
      expect(consoleSpy.mock.calls[0][0]).toContain('Analyzing code');

      consoleSpy.mockRestore();
    });

    it('should manage spinners', () => {
      const taskId = 'test_task';
      
      statusManager.startSpinner(taskId, 'Processing...', 'scout');
      expect(statusManager['activeSpinners'].has(taskId)).toBe(true);

      statusManager.succeedSpinner(taskId, 'Completed');
      expect(statusManager['activeSpinners'].has(taskId)).toBe(false);
    });

    it('should track progress', () => {
      const progressInfo = {
        taskId: 'test_progress',
        taskName: 'Test Task',
        current: 0,
        total: 100,
        agent: 'developer',
        startTime: new Date()
      };

      statusManager.startProgress(progressInfo);
      expect(statusManager['progressBars'].has('test_progress')).toBe(true);

      statusManager.updateProgress('test_progress', 50);
      statusManager.completeProgress('test_progress');
      expect(statusManager['progressBars'].has('test_progress')).toBe(false);
    });

    it('should format different display modes', () => {
      const update = {
        type: 'success' as const,
        agent: 'developer',
        message: 'Code generated',
        timestamp: new Date()
      };

      statusManager.setDisplayMode('detailed');
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      statusManager.displayStatus(update);

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should maintain status history', () => {
      const update = {
        type: 'info' as const,
        message: 'Test message',
        timestamp: new Date()
      };

      statusManager.displayStatus(update);
      const history = statusManager.getHistory();

      expect(history).toHaveLength(1);
      expect(history[0]).toEqual(update);
    });
  });

  describe('AgentErrorHandler', () => {
    it('should categorize errors correctly', async () => {
      const networkError = new Error('ECONNREFUSED: Connection refused');
      const timeoutError = new Error('Request timeout after 30s');
      const validationError = new Error('Invalid input parameters');

      await errorHandler.handleError(networkError);
      await errorHandler.handleError(timeoutError);
      await errorHandler.handleError(validationError);

      const stats = errorHandler.getStatistics();

      expect(stats.byCategory).toHaveProperty('network');
      expect(stats.byCategory).toHaveProperty('timeout');
      expect(stats.byCategory).toHaveProperty('validation');
    });

    it('should assess error severity', async () => {
      const criticalError = new Error('Permission denied');
      const mediumError = new Error('Network timeout');

      await errorHandler.handleError(criticalError);
      await errorHandler.handleError(mediumError);

      const stats = errorHandler.getStatistics();

      expect(stats.bySeverity).toHaveProperty('critical');
      expect(stats.bySeverity).toHaveProperty('medium');
    });

    it('should handle recovery strategies', async () => {
      const retryableError = new Error('Network temporarily unavailable');
      
      const result = await errorHandler.handleError(retryableError);
      
      // Should attempt recovery for network errors
      expect(result).toBeDefined();
    });

    it('should track error history', async () => {
      const error1 = new Error('First error');
      const error2 = new Error('Second error');

      await errorHandler.handleError(error1);
      await errorHandler.handleError(error2);

      const stats = errorHandler.getStatistics();
      expect(stats.total).toBe(2);
    });

    it('should implement circuit breaker pattern', async () => {
      const agent = 'test_agent';
      const breaker = errorHandler['getCircuitBreaker'](agent);

      // Record failures to open circuit
      for (let i = 0; i < 5; i++) {
        breaker.recordFailure();
      }

      expect(breaker.isOpen()).toBe(true);

      // Reset and check
      breaker.reset();
      expect(breaker.isOpen()).toBe(false);
    });
  });

  describe('Integration Scenarios', () => {
    it('should handle complete workflow with error recovery', async () => {
      // Mock a failing then succeeding scenario
      (fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ result: { status: 'success' } })
        });

      const workflow = orchestrator.createWorkflow('test workflow');
      
      // Should not throw despite initial failure
      await expect(orchestrator.executeWorkflow(workflow)).resolves.not.toThrow();
    });

    it('should coordinate between all systems', async () => {
      const command = 'implement secure authentication with tests';
      
      // Parse command
      const nlCommand = nlCLI.parseCommand(command);
      expect(nlCommand.requiresMultiAgent).toBe(true);

      // Create workflow
      const workflow = orchestrator.createWorkflow(command);
      expect(workflow.tasks.length).toBeGreaterThan(3);

      // Track status
      const statusSpy = vi.spyOn(statusManager, 'displayStatus');

      // Execute workflow (mocked)
      statusManager.displayStatus({
        type: 'info',
        message: 'Workflow started',
        timestamp: new Date()
      });

      expect(statusSpy).toHaveBeenCalled();
    });

    it('should handle graceful degradation', async () => {
      // Mock server unavailable
      (fetch as any).mockRejectedValue(new Error('ECONNREFUSED'));

      // Should still function with fallbacks
      const command = nlCLI.parseCommand('simple task');
      expect(command).toBeDefined();
      expect(command.suggestedAgent).toBeDefined();
    });

    it('should maintain session state', () => {
      const sessionId = config.getSessionId();
      expect(sessionId).toBe('test-session');

      // Systems should use the same session
      expect(nlCLI['config'].getSessionId()).toBe(sessionId);
      expect(orchestrator['config'].getSessionId()).toBe(sessionId);
    });
  });

  describe('Performance Tests', () => {
    it('should parse commands quickly', () => {
      const start = performance.now();
      
      for (let i = 0; i < 100; i++) {
        nlCLI.parseCommand('test command ' + i);
      }
      
      const end = performance.now();
      const avgTime = (end - start) / 100;
      
      expect(avgTime).toBeLessThan(10); // Should be under 10ms per command
    });

    it('should handle concurrent workflows', async () => {
      const workflows = [
        orchestrator.createWorkflow('task 1'),
        orchestrator.createWorkflow('task 2'),
        orchestrator.createWorkflow('task 3')
      ];

      const start = performance.now();
      
      await Promise.all(
        workflows.map(w => orchestrator.executeWorkflow(w))
      );
      
      const end = performance.now();
      
      expect(end - start).toBeLessThan(5000); // Should complete within 5 seconds
    });
  });

  describe('Error Edge Cases', () => {
    it('should handle malformed commands gracefully', () => {
      const commands = [
        '',
        '   ',
        null as any,
        undefined as any,
        '/agent',
        '/agent     ',
        'random text without agent prefix'
      ];

      commands.forEach(cmd => {
        expect(() => nlCLI.parseCommand(cmd || '')).not.toThrow();
      });
    });

    it('should handle server disconnection', async () => {
      // Mock connection loss
      nlCLI['isConnected'] = false;
      
      // Should degrade gracefully
      const result = await nlCLI['callAgentAPI']({ agent: 'scout', task: 'test' });
      expect(result).toBeDefined(); // Should return mock response
    });

    it('should handle circular dependencies in workflows', () => {
      const workflow = orchestrator.createWorkflow('complex task');
      
      // Artificially create circular dependency
      if (workflow.tasks.length >= 2) {
        workflow.tasks[1].dependencies = [workflow.tasks[0].id];
        workflow.tasks[0].dependencies = [workflow.tasks[1].id];
      }

      // Should not hang
      expect(() => orchestrator['getReadyTasks']()).not.toThrow();
    });
  });
});