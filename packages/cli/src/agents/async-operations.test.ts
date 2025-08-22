/**
 * Async Operations Tests
 * Comprehensive tests for asynchronous agent operations and workflows
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createMockConfig, mockSuccessfulFetch, mockConsole, AsyncTestUtils, AgentTestUtils } from '../test-utils/test-helpers.js';
import { Config } from '@google/gemini-cli-core';

// Mock agent operations for testing
class AsyncAgentOperations {
  private config: Config;
  private pendingOperations: Map<string, Promise<any>> = new Map();
  private operationTimeouts: Map<string, NodeJS.Timeout> = new Map();

  constructor(config: Config) {
    this.config = config;
  }

  /**
   * Execute single agent operation asynchronously
   */
  async executeAgentOperation(agentId: string, operation: string, input: any): Promise<any> {
    const operationId = `${agentId}_${operation}_${Date.now()}`;
    
    const operationPromise = this.performAsyncOperation(agentId, operation, input);
    this.pendingOperations.set(operationId, operationPromise);

    // Set timeout
    const timeout = setTimeout(() => {
      this.cancelOperation(operationId);
    }, 30000);
    this.operationTimeouts.set(operationId, timeout);

    try {
      const result = await operationPromise;
      this.cleanup(operationId);
      return { operationId, result, status: 'completed' };
    } catch (error) {
      this.cleanup(operationId);
      return { operationId, error, status: 'failed' };
    }
  }

  /**
   * Execute multiple agent operations concurrently
   */
  async executeMultipleOperations(operations: Array<{ agentId: string; operation: string; input: any }>): Promise<any[]> {
    const promises = operations.map((op, index) => 
      this.executeAgentOperation(op.agentId, op.operation, op.input).catch(error => ({
        operationId: `${op.agentId}_${index}`,
        error,
        status: 'failed'
      }))
    );

    return Promise.all(promises);
  }

  /**
   * Execute operations in sequence
   */
  async executeSequentialOperations(operations: Array<{ agentId: string; operation: string; input: any }>): Promise<any[]> {
    const results: any[] = [];
    
    for (const operation of operations) {
      const result = await this.executeAgentOperation(operation.agentId, operation.operation, operation.input);
      results.push(result);
      
      // If operation failed and it's critical, stop the sequence
      if (result.status === 'failed' && operation.input?.critical) {
        break;
      }
    }
    
    return results;
  }

  /**
   * Execute operations with retry logic
   */
  async executeWithRetry(agentId: string, operation: string, input: any, maxRetries: number = 3): Promise<any> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const result = await this.executeAgentOperation(agentId, operation, input);
        
        if (result.status === 'completed') {
          return result;
        }
        
        lastError = result.error;
        
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
          await AsyncTestUtils.delay(delay);
        }
      } catch (error) {
        lastError = error;
        
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
          await AsyncTestUtils.delay(delay);
        }
      }
    }
    
    return { operationId: `retry_${Date.now()}`, error: lastError, status: 'failed_after_retries' };
  }

  /**
   * Get status of pending operations
   */
  getPendingOperations(): string[] {
    return Array.from(this.pendingOperations.keys());
  }

  /**
   * Cancel specific operation
   */
  cancelOperation(operationId: string): boolean {
    const operation = this.pendingOperations.get(operationId);
    if (operation) {
      this.cleanup(operationId);
      return true;
    }
    return false;
  }

  /**
   * Cancel all pending operations
   */
  cancelAllOperations(): number {
    const count = this.pendingOperations.size;
    this.pendingOperations.forEach((_, operationId) => {
      this.cleanup(operationId);
    });
    return count;
  }

  /**
   * Wait for all operations to complete
   */
  async waitForAllOperations(): Promise<any[]> {
    const pendingPromises = Array.from(this.pendingOperations.values());
    const results = await Promise.allSettled(pendingPromises);
    
    return results.map(result => ({
      status: result.status,
      value: result.status === 'fulfilled' ? result.value : undefined,
      error: result.status === 'rejected' ? result.reason : undefined
    }));
  }

  private async performAsyncOperation(agentId: string, operation: string, input: any): Promise<any> {
    // Simulate different types of async operations
    const operationType = input?.type || 'default';
    
    switch (operationType) {
      case 'fast':
        await AsyncTestUtils.delay(50);
        return { result: `Fast ${operation} completed`, agent: agentId };
        
      case 'slow':
        await AsyncTestUtils.delay(2000);
        return { result: `Slow ${operation} completed`, agent: agentId };
        
      case 'error':
        await AsyncTestUtils.delay(100);
        throw new Error(`Operation ${operation} failed`);
        
      case 'timeout':
        await AsyncTestUtils.delay(35000); // Longer than timeout
        return { result: 'Should not reach here', agent: agentId };
        
      case 'variable':
        const delay = Math.random() * 1000;
        await AsyncTestUtils.delay(delay);
        return { result: `Variable ${operation} completed in ${delay}ms`, agent: agentId };
        
      default:
        await AsyncTestUtils.delay(100 + Math.random() * 400);
        return { result: `${operation} completed`, agent: agentId, input };
    }
  }

  private cleanup(operationId: string): void {
    this.pendingOperations.delete(operationId);
    
    const timeout = this.operationTimeouts.get(operationId);
    if (timeout) {
      clearTimeout(timeout);
      this.operationTimeouts.delete(operationId);
    }
  }
}

describe('Async Operations', () => {
  let asyncOps: AsyncAgentOperations;
  let mockConfig: Config;
  let consoleMock: any;
  let fetchMock: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfig = createMockConfig();
    consoleMock = mockConsole();
    fetchMock = mockSuccessfulFetch({ success: true });
    
    asyncOps = new AsyncAgentOperations(mockConfig);
  });

  afterEach(() => {
    consoleMock.restore();
    vi.restoreAllMocks();
    asyncOps.cancelAllOperations();
  });

  describe('Single Agent Operations', () => {
    it('should execute single operation successfully', async () => {
      const result = await asyncOps.executeAgentOperation('developer', 'implement_feature', {
        type: 'fast',
        description: 'Create user service'
      });

      expect(result.status).toBe('completed');
      expect(result.result.result).toContain('Fast implement_feature completed');
      expect(result.result.agent).toBe('developer');
    });

    it('should handle operation errors gracefully', async () => {
      const result = await asyncOps.executeAgentOperation('guardian', 'security_scan', {
        type: 'error'
      });

      expect(result.status).toBe('failed');
      expect(result.error.message).toContain('Operation security_scan failed');
    });

    it('should timeout long-running operations', async () => {
      const promise = asyncOps.executeAgentOperation('architect', 'design_system', {
        type: 'timeout'
      });

      // Wait a bit then cancel to simulate timeout
      setTimeout(() => {
        asyncOps.cancelOperation(asyncOps.getPendingOperations()[0]);
      }, 100);

      const result = await promise;
      expect(result.status).toBe('failed');
    });

    it('should track operation metadata', async () => {
      const startTime = Date.now();
      
      const result = await asyncOps.executeAgentOperation('qa', 'run_tests', {
        type: 'fast',
        testSuite: 'unit_tests'
      });

      const endTime = Date.now();
      const duration = endTime - startTime;

      expect(result.operationId).toBeDefined();
      expect(result.operationId).toContain('qa_run_tests');
      expect(duration).toBeLessThan(1000); // Fast operation
    });
  });

  describe('Concurrent Operations', () => {
    it('should execute multiple operations concurrently', async () => {
      const operations = [
        { agentId: 'scout', operation: 'analyze_code', input: { type: 'fast' } },
        { agentId: 'developer', operation: 'implement_feature', input: { type: 'fast' } },
        { agentId: 'qa', operation: 'run_tests', input: { type: 'fast' } }
      ];

      const startTime = Date.now();
      const results = await asyncOps.executeMultipleOperations(operations);
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(3);
      expect(results.every(r => r.status === 'completed')).toBe(true);
      expect(duration).toBeLessThan(500); // Should be concurrent, not sequential
    });

    it('should handle mixed success and failure in concurrent operations', async () => {
      const operations = [
        { agentId: 'scout', operation: 'analyze_code', input: { type: 'fast' } },
        { agentId: 'guardian', operation: 'security_scan', input: { type: 'error' } },
        { agentId: 'qa', operation: 'run_tests', input: { type: 'fast' } }
      ];

      const results = await asyncOps.executeMultipleOperations(operations);

      expect(results).toHaveLength(3);
      expect(results.filter(r => r.status === 'completed')).toHaveLength(2);
      expect(results.filter(r => r.status === 'failed')).toHaveLength(1);
    });

    it('should execute operations with different durations', async () => {
      const operations = [
        { agentId: 'agent1', operation: 'fast_op', input: { type: 'fast' } },
        { agentId: 'agent2', operation: 'slow_op', input: { type: 'slow' } },
        { agentId: 'agent3', operation: 'variable_op', input: { type: 'variable' } }
      ];

      const results = await asyncOps.executeMultipleOperations(operations);

      expect(results).toHaveLength(3);
      expect(results.every(r => r.status === 'completed')).toBe(true);
    });
  });

  describe('Sequential Operations', () => {
    it('should execute operations in sequence', async () => {
      const operations = [
        { agentId: 'scout', operation: 'analyze', input: { type: 'fast', step: 1 } },
        { agentId: 'architect', operation: 'design', input: { type: 'fast', step: 2 } },
        { agentId: 'developer', operation: 'implement', input: { type: 'fast', step: 3 } }
      ];

      const startTime = Date.now();
      const results = await asyncOps.executeSequentialOperations(operations);
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(3);
      expect(results.every(r => r.status === 'completed')).toBe(true);
      expect(duration).toBeGreaterThan(150); // Should be sequential (3 * 50ms min)
    });

    it('should stop sequence on critical failure', async () => {
      const operations = [
        { agentId: 'scout', operation: 'analyze', input: { type: 'fast' } },
        { agentId: 'guardian', operation: 'validate', input: { type: 'error', critical: true } },
        { agentId: 'developer', operation: 'implement', input: { type: 'fast' } }
      ];

      const results = await asyncOps.executeSequentialOperations(operations);

      expect(results).toHaveLength(2); // Should stop after critical failure
      expect(results[0].status).toBe('completed');
      expect(results[1].status).toBe('failed');
    });

    it('should continue sequence on non-critical failure', async () => {
      const operations = [
        { agentId: 'scout', operation: 'analyze', input: { type: 'fast' } },
        { agentId: 'guardian', operation: 'validate', input: { type: 'error', critical: false } },
        { agentId: 'developer', operation: 'implement', input: { type: 'fast' } }
      ];

      const results = await asyncOps.executeSequentialOperations(operations);

      expect(results).toHaveLength(3); // Should continue despite non-critical failure
      expect(results[0].status).toBe('completed');
      expect(results[1].status).toBe('failed');
      expect(results[2].status).toBe('completed');
    });
  });

  describe('Retry Logic', () => {
    it('should retry failed operations', async () => {
      let attemptCount = 0;
      
      // Mock operation that fails first two times, succeeds third time
      vi.spyOn(asyncOps as any, 'performAsyncOperation').mockImplementation(async () => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error(`Attempt ${attemptCount} failed`);
        }
        return { result: 'Success on third attempt', attempt: attemptCount };
      });

      const result = await asyncOps.executeWithRetry('developer', 'implement_feature', {}, 3);

      expect(result.status).toBe('completed');
      expect(result.result.result).toBe('Success on third attempt');
      expect(attemptCount).toBe(3);
    });

    it('should fail after max retries exceeded', async () => {
      vi.spyOn(asyncOps as any, 'performAsyncOperation').mockImplementation(async () => {
        throw new Error('Persistent failure');
      });

      const result = await asyncOps.executeWithRetry('guardian', 'security_scan', {}, 2);

      expect(result.status).toBe('failed_after_retries');
      expect(result.error.message).toBe('Persistent failure');
    });

    it('should use exponential backoff between retries', async () => {
      let attemptTimes: number[] = [];
      
      vi.spyOn(asyncOps as any, 'performAsyncOperation').mockImplementation(async () => {
        attemptTimes.push(Date.now());
        throw new Error('Retry test');
      });

      const startTime = Date.now();
      await asyncOps.executeWithRetry('developer', 'test_operation', {}, 3);
      
      // Check that delays increase exponentially (approximately)
      expect(attemptTimes).toHaveLength(3);
      
      if (attemptTimes.length >= 2) {
        const delay1 = attemptTimes[1] - attemptTimes[0];
        expect(delay1).toBeGreaterThan(900); // ~1000ms delay
      }
      
      if (attemptTimes.length >= 3) {
        const delay2 = attemptTimes[2] - attemptTimes[1];
        expect(delay2).toBeGreaterThan(1900); // ~2000ms delay
      }
    });
  });

  describe('Operation Management', () => {
    it('should track pending operations', async () => {
      const promise1 = asyncOps.executeAgentOperation('agent1', 'slow_op', { type: 'slow' });
      const promise2 = asyncOps.executeAgentOperation('agent2', 'slow_op', { type: 'slow' });

      const pending = asyncOps.getPendingOperations();
      expect(pending).toHaveLength(2);
      expect(pending.some(id => id.includes('agent1'))).toBe(true);
      expect(pending.some(id => id.includes('agent2'))).toBe(true);

      // Cancel operations to clean up
      asyncOps.cancelAllOperations();
      
      await expect(promise1).resolves.toEqual(expect.objectContaining({ status: 'failed' }));
      await expect(promise2).resolves.toEqual(expect.objectContaining({ status: 'failed' }));
    });

    it('should cancel specific operations', async () => {
      const promise = asyncOps.executeAgentOperation('agent', 'long_running', { type: 'slow' });
      
      const pending = asyncOps.getPendingOperations();
      expect(pending).toHaveLength(1);
      
      const cancelled = asyncOps.cancelOperation(pending[0]);
      expect(cancelled).toBe(true);
      
      const result = await promise;
      expect(result.status).toBe('failed');
    });

    it('should cancel all operations', async () => {
      const promises = [
        asyncOps.executeAgentOperation('agent1', 'op1', { type: 'slow' }),
        asyncOps.executeAgentOperation('agent2', 'op2', { type: 'slow' }),
        asyncOps.executeAgentOperation('agent3', 'op3', { type: 'slow' })
      ];

      expect(asyncOps.getPendingOperations()).toHaveLength(3);

      const cancelledCount = asyncOps.cancelAllOperations();
      expect(cancelledCount).toBe(3);
      expect(asyncOps.getPendingOperations()).toHaveLength(0);

      const results = await Promise.all(promises);
      expect(results.every(r => r.status === 'failed')).toBe(true);
    });

    it('should wait for all operations to complete', async () => {
      // Start multiple operations
      asyncOps.executeAgentOperation('agent1', 'op1', { type: 'fast' });
      asyncOps.executeAgentOperation('agent2', 'op2', { type: 'variable' });
      asyncOps.executeAgentOperation('agent3', 'op3', { type: 'fast' });

      const results = await asyncOps.waitForAllOperations();

      expect(results).toHaveLength(3);
      expect(results.every(r => r.status === 'fulfilled')).toBe(true);
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle many concurrent operations efficiently', async () => {
      const operationCount = 50;
      const operations = Array.from({ length: operationCount }, (_, i) => ({
        agentId: `agent${i % 5}`,
        operation: `operation${i}`,
        input: { type: 'fast', index: i }
      }));

      const startTime = Date.now();
      const results = await asyncOps.executeMultipleOperations(operations);
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(operationCount);
      expect(results.every(r => r.status === 'completed')).toBe(true);
      expect(duration).toBeLessThan(2000); // Should complete quickly due to concurrency
    });

    it('should handle operations with varying durations', async () => {
      const operations = Array.from({ length: 10 }, (_, i) => ({
        agentId: `agent${i}`,
        operation: `operation${i}`,
        input: { type: 'variable' }
      }));

      const results = await asyncOps.executeMultipleOperations(operations);

      expect(results).toHaveLength(10);
      expect(results.every(r => r.status === 'completed')).toBe(true);
    });

    it('should maintain performance under stress', async () => {
      const stressTestPromises = [];
      
      // Run multiple concurrent test batches
      for (let batch = 0; batch < 5; batch++) {
        const batchPromise = asyncOps.executeMultipleOperations([
          { agentId: `batch${batch}_agent1`, operation: 'test', input: { type: 'fast' } },
          { agentId: `batch${batch}_agent2`, operation: 'test', input: { type: 'variable' } },
          { agentId: `batch${batch}_agent3`, operation: 'test', input: { type: 'fast' } }
        ]);
        stressTestPromises.push(batchPromise);
      }

      const startTime = Date.now();
      const allResults = await Promise.all(stressTestPromises);
      const duration = Date.now() - startTime;

      expect(allResults).toHaveLength(5);
      expect(allResults.flat().every(r => r.status === 'completed')).toBe(true);
      expect(duration).toBeLessThan(3000);
    });
  });

  describe('Error Recovery and Resilience', () => {
    it('should handle partial failures in concurrent operations', async () => {
      const operations = [
        { agentId: 'reliable1', operation: 'test', input: { type: 'fast' } },
        { agentId: 'unreliable', operation: 'test', input: { type: 'error' } },
        { agentId: 'reliable2', operation: 'test', input: { type: 'fast' } },
        { agentId: 'unreliable2', operation: 'test', input: { type: 'error' } },
        { agentId: 'reliable3', operation: 'test', input: { type: 'fast' } }
      ];

      const results = await asyncOps.executeMultipleOperations(operations);

      expect(results).toHaveLength(5);
      expect(results.filter(r => r.status === 'completed')).toHaveLength(3);
      expect(results.filter(r => r.status === 'failed')).toHaveLength(2);
    });

    it('should recover gracefully from resource constraints', async () => {
      // Simulate resource-constrained operations
      const heavyOperations = Array.from({ length: 20 }, (_, i) => ({
        agentId: `heavy_agent${i}`,
        operation: 'heavy_computation',
        input: { type: 'variable', load: 'high' }
      }));

      const results = await asyncOps.executeMultipleOperations(heavyOperations);

      expect(results).toHaveLength(20);
      expect(results.every(r => r.status === 'completed')).toBe(true);
    });
  });
});