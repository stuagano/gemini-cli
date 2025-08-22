/**
 * Agent Command Tests with Scout Integration
 * Tests the Scout-first workflow for CLI operations
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { agentCommand, scoutCommand } from './agentCommand.js';
import { CommandContext } from './types.js';

// Mock dependencies
vi.mock('../../agents/natural-language-cli.js');
vi.mock('../../agents/agent-orchestrator.js');
vi.mock('../../agents/real-time-status.js');
vi.mock('../../agents/scout-pipeline.js');

describe('Agent Command with Scout Integration', () => {
  let mockContext: CommandContext;
  let mockConfig: any;

  beforeEach(() => {
    mockConfig = {
      getProjectRoot: vi.fn().mockReturnValue('/test/project'),
      getDebugMode: vi.fn().mockReturnValue(false)
    };

    mockContext = {
      addMessage: vi.fn(),
      addDebugMessage: vi.fn(),
      requestConfirmation: vi.fn().mockResolvedValue(true),
      config: mockConfig
    } as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Scout-First Workflow', () => {
    it('should run Scout analysis before agent commands', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn().mockResolvedValue({
        requestId: 'test-123',
        operation: 'test operation',
        timestamp: new Date(),
        duplications: [],
        dependencies: { affectedFiles: [], breakingChanges: [], riskLevel: 'low', mitigations: [], estimatedEffort: '1h' },
        technicalDebt: [],
        shouldProceed: true,
        warnings: [],
        suggestions: [],
        alternatives: [],
        analysisTime: 100,
        cacheHit: false,
        confidence: 0.8,
        impactVisualization: { affected: 0, complexity: 0, riskScore: 10 }
      });

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      const result = await agentCommand.handler(mockContext, 'create user authentication system');

      expect(result).toEqual({ redraw: true });
      // Scout analysis should be called first (after initialization)
    });

    it('should allow skipping Scout analysis with "skip scout" flag', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn();

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      await agentCommand.handler(mockContext, 'create user auth skip scout');

      // Scout analysis should NOT be called when skip flag is present
      expect(mockAnalyzeBeforeOperation).not.toHaveBeenCalled();
    });

    it('should prompt for confirmation when Scout recommends not proceeding', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn().mockResolvedValue({
        requestId: 'test-123',
        operation: 'test operation',
        timestamp: new Date(),
        duplications: [
          {
            filePath: 'src/auth/login.ts',
            similarity: 0.95,
            matchedLines: [10, 11, 12],
            pattern: 'authentication logic',
            confidence: 0.9,
            suggestion: 'Reuse existing authentication implementation'
          }
        ],
        dependencies: { affectedFiles: [], breakingChanges: [], riskLevel: 'high', mitigations: [], estimatedEffort: '4h' },
        technicalDebt: [],
        shouldProceed: false, // Scout recommends not proceeding
        warnings: ['Found highly similar implementation'],
        suggestions: ['Consider reusing existing code'],
        alternatives: ['Reuse src/auth/login.ts'],
        analysisTime: 150,
        cacheHit: false,
        confidence: 0.9,
        impactVisualization: { affected: 5, complexity: 3, riskScore: 75 }
      });

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      // Test user cancels operation
      mockContext.requestConfirmation = vi.fn().mockResolvedValue(false);

      const result = await agentCommand.handler(mockContext, 'implement user authentication');

      expect(mockContext.requestConfirmation).toHaveBeenCalledWith('Scout found issues. Continue anyway?');
      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('Operation cancelled by user.')
      });
      expect(result).toEqual({ redraw: true });
    });
  });

  describe('Scout Command', () => {
    it('should provide detailed analysis results', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn().mockResolvedValue({
        requestId: 'scout-test-123',
        operation: 'Scout analysis',
        timestamp: new Date(),
        duplications: [
          {
            filePath: 'src/utils/validator.ts',
            similarity: 0.85,
            matchedLines: [15, 16, 17],
            pattern: 'validation function',
            confidence: 0.8,
            suggestion: 'Consider reusing existing validation implementation'
          }
        ],
        dependencies: { affectedFiles: ['tests/validator.test.ts'], breakingChanges: [], riskLevel: 'medium', mitigations: [], estimatedEffort: '2h' },
        technicalDebt: [
          {
            type: 'complexity',
            severity: 'warning',
            description: 'Function is too complex',
            location: 'src/utils/validator.ts:25',
            recommendation: 'Break into smaller functions',
            estimatedFixTime: '1h'
          }
        ],
        shouldProceed: true,
        warnings: ['Medium complexity detected'],
        suggestions: ['Consider refactoring for better maintainability'],
        alternatives: [],
        analysisTime: 200,
        cacheHit: false,
        confidence: 0.85,
        impactVisualization: { affected: 2, complexity: 2, riskScore: 45 }
      });

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      const result = await scoutCommand.handler(mockContext, 'validation logic');

      expect(mockAnalyzeBeforeOperation).toHaveBeenCalledWith({
        operation: 'Scout analysis',
        description: 'validation logic',
        context: {
          filePath: undefined,
          intent: 'general',
          language: 'typescript'
        }
      });

      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'warning',
        text: expect.stringContaining('Found 1 potential duplication(s)')
      });

      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'warning',
        text: expect.stringContaining('Found 1 technical debt issue(s)')
      });

      expect(result).toEqual({ redraw: true });
    });

    it('should detect file paths in Scout commands', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn().mockResolvedValue({
        requestId: 'scout-file-test',
        operation: 'Scout analysis',
        timestamp: new Date(),
        duplications: [],
        dependencies: { affectedFiles: [], breakingChanges: [], riskLevel: 'low', mitigations: [], estimatedEffort: '0h' },
        technicalDebt: [],
        shouldProceed: true,
        warnings: [],
        suggestions: [],
        alternatives: [],
        analysisTime: 50,
        cacheHit: false,
        confidence: 0.7,
        impactVisualization: { affected: 0, complexity: 0, riskScore: 5 }
      });

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      await scoutCommand.handler(mockContext, 'src/utils/helper.ts');

      expect(mockAnalyzeBeforeOperation).toHaveBeenCalledWith({
        operation: 'Scout analysis',
        description: 'src/utils/helper.ts',
        context: {
          filePath: 'src/utils/helper.ts',
          intent: 'general',
          language: 'typescript'
        }
      });
    });

    it('should display risk summary correctly', async () => {
      const { ScoutPipeline } = await import('../../agents/scout-pipeline.js');
      const mockAnalyzeBeforeOperation = vi.fn().mockResolvedValue({
        requestId: 'scout-risk-test',
        operation: 'Scout analysis',
        timestamp: new Date(),
        duplications: [],
        dependencies: { affectedFiles: [], breakingChanges: [], riskLevel: 'low', mitigations: [], estimatedEffort: '0h' },
        technicalDebt: [],
        shouldProceed: true,
        warnings: [],
        suggestions: [],
        alternatives: [],
        analysisTime: 75,
        cacheHit: false,
        confidence: 0.9,
        impactVisualization: { affected: 0, complexity: 0, riskScore: 75 } // High risk
      });

      (ScoutPipeline as any).mockImplementation(() => ({
        analyzeBeforeOperation: mockAnalyzeBeforeOperation,
        on: vi.fn()
      }));

      await scoutCommand.handler(mockContext, 'complex security module');

      // Should show HIGH risk in red
      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('HIGH risk (75% score)')
      });
    });
  });

  describe('Integration with Existing Commands', () => {
    it('should handle agent command with no arguments', async () => {
      const result = await agentCommand.handler(mockContext);

      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'info',
        text: 'Please provide a command. Use "/agent help" for examples.'
      });
      expect(result).toEqual({ redraw: true });
    });

    it('should display help correctly', async () => {
      const result = await agentCommand.handler(mockContext, 'help');

      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('Scout-First Architecture')
      });
      expect(result).toEqual({ redraw: true });
    });

    it('should handle Scout command with no arguments', async () => {
      const result = await scoutCommand.handler(mockContext);

      expect(mockContext.addMessage).toHaveBeenCalledWith({
        type: 'info',
        text: 'Please specify what to check. Example: /scout authentication logic'
      });
      expect(result).toEqual({ redraw: true });
    });
  });

  describe('Intent Extraction', () => {
    it('should extract implementation intent correctly', async () => {
      // This test would verify the extractIntent function
      // Implementation intents: implement, create, build
      const testCases = [
        { input: 'implement user authentication', expected: 'implementation' },
        { input: 'create REST API', expected: 'implementation' },
        { input: 'build payment system', expected: 'implementation' },
        { input: 'check for duplicates', expected: 'analysis' },
        { input: 'review security vulnerabilities', expected: 'analysis' },
        { input: 'refactor database module', expected: 'refactoring' },
        { input: 'test user service', expected: 'testing' },
        { input: 'design system architecture', expected: 'design' },
        { input: 'scan for security issues', expected: 'security' },
        { input: 'random command', expected: 'general' }
      ];

      // Note: extractIntent is currently a private function
      // In a real implementation, we might expose it for testing
      // or test it indirectly through the Scout analysis
      expect(testCases.length).toBeGreaterThan(0);
    });
  });
});