/**
 * Error Handler Tests
 * Comprehensive tests for error handling and recovery mechanisms
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import ErrorHandler, { ErrorContext, ErrorHandlingStrategy, RecoveryAction } from './error-handler.js';
import { createMockConfig, mockConsole, AsyncTestUtils, ErrorTestUtils } from '../test-utils/test-helpers.js';
import { Config } from '@google/gemini-cli-core';

describe('ErrorHandler', () => {
  let errorHandler: ErrorHandler;
  let mockConfig: Config;
  let consoleMock: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfig = createMockConfig();
    consoleMock = mockConsole();
    errorHandler = new ErrorHandler(mockConfig);
  });

  afterEach(() => {
    consoleMock.restore();
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      expect(errorHandler).toBeDefined();
      expect(errorHandler.isEnabled()).toBe(true);
      expect(errorHandler.getErrorCount()).toBe(0);
    });

    it('should set up error handling strategies', () => {
      const strategies = errorHandler.getHandlingStrategies();
      expect(strategies.length).toBeGreaterThan(0);
      expect(strategies.some(s => s.type === 'retry')).toBe(true);
      expect(strategies.some(s => s.type === 'fallback')).toBe(true);
    });
  });

  describe('Error Classification', () => {
    it('should classify network errors correctly', () => {
      const error = new Error('Network request failed');
      error.code = 'ECONNREFUSED';
      
      const classification = errorHandler.classifyError(error);
      
      expect(classification.category).toBe('network');
      expect(classification.severity).toBe('high');
      expect(classification.recoverable).toBe(true);
    });

    it('should classify validation errors correctly', () => {
      const error = new Error('Invalid input format');
      error.code = 'VALIDATION_ERROR';
      
      const classification = errorHandler.classifyError(error);
      
      expect(classification.category).toBe('validation');
      expect(classification.severity).toBe('medium');
      expect(classification.recoverable).toBe(false);
    });

    it('should classify system errors correctly', () => {
      const error = new Error('Out of memory');
      error.code = 'ENOMEM';
      
      const classification = errorHandler.classifyError(error);
      
      expect(classification.category).toBe('system');
      expect(classification.severity).toBe('critical');
      expect(classification.recoverable).toBe(false);
    });

    it('should classify unknown errors as generic', () => {
      const error = new Error('Unknown error occurred');
      
      const classification = errorHandler.classifyError(error);
      
      expect(classification.category).toBe('generic');
      expect(classification.severity).toBe('medium');
      expect(classification.recoverable).toBe(true);
    });
  });

  describe('Error Handling Strategies', () => {
    it('should execute retry strategy for transient errors', async () => {
      let attempts = 0;
      const operation = vi.fn(() => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Transient error');
        }
        return 'success';
      });

      const context: ErrorContext = {
        operation: 'test_operation',
        agentId: 'test-agent',
        metadata: { retryable: true }
      };

      const result = await errorHandler.handleError(
        new Error('Transient error'),
        context,
        operation
      );

      expect(result.success).toBe(true);
      expect(result.result).toBe('success');
      expect(attempts).toBe(3);
    });

    it('should execute fallback strategy when retries fail', async () => {
      const operation = vi.fn(() => {
        throw new Error('Persistent error');
      });

      const fallbackOperation = vi.fn(() => 'fallback_result');

      const context: ErrorContext = {
        operation: 'test_operation',
        agentId: 'test-agent',
        metadata: { 
          retryable: true,
          fallback: fallbackOperation
        }
      };

      const result = await errorHandler.handleError(
        new Error('Persistent error'),
        context,
        operation
      );

      expect(result.success).toBe(true);
      expect(result.result).toBe('fallback_result');
      expect(fallbackOperation).toHaveBeenCalled();
    });

    it('should circuit break after too many failures', async () => {
      const operation = vi.fn(() => {
        throw new Error('Service unavailable');
      });

      const context: ErrorContext = {
        operation: 'test_operation',
        agentId: 'test-agent',
        metadata: { circuitBreaker: true }
      };

      // Cause multiple failures to trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        await errorHandler.handleError(
          new Error('Service unavailable'),
          context,
          operation
        );
      }

      const result = await errorHandler.handleError(
        new Error('Service unavailable'),
        context,
        operation
      );

      expect(result.success).toBe(false);
      expect(result.error).toContain('Circuit breaker open');
    });
  });

  describe('Error Recovery', () => {
    it('should provide recovery actions for known errors', () => {
      const error = new Error('Authentication failed');
      error.code = 'AUTH_ERROR';

      const recoveryActions = errorHandler.getRecoveryActions(error);

      expect(recoveryActions.length).toBeGreaterThan(0);
      expect(recoveryActions.some(a => a.type === 'refresh_token')).toBe(true);
      expect(recoveryActions.some(a => a.type === 'reauth')).toBe(true);
    });

    it('should execute automatic recovery for supported errors', async () => {
      const mockRefreshToken = vi.fn().mockResolvedValue('new_token');
      
      const error = new Error('Token expired');
      error.code = 'TOKEN_EXPIRED';

      const context: ErrorContext = {
        operation: 'api_call',
        agentId: 'test-agent',
        metadata: { 
          autoRecover: true,
          refreshToken: mockRefreshToken
        }
      };

      const result = await errorHandler.handleError(error, context);

      expect(result.recovered).toBe(true);
      expect(mockRefreshToken).toHaveBeenCalled();
    });

    it('should suggest manual recovery steps for complex errors', () => {
      const error = new Error('Database schema mismatch');
      error.code = 'SCHEMA_ERROR';

      const recoveryActions = errorHandler.getRecoveryActions(error);

      expect(recoveryActions.some(a => a.type === 'manual')).toBe(true);
      expect(recoveryActions.some(a => a.description.includes('migration'))).toBe(true);
    });
  });

  describe('Error Logging and Reporting', () => {
    it('should log errors with proper context', async () => {
      const error = new Error('Test error');
      const context: ErrorContext = {
        operation: 'test_operation',
        agentId: 'test-agent',
        metadata: { userId: 'user123' }
      };

      await errorHandler.handleError(error, context);

      const errorLogs = consoleMock.getLogs('error');
      expect(errorLogs.length).toBeGreaterThan(0);
      expect(errorLogs[0].args[0]).toContain('test_operation');
      expect(errorLogs[0].args[0]).toContain('test-agent');
    });

    it('should track error statistics', async () => {
      const error1 = new Error('Network error');
      error1.code = 'ECONNREFUSED';
      
      const error2 = new Error('Validation error');
      error2.code = 'VALIDATION_ERROR';

      await errorHandler.handleError(error1, { operation: 'op1', agentId: 'agent1' });
      await errorHandler.handleError(error2, { operation: 'op2', agentId: 'agent2' });

      const stats = errorHandler.getErrorStatistics();
      expect(stats.totalErrors).toBe(2);
      expect(stats.errorsByCategory.network).toBe(1);
      expect(stats.errorsByCategory.validation).toBe(1);
      expect(stats.errorsByAgent['agent1']).toBe(1);
      expect(stats.errorsByAgent['agent2']).toBe(1);
    });

    it('should emit error events for monitoring', async () => {
      const errorEvents: any[] = [];
      errorHandler.on('error_handled', (data) => {
        errorEvents.push(data);
      });

      const error = new Error('Test error');
      const context: ErrorContext = {
        operation: 'test_operation',
        agentId: 'test-agent'
      };

      await errorHandler.handleError(error, context);

      expect(errorEvents.length).toBe(1);
      expect(errorEvents[0].error.message).toBe('Test error');
      expect(errorEvents[0].context.operation).toBe('test_operation');
    });
  });

  describe('Error Patterns and Analysis', () => {
    it('should detect recurring error patterns', async () => {
      const similarErrors = [
        new Error('Connection timeout to service A'),
        new Error('Connection timeout to service B'),
        new Error('Connection timeout to service C')
      ];

      for (const error of similarErrors) {
        await errorHandler.handleError(error, { operation: 'api_call', agentId: 'agent' });
      }

      const patterns = errorHandler.detectErrorPatterns();
      expect(patterns.length).toBeGreaterThan(0);
      expect(patterns[0].pattern).toContain('timeout');
      expect(patterns[0].frequency).toBe(3);
    });

    it('should provide recommendations based on error trends', async () => {
      // Simulate high error rate for specific agent
      for (let i = 0; i < 10; i++) {
        await errorHandler.handleError(
          new Error('Service unavailable'),
          { operation: 'api_call', agentId: 'problematic-agent' }
        );
      }

      const recommendations = errorHandler.getRecommendations();
      expect(recommendations.length).toBeGreaterThan(0);
      expect(recommendations.some(r => r.includes('problematic-agent'))).toBe(true);
      expect(recommendations.some(r => r.includes('circuit breaker'))).toBe(true);
    });
  });

  describe('Configuration and Customization', () => {
    it('should update error handling configuration', () => {
      const newConfig = {
        maxRetries: 5,
        retryDelay: 2000,
        circuitBreakerThreshold: 10
      };

      errorHandler.updateConfiguration(newConfig);
      const config = errorHandler.getConfiguration();

      expect(config.maxRetries).toBe(5);
      expect(config.retryDelay).toBe(2000);
      expect(config.circuitBreakerThreshold).toBe(10);
    });

    it('should register custom error handlers', () => {
      const customHandler = {
        canHandle: (error: Error) => error.message.includes('custom'),
        handle: vi.fn().mockResolvedValue({ success: true, result: 'custom_handled' })
      };

      errorHandler.registerCustomHandler('custom_error', customHandler);

      const error = new Error('This is a custom error');
      const handler = errorHandler.findHandler(error);

      expect(handler).toBeDefined();
      expect(handler.name).toBe('custom_error');
    });
  });

  describe('Performance and Efficiency', () => {
    it('should handle errors efficiently under load', async () => {
      const errors = Array.from({ length: 100 }, (_, i) => 
        new Error(`Error ${i}`)
      );

      const startTime = Date.now();
      
      await Promise.all(
        errors.map(error => 
          errorHandler.handleError(error, { operation: 'load_test', agentId: 'agent' })
        )
      );

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(5000); // Should handle 100 errors in less than 5 seconds
    });

    it('should cleanup old error records to prevent memory leaks', async () => {
      // Generate many errors
      for (let i = 0; i < 1000; i++) {
        await errorHandler.handleError(
          new Error(`Error ${i}`),
          { operation: 'memory_test', agentId: 'agent' }
        );
      }

      errorHandler.cleanup();

      const stats = errorHandler.getErrorStatistics();
      expect(stats.totalErrors).toBeLessThan(1000); // Should have cleaned up old errors
    });
  });

  describe('Integration and Compatibility', () => {
    it('should integrate with agent error boundaries', async () => {
      const agentError = new Error('Agent execution failed');
      agentError.agentId = 'scout';
      agentError.operation = 'analyze_code';

      const context: ErrorContext = {
        operation: 'analyze_code',
        agentId: 'scout',
        metadata: { 
          agentSpecific: true,
          retryWithDifferentAgent: true
        }
      };

      const result = await errorHandler.handleError(agentError, context);

      expect(result.alternativeAgent).toBeDefined();
      expect(result.recoveryStrategy).toBe('agent_fallback');
    });

    it('should handle async operation errors gracefully', async () => {
      const asyncOperation = async () => {
        await AsyncTestUtils.delay(100);
        throw new Error('Async operation failed');
      };

      const context: ErrorContext = {
        operation: 'async_test',
        agentId: 'async-agent'
      };

      const result = await errorHandler.handleError(
        new Error('Async operation failed'),
        context,
        asyncOperation
      );

      expect(result).toBeDefined();
      expect(result.success).toBe(false);
    });
  });
});