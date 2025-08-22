/**
 * Scout Pipeline Tests
 * Comprehensive tests for Scout analysis and duplication detection
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import ScoutPipeline, { ScoutAnalysisRequest, ScoutAnalysisResult, DuplicateMatch, TechnicalDebtItem } from './scout-pipeline.js';
import { createMockConfig, mockSuccessfulFetch, mockConsole, AgentTestUtils, DataGenerators } from '../test-utils/test-helpers.js';
import { Config } from '@google/gemini-cli-core';

describe('ScoutPipeline', () => {
  let scout: ScoutPipeline;
  let mockConfig: Config;
  let consoleMock: any;
  let fetchMock: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfig = createMockConfig();
    consoleMock = mockConsole();
    fetchMock = mockSuccessfulFetch({
      duplicates: [],
      dependencies: [],
      technical_debt: [],
      code_quality_score: 8.5,
      risk_assessment: 'low'
    });

    scout = new ScoutPipeline(mockConfig);
  });

  afterEach(() => {
    consoleMock.restore();
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      expect(scout).toBeDefined();
      expect(scout.getAnalysisHistory()).toHaveLength(0);
    });

    it('should set up event handlers', () => {
      const eventHandler = vi.fn();
      scout.on('analysis_completed', eventHandler);
      expect(scout.listenerCount('analysis_completed')).toBe(1);
    });
  });

  describe('Duplication Detection', () => {
    it('should detect exact duplicates', async () => {
      const mockDuplicates: DuplicateMatch[] = [
        {
          file1: '/src/auth/login.ts',
          file2: '/src/user/authenticate.ts',
          similarity: 0.95,
          type: 'exact',
          conflictingLines: [[10, 20], [15, 25]],
          suggestion: 'Consider extracting common functionality'
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          duplicates: mockDuplicates,
          code_quality_score: 7.5
        })
      });

      const request: ScoutAnalysisRequest = {
        operation: 'implement_authentication',
        target_files: ['/src/auth/login.ts'],
        project_context: 'User authentication system'
      };

      const result = await scout.analyzeBeforeOperation(request);

      expect(result.duplicates).toHaveLength(1);
      expect(result.duplicates[0].similarity).toBe(0.95);
      expect(result.duplicates[0].type).toBe('exact');
      expect(result.recommendation).toContain('duplicate');
    });

    it('should detect partial duplicates', async () => {
      const mockDuplicates: DuplicateMatch[] = [
        {
          file1: '/src/validation/email.ts',
          file2: '/src/utils/validators.ts',
          similarity: 0.75,
          type: 'partial',
          conflictingLines: [[5, 15], [20, 30]],
          suggestion: 'Merge validation logic into shared utility'
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ duplicates: mockDuplicates })
      });

      const request: ScoutAnalysisRequest = {
        operation: 'add_email_validation',
        target_files: ['/src/validation/email.ts']
      };

      const result = await scout.analyzeBeforeOperation(request);

      expect(result.duplicates[0].type).toBe('partial');
      expect(result.duplicates[0].similarity).toBe(0.75);
    });

    it('should detect semantic duplicates', async () => {
      const mockDuplicates: DuplicateMatch[] = [
        {
          file1: '/src/api/users.ts',
          file2: '/src/services/user-service.ts',
          similarity: 0.68,
          type: 'semantic',
          conflictingLines: [[1, 50], [1, 60]],
          suggestion: 'Similar functionality detected - consider consolidation'
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ duplicates: mockDuplicates })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'refactor_user_management',
        target_files: ['/src/api/users.ts']
      });

      expect(result.duplicates[0].type).toBe('semantic');
      expect(result.duplicates[0].similarity).toBeGreaterThan(0.6);
    });

    it('should handle no duplicates found', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          duplicates: [],
          code_quality_score: 9.2
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'create_new_feature',
        target_files: ['/src/new/feature.ts']
      });

      expect(result.duplicates).toHaveLength(0);
      expect(result.recommendation).toContain('No duplicates found');
    });
  });

  describe('Dependency Analysis', () => {
    it('should analyze dependency impact', async () => {
      const mockDependencies = [
        {
          name: '@auth/core',
          version: '2.1.0',
          impact: 'high',
          reason: 'Core authentication dependency',
          affected_files: ['/src/auth/*.ts']
        },
        {
          name: 'express',
          version: '4.18.0',
          impact: 'medium',
          reason: 'Web framework dependency',
          affected_files: ['/src/server/*.ts']
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          dependencies: mockDependencies,
          dependency_conflicts: []
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'update_authentication',
        target_files: ['/src/auth/login.ts']
      });

      expect(result.dependencyAnalysis.impactedDependencies).toHaveLength(2);
      expect(result.dependencyAnalysis.impactedDependencies[0].impact).toBe('high');
    });

    it('should detect dependency conflicts', async () => {
      const mockConflicts = [
        {
          dependency1: '@types/node@16.0.0',
          dependency2: '@types/express@4.17.0',
          conflict_type: 'version_mismatch',
          severity: 'warning',
          resolution: 'Update @types/node to compatible version'
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          dependencies: [],
          dependency_conflicts: mockConflicts
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'add_type_definitions',
        target_files: ['/src/types/index.ts']
      });

      expect(result.dependencyAnalysis.conflicts).toHaveLength(1);
      expect(result.dependencyAnalysis.conflicts[0].severity).toBe('warning');
    });

    it('should analyze circular dependencies', async () => {
      const mockCircularDeps = [
        {
          cycle: ['/src/user.ts', '/src/auth.ts', '/src/user.ts'],
          severity: 'error',
          suggestion: 'Extract shared interfaces to separate module'
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          circular_dependencies: mockCircularDeps
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'refactor_imports',
        target_files: ['/src/user.ts', '/src/auth.ts']
      });

      expect(result.dependencyAnalysis.circularDependencies).toHaveLength(1);
      expect(result.dependencyAnalysis.circularDependencies[0].severity).toBe('error');
    });
  });

  describe('Technical Debt Detection', () => {
    it('should identify code smells', async () => {
      const mockTechnicalDebt: TechnicalDebtItem[] = [
        {
          type: 'code_smell',
          file: '/src/legacy/processor.ts',
          severity: 'medium',
          description: 'Long function with high complexity',
          suggestion: 'Break down into smaller functions',
          effort_estimate: '2 hours',
          debt_score: 6.5
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          technical_debt: mockTechnicalDebt
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'refactor_legacy_code',
        target_files: ['/src/legacy/processor.ts']
      });

      expect(result.technicalDebt).toHaveLength(1);
      expect(result.technicalDebt[0].type).toBe('code_smell');
      expect(result.technicalDebt[0].debt_score).toBe(6.5);
    });

    it('should detect performance issues', async () => {
      const mockPerformanceIssues: TechnicalDebtItem[] = [
        {
          type: 'performance',
          file: '/src/api/heavy-operation.ts',
          severity: 'high',
          description: 'N+1 query pattern detected',
          suggestion: 'Implement query batching',
          effort_estimate: '4 hours',
          debt_score: 8.2
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          technical_debt: mockPerformanceIssues
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'optimize_database_queries',
        target_files: ['/src/api/heavy-operation.ts']
      });

      expect(result.technicalDebt[0].type).toBe('performance');
      expect(result.technicalDebt[0].severity).toBe('high');
    });

    it('should identify security vulnerabilities', async () => {
      const mockSecurityIssues: TechnicalDebtItem[] = [
        {
          type: 'security',
          file: '/src/auth/password.ts',
          severity: 'critical',
          description: 'Hardcoded secret detected',
          suggestion: 'Move to environment variables',
          effort_estimate: '1 hour',
          debt_score: 9.5
        }
      ];

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          technical_debt: mockSecurityIssues
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'security_audit',
        target_files: ['/src/auth/password.ts']
      });

      expect(result.technicalDebt[0].type).toBe('security');
      expect(result.technicalDebt[0].severity).toBe('critical');
    });
  });

  describe('Code Quality Assessment', () => {
    it('should calculate code quality score', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          code_quality_score: 8.7,
          quality_factors: {
            maintainability: 9.0,
            readability: 8.5,
            testability: 8.2,
            performance: 9.1
          }
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'quality_assessment',
        target_files: ['/src/utils/helpers.ts']
      });

      expect(result.codeQualityScore).toBe(8.7);
      expect(result.qualityFactors.maintainability).toBe(9.0);
      expect(result.qualityFactors.readability).toBe(8.5);
    });

    it('should provide quality improvement suggestions', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          code_quality_score: 6.2,
          quality_suggestions: [
            'Add unit tests to improve testability',
            'Extract complex functions for better readability',
            'Add TypeScript interfaces for better maintainability'
          ]
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'improve_code_quality',
        target_files: ['/src/legacy/old-module.js']
      });

      expect(result.codeQualityScore).toBe(6.2);
      expect(result.qualitySuggestions).toHaveLength(3);
      expect(result.qualitySuggestions[0]).toContain('unit tests');
    });
  });

  describe('Risk Assessment', () => {
    it('should assess low risk operations', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          risk_assessment: 'low',
          risk_factors: [
            'Simple utility function addition',
            'No external dependencies',
            'Well-tested module'
          ],
          risk_score: 2.1
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'add_utility_function',
        target_files: ['/src/utils/string-helpers.ts']
      });

      expect(result.riskAssessment.level).toBe('low');
      expect(result.riskAssessment.score).toBe(2.1);
      expect(result.riskAssessment.factors).toHaveLength(3);
    });

    it('should assess high risk operations', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          risk_assessment: 'high',
          risk_factors: [
            'Core authentication system modification',
            'Multiple dependency updates required',
            'Potential breaking changes'
          ],
          risk_score: 8.7
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'refactor_authentication_core',
        target_files: ['/src/auth/core.ts']
      });

      expect(result.riskAssessment.level).toBe('high');
      expect(result.riskAssessment.score).toBe(8.7);
      expect(result.recommendation).toContain('high risk');
    });

    it('should recommend user confirmation for risky operations', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          risk_assessment: 'high',
          risk_score: 9.2,
          requires_confirmation: true
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'delete_core_module',
        target_files: ['/src/core/essential.ts']
      });

      expect(result.requiresUserConfirmation).toBe(true);
      expect(result.riskAssessment.level).toBe('high');
    });
  });

  describe('Performance and Caching', () => {
    it('should cache analysis results', async () => {
      const request: ScoutAnalysisRequest = {
        operation: 'test_operation',
        target_files: ['/src/test.ts']
      };

      // First call
      await scout.analyzeBeforeOperation(request);
      
      // Second call should use cache
      const result = await scout.analyzeBeforeOperation(request);

      expect(fetch).toHaveBeenCalledTimes(1); // Only one actual API call
      expect(result).toBeDefined();
    });

    it('should invalidate cache when files change', async () => {
      const request: ScoutAnalysisRequest = {
        operation: 'test_operation',
        target_files: ['/src/test.ts']
      };

      await scout.analyzeBeforeOperation(request);
      
      // Simulate file change
      scout.invalidateCache(['/src/test.ts']);
      
      await scout.analyzeBeforeOperation(request);

      expect(fetch).toHaveBeenCalledTimes(2); // Two API calls due to cache invalidation
    });

    it('should handle large file analysis efficiently', async () => {
      const largeFileList = Array.from({ length: 100 }, (_, i) => `/src/file${i}.ts`);
      
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          duplicates: [],
          processing_time: 2500,
          files_processed: 100
        })
      });

      const startTime = Date.now();
      const result = await scout.analyzeBeforeOperation({
        operation: 'large_refactoring',
        target_files: largeFileList
      });
      const duration = Date.now() - startTime;

      expect(result).toBeDefined();
      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
    });
  });

  describe('Integration and Workflow', () => {
    it('should integrate with agent orchestrator', async () => {
      const workflowEvents: any[] = [];
      scout.on('workflow_step_completed', (data) => {
        workflowEvents.push(data);
      });

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          duplicates: [],
          workflow_ready: true,
          next_suggested_agent: 'architect'
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'implement_new_feature',
        target_files: ['/src/features/new-feature.ts'],
        workflow_context: { previous_agent: 'none' }
      });

      expect(result.nextSuggestedAgent).toBe('architect');
      expect(workflowEvents).toHaveLength(1);
    });

    it('should provide recommendations for next steps', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          duplicates: [{ similarity: 0.9, type: 'exact' }],
          recommendations: [
            'Review existing implementation before proceeding',
            'Consider extracting common functionality',
            'Update existing code instead of creating duplicate'
          ]
        })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'add_duplicate_functionality',
        target_files: ['/src/duplicate.ts']
      });

      expect(result.recommendations).toHaveLength(3);
      expect(result.recommendations[0]).toContain('Review existing');
    });

    it('should emit analysis events', async () => {
      const analysisEvents: any[] = [];
      scout.on('analysis_completed', (data) => {
        analysisEvents.push(data);
      });

      await scout.analyzeBeforeOperation({
        operation: 'test_operation',
        target_files: ['/src/test.ts']
      });

      expect(analysisEvents).toHaveLength(1);
      expect(analysisEvents[0].operation).toBe('test_operation');
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      const result = await scout.analyzeBeforeOperation({
        operation: 'test_operation',
        target_files: ['/src/test.ts']
      });

      expect(result.error).toBeDefined();
      expect(result.recommendation).toContain('analysis failed');
      expect(consoleMock.getLogs('error')).toHaveLength(1);
    });

    it('should handle malformed responses', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'response' })
      });

      const result = await scout.analyzeBeforeOperation({
        operation: 'test_operation',
        target_files: ['/src/test.ts']
      });

      expect(result.duplicates).toHaveLength(0);
      expect(result.riskAssessment.level).toBe('unknown');
    });

    it('should timeout on slow responses', async () => {
      fetchMock.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ duplicates: [] })
          }), 10000)
        )
      );

      const result = await scout.analyzeBeforeOperation({
        operation: 'slow_operation',
        target_files: ['/src/slow.ts']
      }, { timeout: 100 });

      expect(result.error).toContain('timeout');
    });
  });

  describe('Analysis History', () => {
    it('should maintain analysis history', async () => {
      await scout.analyzeBeforeOperation({
        operation: 'operation1',
        target_files: ['/src/test1.ts']
      });

      await scout.analyzeBeforeOperation({
        operation: 'operation2',
        target_files: ['/src/test2.ts']
      });

      const history = scout.getAnalysisHistory();
      expect(history).toHaveLength(2);
      expect(history[0].operation).toBe('operation1');
      expect(history[1].operation).toBe('operation2');
    });

    it('should limit history size', async () => {
      // Perform more analyses than the history limit
      for (let i = 0; i < 15; i++) {
        await scout.analyzeBeforeOperation({
          operation: `operation${i}`,
          target_files: [`/src/test${i}.ts`]
        });
      }

      const history = scout.getAnalysisHistory();
      expect(history).toHaveLength(10); // Default history limit
    });

    it('should provide analysis statistics', async () => {
      // Perform several analyses with different results
      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ duplicates: [{ similarity: 0.9 }], risk_assessment: 'high' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ duplicates: [], risk_assessment: 'low' })
        });

      await scout.analyzeBeforeOperation({
        operation: 'high_risk_op',
        target_files: ['/src/risky.ts']
      });

      await scout.analyzeBeforeOperation({
        operation: 'safe_op',
        target_files: ['/src/safe.ts']
      });

      const stats = scout.getAnalysisStatistics();
      expect(stats.totalAnalyses).toBe(2);
      expect(stats.duplicatesFound).toBe(1);
      expect(stats.highRiskOperations).toBe(1);
    });
  });
});