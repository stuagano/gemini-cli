/**
 * Comprehensive Test Utilities and Helpers
 * Provides shared utilities for testing agent components and core functionality
 */

import { vi } from 'vitest';
import { Config } from '@google/gemini-cli-core';
import { EventEmitter } from 'events';

/**
 * Mock Config for testing
 */
export function createMockConfig(overrides: Partial<Config> = {}): Config {
  return {
    apiKey: 'test-api-key',
    model: 'gemini-pro',
    maxTokens: 1000,
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    safetySettings: [],
    generationConfig: {},
    systemInstruction: undefined,
    toolConfig: undefined,
    cachedContent: undefined,
    requestOptions: {},
    ...overrides
  } as Config;
}

/**
 * Mock EventEmitter with tracking
 */
export class MockEventEmitter extends EventEmitter {
  public emittedEvents: Array<{ event: string; args: any[] }> = [];

  emit(event: string | symbol, ...args: any[]): boolean {
    this.emittedEvents.push({ event: event.toString(), args });
    return super.emit(event, ...args);
  }

  getEmittedEvents(eventName?: string): Array<{ event: string; args: any[] }> {
    if (eventName) {
      return this.emittedEvents.filter(e => e.event === eventName);
    }
    return this.emittedEvents;
  }

  clearEmittedEvents(): void {
    this.emittedEvents = [];
  }
}

/**
 * Mock fetch responses
 */
export function mockFetch(responses: Array<{ url?: string | RegExp; response: any }>) {
  const mockFn = vi.fn();
  
  responses.forEach((config, index) => {
    const matcher = config.url ? 
      (url: string) => {
        if (typeof config.url === 'string') {
          return url.includes(config.url);
        }
        return config.url.test(url);
      } : 
      () => true;

    mockFn.mockImplementation((url: string) => {
      if (matcher(url)) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => config.response,
          text: async () => JSON.stringify(config.response),
          ...config.response.fetchProps
        });
      }
      return Promise.reject(new Error(`No mock response for: ${url}`));
    });
  });

  global.fetch = mockFn;
  return mockFn;
}

/**
 * Mock successful API responses
 */
export function mockSuccessfulFetch(defaultResponse: any = { success: true }) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => defaultResponse,
    text: async () => JSON.stringify(defaultResponse)
  });
  return global.fetch as any;
}

/**
 * Mock failed API responses
 */
export function mockFailedFetch(error: string = 'Network error') {
  global.fetch = vi.fn().mockRejectedValue(new Error(error));
  return global.fetch as any;
}

/**
 * Mock console methods with tracking
 */
export function mockConsole() {
  const originalConsole = { ...console };
  const logs: Array<{ level: string; args: any[] }> = [];

  const mockMethods = ['log', 'error', 'warn', 'info', 'debug'] as const;
  
  mockMethods.forEach(method => {
    console[method] = vi.fn((...args: any[]) => {
      logs.push({ level: method, args });
    });
  });

  return {
    logs,
    restore: () => {
      Object.assign(console, originalConsole);
    },
    getLogs: (level?: string) => level ? logs.filter(l => l.level === level) : logs,
    clearLogs: () => logs.splice(0, logs.length)
  };
}

/**
 * Mock WebSocket for testing
 */
export class MockWebSocket extends EventEmitter {
  public readyState: number = WebSocket.CONNECTING;
  public url: string;
  public sentMessages: any[] = [];

  constructor(url: string) {
    super();
    this.url = url;
    
    // Simulate connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.emit('open');
    }, 0);
  }

  send(data: any): void {
    this.sentMessages.push(data);
    // Simulate message reception
    setTimeout(() => {
      this.emit('message', data);
    }, 0);
  }

  close(): void {
    this.readyState = WebSocket.CLOSED;
    this.emit('close');
  }

  // Mock error
  simulateError(error: Error): void {
    this.emit('error', error);
  }
}

/**
 * Mock timer utilities
 */
export function mockTimers() {
  vi.useFakeTimers();
  
  return {
    tick: (ms: number) => vi.advanceTimersByTime(ms),
    tickAsync: async (ms: number) => {
      vi.advanceTimersByTime(ms);
      await vi.runAllTimersAsync();
    },
    restore: () => vi.useRealTimers()
  };
}

/**
 * Mock file system operations
 */
export function mockFileSystem() {
  const files: Map<string, string> = new Map();
  
  const mockFs = {
    readFile: vi.fn((path: string) => {
      if (files.has(path)) {
        return Promise.resolve(files.get(path));
      }
      return Promise.reject(new Error(`File not found: ${path}`));
    }),
    
    writeFile: vi.fn((path: string, content: string) => {
      files.set(path, content);
      return Promise.resolve();
    }),
    
    exists: vi.fn((path: string) => {
      return Promise.resolve(files.has(path));
    }),
    
    mkdir: vi.fn(() => Promise.resolve()),
    
    readdir: vi.fn((path: string) => {
      const pathFiles = Array.from(files.keys())
        .filter(f => f.startsWith(path))
        .map(f => f.replace(path + '/', '').split('/')[0])
        .filter((name, index, arr) => arr.indexOf(name) === index);
      return Promise.resolve(pathFiles);
    })
  };

  return {
    mockFs,
    setFile: (path: string, content: string) => files.set(path, content),
    getFile: (path: string) => files.get(path),
    hasFile: (path: string) => files.has(path),
    clearFiles: () => files.clear(),
    getAllFiles: () => new Map(files)
  };
}

/**
 * Agent test utilities
 */
export class AgentTestUtils {
  static createMockAgent(overrides: any = {}) {
    return {
      id: 'test-agent',
      name: 'Test Agent',
      status: 'ready',
      capabilities: ['test'],
      execute: vi.fn().mockResolvedValue({ success: true }),
      initialize: vi.fn().mockResolvedValue(undefined),
      shutdown: vi.fn().mockResolvedValue(undefined),
      ...overrides
    };
  }

  static createMockAgentResponse(overrides: any = {}) {
    return {
      agentId: 'test-agent',
      persona: 'test',
      result: { success: true },
      status: 'success' as const,
      executionTime: 100,
      ...overrides
    };
  }

  static createMockValidationIssue(overrides: any = {}) {
    return {
      id: 'test-issue-1',
      rule_id: 'test_rule',
      severity: 'warning' as const,
      category: 'quality' as const,
      title: 'Test Issue',
      description: 'Test description',
      file_path: '/test/file.ts',
      line_number: 10,
      auto_fixable: false,
      timestamp: new Date(),
      resolved: false,
      ...overrides
    };
  }
}

/**
 * Async test utilities
 */
export class AsyncTestUtils {
  /**
   * Wait for event to be emitted
   */
  static waitForEvent(emitter: EventEmitter, event: string, timeout: number = 1000): Promise<any> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Timeout waiting for event: ${event}`));
      }, timeout);

      emitter.once(event, (data) => {
        clearTimeout(timer);
        resolve(data);
      });
    });
  }

  /**
   * Wait for multiple events
   */
  static waitForEvents(emitter: EventEmitter, events: string[], timeout: number = 1000): Promise<any[]> {
    return Promise.all(events.map(event => this.waitForEvent(emitter, event, timeout)));
  }

  /**
   * Wait for condition to be true
   */
  static waitForCondition(
    condition: () => boolean, 
    timeout: number = 1000, 
    interval: number = 10
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const check = () => {
        if (condition()) {
          resolve();
        } else if (Date.now() - startTime > timeout) {
          reject(new Error('Timeout waiting for condition'));
        } else {
          setTimeout(check, interval);
        }
      };
      
      check();
    });
  }

  /**
   * Simulate async delay
   */
  static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Test performance utilities
 */
export class PerformanceTestUtils {
  /**
   * Measure execution time
   */
  static async measureTime<T>(fn: () => Promise<T>): Promise<{ result: T; time: number }> {
    const start = Date.now();
    const result = await fn();
    const time = Date.now() - start;
    return { result, time };
  }

  /**
   * Run performance test
   */
  static async runPerformanceTest(
    fn: () => Promise<any>,
    iterations: number = 10
  ): Promise<{
    average: number;
    min: number;
    max: number;
    total: number;
  }> {
    const times: number[] = [];
    
    for (let i = 0; i < iterations; i++) {
      const { time } = await this.measureTime(fn);
      times.push(time);
    }
    
    return {
      average: times.reduce((a, b) => a + b, 0) / times.length,
      min: Math.min(...times),
      max: Math.max(...times),
      total: times.reduce((a, b) => a + b, 0)
    };
  }
}

/**
 * Error testing utilities
 */
export class ErrorTestUtils {
  /**
   * Test that function throws expected error
   */
  static async expectThrows(
    fn: () => Promise<any> | any,
    expectedError?: string | RegExp | Error
  ): Promise<Error> {
    try {
      await fn();
      throw new Error('Expected function to throw');
    } catch (error) {
      if (expectedError) {
        if (typeof expectedError === 'string') {
          expect(error.message).toContain(expectedError);
        } else if (expectedError instanceof RegExp) {
          expect(error.message).toMatch(expectedError);
        } else if (expectedError instanceof Error) {
          expect(error.message).toBe(expectedError.message);
        }
      }
      return error as Error;
    }
  }

  /**
   * Test error recovery
   */
  static async testErrorRecovery<T>(
    fn: () => Promise<T>,
    expectedError: any,
    recoveryFn: () => Promise<T>
  ): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      expect(error).toEqual(expectedError);
      return await recoveryFn();
    }
  }
}

/**
 * Data generation utilities
 */
export class DataGenerators {
  /**
   * Generate random string
   */
  static randomString(length: number = 10): string {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Generate test file path
   */
  static testFilePath(ext: string = 'ts'): string {
    return `/test/files/${this.randomString(8)}.${ext}`;
  }

  /**
   * Generate mock validation issues
   */
  static mockValidationIssues(count: number): any[] {
    const severities = ['critical', 'error', 'warning', 'info'];
    const categories = ['security', 'performance', 'quality', 'architecture'];
    
    return Array.from({ length: count }, (_, index) => ({
      id: `issue-${index + 1}`,
      rule_id: `rule_${index + 1}`,
      severity: severities[index % severities.length],
      category: categories[index % categories.length],
      title: `Test Issue ${index + 1}`,
      description: `Description for issue ${index + 1}`,
      file_path: this.testFilePath(),
      line_number: Math.floor(Math.random() * 100) + 1,
      auto_fixable: Math.random() > 0.5,
      timestamp: new Date(),
      resolved: false
    }));
  }
}

/**
 * Setup test environment
 */
export function setupTestEnvironment() {
  const mocks = {
    console: mockConsole(),
    timers: mockTimers(),
    fileSystem: mockFileSystem(),
    config: createMockConfig()
  };

  // Setup global mocks
  mockSuccessfulFetch();

  return {
    ...mocks,
    cleanup: () => {
      mocks.console.restore();
      mocks.timers.restore();
      vi.restoreAllMocks();
    }
  };
}

/**
 * Test suite utilities
 */
export class TestSuiteUtils {
  /**
   * Run test with timeout
   */
  static withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('Test timeout')), timeout)
      )
    ]);
  }

  /**
   * Retry test on failure
   */
  static async withRetry<T>(
    fn: () => Promise<T>, 
    maxRetries: number = 3, 
    delay: number = 100
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        if (attempt < maxRetries) {
          await AsyncTestUtils.delay(delay);
        }
      }
    }
    
    throw lastError!;
  }
}

export default {
  createMockConfig,
  MockEventEmitter,
  mockFetch,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockConsole,
  MockWebSocket,
  mockTimers,
  mockFileSystem,
  AgentTestUtils,
  AsyncTestUtils,
  PerformanceTestUtils,
  ErrorTestUtils,
  DataGenerators,
  setupTestEnvironment,
  TestSuiteUtils
};