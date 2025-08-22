/**
 * External Dependencies Mocking Tests
 * Comprehensive tests for mocking external services, APIs, and dependencies
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { 
  createMockConfig, 
  mockFetch, 
  mockSuccessfulFetch, 
  mockFailedFetch,
  MockWebSocket,
  mockFileSystem,
  mockTimers,
  mockConsole
} from './test-helpers.js';
import { Config } from '@google/gemini-cli-core';

// Mock implementations for various external services
class ExternalServiceMocker {
  private activeMocks: Map<string, any> = new Map();
  private originalImplementations: Map<string, any> = new Map();

  /**
   * Mock Google Gemini API
   */
  mockGeminiAPI(responses: any[] = []): void {
    const mockResponses = responses.length > 0 ? responses : [
      {
        candidates: [{
          content: {
            parts: [{ text: 'Mocked Gemini response' }]
          }
        }],
        usageMetadata: {
          promptTokenCount: 10,
          candidatesTokenCount: 20,
          totalTokenCount: 30
        }
      }
    ];

    let responseIndex = 0;
    const mockFetch = vi.fn().mockImplementation(() => 
      Promise.resolve({
        ok: true,
        json: async () => mockResponses[responseIndex++ % mockResponses.length]
      })
    );

    global.fetch = mockFetch;
    this.activeMocks.set('gemini-api', mockFetch);
  }

  /**
   * Mock file system operations
   */
  mockFileSystemOperations(): any {
    const mockFs = mockFileSystem();
    
    // Pre-populate with some test files
    mockFs.setFile('/test/project/package.json', JSON.stringify({
      name: 'test-project',
      version: '1.0.0',
      dependencies: {
        'react': '^18.0.0',
        'typescript': '^5.0.0'
      }
    }));

    mockFs.setFile('/test/project/src/index.ts', 'export default function main() {}');
    mockFs.setFile('/test/project/README.md', '# Test Project\nThis is a test project.');

    this.activeMocks.set('filesystem', mockFs);
    return mockFs;
  }

  /**
   * Mock Git operations
   */
  mockGitOperations(): void {
    const mockGitCommands = {
      'git status': 'On branch main\nnothing to commit, working tree clean',
      'git diff': '',
      'git log --oneline -10': '1a2b3c4 Initial commit\n5d6e7f8 Add README',
      'git branch': '* main\n  develop\n  feature/test',
      'git remote -v': 'origin  https://github.com/test/repo.git (fetch)\norigin  https://github.com/test/repo.git (push)'
    };

    const mockExec = vi.fn().mockImplementation((command: string) => {
      const response = mockGitCommands[command as keyof typeof mockGitCommands];
      if (response !== undefined) {
        return Promise.resolve({ stdout: response, stderr: '' });
      }
      return Promise.reject(new Error(`Unknown git command: ${command}`));
    });

    this.activeMocks.set('git', mockExec);
  }

  /**
   * Mock npm/package manager operations
   */
  mockPackageManager(): void {
    const mockNpmCommands = {
      'npm test': 'All tests passed (25 tests)',
      'npm run build': 'Build completed successfully',
      'npm run lint': 'No linting errors found',
      'npm install': 'Dependencies installed successfully',
      'npm outdated': 'All packages are up to date'
    };

    const mockExec = vi.fn().mockImplementation((command: string) => {
      const response = mockNpmCommands[command as keyof typeof mockNpmCommands];
      if (response !== undefined) {
        return Promise.resolve({ stdout: response, stderr: '' });
      }
      return Promise.reject(new Error(`Unknown npm command: ${command}`));
    });

    this.activeMocks.set('npm', mockExec);
  }

  /**
   * Mock Docker operations
   */
  mockDockerOperations(): void {
    const mockDockerCommands = {
      'docker ps': 'CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES',
      'docker images': 'REPOSITORY   TAG       IMAGE ID   CREATED   SIZE',
      'docker build': 'Successfully built abc123def456',
      'docker run': 'Container started successfully'
    };

    const mockExec = vi.fn().mockImplementation((command: string) => {
      const baseCommand = command.split(' ').slice(0, 2).join(' ');
      const response = mockDockerCommands[baseCommand as keyof typeof mockDockerCommands];
      if (response !== undefined) {
        return Promise.resolve({ stdout: response, stderr: '' });
      }
      return Promise.reject(new Error(`Unknown docker command: ${command}`));
    });

    this.activeMocks.set('docker', mockExec);
  }

  /**
   * Mock database connections
   */
  mockDatabaseOperations(): any {
    const mockDb = {
      connect: vi.fn().mockResolvedValue(true),
      disconnect: vi.fn().mockResolvedValue(true),
      query: vi.fn().mockImplementation((sql: string) => {
        if (sql.toLowerCase().includes('select')) {
          return Promise.resolve([
            { id: 1, name: 'Test User', email: 'test@example.com' },
            { id: 2, name: 'Jane Doe', email: 'jane@example.com' }
          ]);
        }
        if (sql.toLowerCase().includes('insert')) {
          return Promise.resolve({ insertId: 3, affectedRows: 1 });
        }
        if (sql.toLowerCase().includes('update')) {
          return Promise.resolve({ affectedRows: 1 });
        }
        if (sql.toLowerCase().includes('delete')) {
          return Promise.resolve({ affectedRows: 1 });
        }
        return Promise.resolve({ message: 'Query executed' });
      }),
      transaction: vi.fn().mockImplementation(async (callback) => {
        return await callback(mockDb);
      })
    };

    this.activeMocks.set('database', mockDb);
    return mockDb;
  }

  /**
   * Mock Redis/Cache operations
   */
  mockCacheOperations(): any {
    const cache: Map<string, any> = new Map();
    
    const mockCache = {
      get: vi.fn().mockImplementation((key: string) => {
        return Promise.resolve(cache.get(key) || null);
      }),
      set: vi.fn().mockImplementation((key: string, value: any, ttl?: number) => {
        cache.set(key, value);
        if (ttl) {
          setTimeout(() => cache.delete(key), ttl * 1000);
        }
        return Promise.resolve('OK');
      }),
      del: vi.fn().mockImplementation((key: string) => {
        const existed = cache.has(key);
        cache.delete(key);
        return Promise.resolve(existed ? 1 : 0);
      }),
      exists: vi.fn().mockImplementation((key: string) => {
        return Promise.resolve(cache.has(key) ? 1 : 0);
      }),
      keys: vi.fn().mockImplementation((pattern: string) => {
        const allKeys = Array.from(cache.keys());
        if (pattern === '*') return Promise.resolve(allKeys);
        const regex = new RegExp(pattern.replace('*', '.*'));
        return Promise.resolve(allKeys.filter(key => regex.test(key)));
      }),
      flushall: vi.fn().mockImplementation(() => {
        cache.clear();
        return Promise.resolve('OK');
      })
    };

    this.activeMocks.set('cache', mockCache);
    return mockCache;
  }

  /**
   * Mock external API services
   */
  mockExternalAPIs(): void {
    const mockApiResponses = {
      'https://api.github.com': {
        user: { login: 'testuser', id: 12345, avatar_url: 'https://example.com/avatar.jpg' },
        repos: [
          { name: 'test-repo', full_name: 'testuser/test-repo', stars: 42 }
        ]
      },
      'https://jsonplaceholder.typicode.com': {
        posts: [
          { id: 1, title: 'Test Post', body: 'Test content', userId: 1 }
        ],
        users: [
          { id: 1, name: 'Test User', email: 'test@example.com' }
        ]
      },
      'https://httpbin.org': {
        get: { args: {}, headers: {}, origin: '127.0.0.1', url: 'https://httpbin.org/get' }
      }
    };

    const mockFetch = vi.fn().mockImplementation((url: string) => {
      for (const [baseUrl, responses] of Object.entries(mockApiResponses)) {
        if (url.startsWith(baseUrl)) {
          const path = url.replace(baseUrl, '').split('/').filter(Boolean)[0] || 'default';
          const response = responses[path as keyof typeof responses] || { error: 'Not found' };
          
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => response,
            text: async () => JSON.stringify(response)
          });
        }
      }
      
      return Promise.reject(new Error(`Unmocked URL: ${url}`));
    });

    global.fetch = mockFetch;
    this.activeMocks.set('external-apis', mockFetch);
  }

  /**
   * Mock WebSocket connections
   */
  mockWebSocketConnections(): any {
    const mockWs = new MockWebSocket('ws://test-server:8080');
    
    // Add some test message handlers
    mockWs.on('connection', () => {
      console.log('Mock WebSocket connected');
    });

    this.activeMocks.set('websocket', mockWs);
    return mockWs;
  }

  /**
   * Mock environment variables
   */
  mockEnvironmentVariables(envVars: Record<string, string>): void {
    const originalEnv = { ...process.env };
    this.originalImplementations.set('process.env', originalEnv);

    Object.assign(process.env, envVars);
    this.activeMocks.set('environment', envVars);
  }

  /**
   * Mock system commands
   */
  mockSystemCommands(): void {
    const mockCommands = {
      'ps aux': 'USER  PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND',
      'df -h': 'Filesystem      Size  Used Avail Use% Mounted on',
      'free -h': '              total        used        free      shared  buff/cache   available',
      'uname -a': 'Linux test-system 5.4.0 #1 SMP x86_64 GNU/Linux',
      'whoami': 'testuser',
      'pwd': '/home/testuser/projects/test'
    };

    const mockExec = vi.fn().mockImplementation((command: string) => {
      const response = mockCommands[command as keyof typeof mockCommands];
      if (response !== undefined) {
        return Promise.resolve({ stdout: response, stderr: '' });
      }
      return Promise.reject(new Error(`Unknown system command: ${command}`));
    });

    this.activeMocks.set('system', mockExec);
  }

  /**
   * Get active mock for service
   */
  getMock(service: string): any {
    return this.activeMocks.get(service);
  }

  /**
   * Clear specific mock
   */
  clearMock(service: string): void {
    this.activeMocks.delete(service);
    
    // Restore original implementation if exists
    const original = this.originalImplementations.get(service);
    if (original && service === 'process.env') {
      process.env = original;
    }
  }

  /**
   * Clear all mocks
   */
  clearAllMocks(): void {
    this.activeMocks.clear();
    
    // Restore original implementations
    this.originalImplementations.forEach((original, service) => {
      if (service === 'process.env') {
        process.env = original;
      }
    });
    this.originalImplementations.clear();
  }

  /**
   * Get mock usage statistics
   */
  getMockStatistics(): any {
    const stats: any = {
      activeMocks: this.activeMocks.size,
      services: Array.from(this.activeMocks.keys()),
      callCounts: {}
    };

    this.activeMocks.forEach((mock, service) => {
      if (mock && typeof mock === 'function' && mock.mock) {
        stats.callCounts[service] = mock.mock.calls.length;
      }
    });

    return stats;
  }
}

describe('External Dependencies Mocking', () => {
  let mocker: ExternalServiceMocker;
  let consoleMock: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mocker = new ExternalServiceMocker();
    consoleMock = mockConsole();
  });

  afterEach(() => {
    mocker.clearAllMocks();
    consoleMock.restore();
    vi.restoreAllMocks();
  });

  describe('API Mocking', () => {
    it('should mock Gemini API responses', async () => {
      const customResponses = [
        {
          candidates: [{
            content: {
              parts: [{ text: 'Custom test response' }]
            }
          }]
        }
      ];

      mocker.mockGeminiAPI(customResponses);

      const response = await fetch('https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent');
      const data = await response.json();

      expect(data.candidates[0].content.parts[0].text).toBe('Custom test response');
    });

    it('should mock multiple external APIs', async () => {
      mocker.mockExternalAPIs();

      const githubResponse = await fetch('https://api.github.com/user');
      const githubData = await githubResponse.json();
      expect(githubData.login).toBe('testuser');

      const placeholderResponse = await fetch('https://jsonplaceholder.typicode.com/posts');
      const placeholderData = await placeholderResponse.json();
      expect(placeholderData[0].title).toBe('Test Post');
    });

    it('should handle API error scenarios', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          json: async () => ({ error: 'Not found' })
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ error: 'Internal server error' })
        });

      global.fetch = mockFetch;

      const response1 = await fetch('https://api.example.com/404');
      expect(response1.status).toBe(404);

      const response2 = await fetch('https://api.example.com/500');
      expect(response2.status).toBe(500);
    });

    it('should simulate API rate limiting', async () => {
      let callCount = 0;
      const mockFetch = vi.fn().mockImplementation(() => {
        callCount++;
        if (callCount > 3) {
          return Promise.resolve({
            ok: false,
            status: 429,
            json: async () => ({ error: 'Rate limit exceeded' })
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true, callNumber: callCount })
        });
      });

      global.fetch = mockFetch;

      // Make multiple requests
      for (let i = 0; i < 5; i++) {
        const response = await fetch('https://api.example.com/test');
        const data = await response.json();
        
        if (i < 3) {
          expect(response.ok).toBe(true);
          expect(data.success).toBe(true);
        } else {
          expect(response.status).toBe(429);
          expect(data.error).toBe('Rate limit exceeded');
        }
      }
    });
  });

  describe('File System Mocking', () => {
    it('should mock file system operations', () => {
      const mockFs = mocker.mockFileSystemOperations();

      expect(mockFs.hasFile('/test/project/package.json')).toBe(true);
      expect(mockFs.hasFile('/nonexistent/file.txt')).toBe(false);

      const packageJson = mockFs.getFile('/test/project/package.json');
      const parsed = JSON.parse(packageJson!);
      expect(parsed.name).toBe('test-project');
    });

    it('should simulate file creation and modification', () => {
      const mockFs = mocker.mockFileSystemOperations();

      mockFs.setFile('/test/new-file.txt', 'New file content');
      expect(mockFs.hasFile('/test/new-file.txt')).toBe(true);
      expect(mockFs.getFile('/test/new-file.txt')).toBe('New file content');

      mockFs.setFile('/test/new-file.txt', 'Modified content');
      expect(mockFs.getFile('/test/new-file.txt')).toBe('Modified content');
    });

    it('should handle file system errors', () => {
      const mockFs = mocker.mockFileSystemOperations();

      expect(() => {
        mockFs.getFile('/nonexistent/file.txt');
      }).toThrow();
    });
  });

  describe('Database Mocking', () => {
    it('should mock database operations', async () => {
      const mockDb = mocker.mockDatabaseOperations();

      await mockDb.connect();
      expect(mockDb.connect).toHaveBeenCalled();

      const users = await mockDb.query('SELECT * FROM users');
      expect(users).toHaveLength(2);
      expect(users[0].name).toBe('Test User');

      const insertResult = await mockDb.query('INSERT INTO users (name, email) VALUES (?, ?)', ['New User', 'new@example.com']);
      expect(insertResult.insertId).toBe(3);
      expect(insertResult.affectedRows).toBe(1);
    });

    it('should mock database transactions', async () => {
      const mockDb = mocker.mockDatabaseOperations();

      const result = await mockDb.transaction(async (tx: any) => {
        await tx.query('INSERT INTO users (name) VALUES (?)', ['Transaction User']);
        await tx.query('UPDATE users SET email = ? WHERE id = ?', ['tx@example.com', 1]);
        return 'Transaction completed';
      });

      expect(result).toBe('Transaction completed');
      expect(mockDb.transaction).toHaveBeenCalled();
    });

    it('should simulate database connection failures', async () => {
      const mockDb = mocker.mockDatabaseOperations();
      mockDb.connect.mockRejectedValueOnce(new Error('Connection failed'));

      await expect(mockDb.connect()).rejects.toThrow('Connection failed');
    });
  });

  describe('Cache Mocking', () => {
    it('should mock cache operations', async () => {
      const mockCache = mocker.mockCacheOperations();

      await mockCache.set('test-key', 'test-value');
      const value = await mockCache.get('test-key');
      expect(value).toBe('test-value');

      const exists = await mockCache.exists('test-key');
      expect(exists).toBe(1);

      await mockCache.del('test-key');
      const deletedValue = await mockCache.get('test-key');
      expect(deletedValue).toBeNull();
    });

    it('should mock cache patterns and bulk operations', async () => {
      const mockCache = mocker.mockCacheOperations();

      await mockCache.set('user:1', 'User 1');
      await mockCache.set('user:2', 'User 2');
      await mockCache.set('session:abc', 'Session data');

      const userKeys = await mockCache.keys('user:*');
      expect(userKeys).toHaveLength(2);
      expect(userKeys).toContain('user:1');
      expect(userKeys).toContain('user:2');

      await mockCache.flushall();
      const allKeys = await mockCache.keys('*');
      expect(allKeys).toHaveLength(0);
    });

    it('should simulate cache TTL expiration', async () => {
      const mockCache = mocker.mockCacheOperations();
      const timers = mockTimers();

      await mockCache.set('temp-key', 'temp-value', 1); // 1 second TTL

      let value = await mockCache.get('temp-key');
      expect(value).toBe('temp-value');

      timers.tick(1500); // Advance time past TTL

      value = await mockCache.get('temp-key');
      expect(value).toBeNull();

      timers.restore();
    });
  });

  describe('WebSocket Mocking', () => {
    it('should mock WebSocket connections', () => {
      const mockWs = mocker.mockWebSocketConnections();

      expect(mockWs).toBeDefined();
      expect(mockWs.url).toBe('ws://test-server:8080');

      const messageHandler = vi.fn();
      mockWs.on('message', messageHandler);

      mockWs.send('test message');
      expect(mockWs.sentMessages).toContain('test message');
    });

    it('should simulate WebSocket events', () => {
      const mockWs = mocker.mockWebSocketConnections();

      const openHandler = vi.fn();
      const closeHandler = vi.fn();
      const errorHandler = vi.fn();

      mockWs.on('open', openHandler);
      mockWs.on('close', closeHandler);
      mockWs.on('error', errorHandler);

      // Simulate connection events
      mockWs.emit('open');
      expect(openHandler).toHaveBeenCalled();

      mockWs.close();
      expect(mockWs.readyState).toBe(WebSocket.CLOSED);

      mockWs.simulateError(new Error('Connection error'));
      expect(errorHandler).toHaveBeenCalledWith(expect.any(Error));
    });
  });

  describe('Environment and System Mocking', () => {
    it('should mock environment variables', () => {
      const originalEnv = process.env.NODE_ENV;

      mocker.mockEnvironmentVariables({
        NODE_ENV: 'test',
        API_KEY: 'test-api-key',
        DEBUG: 'true'
      });

      expect(process.env.NODE_ENV).toBe('test');
      expect(process.env.API_KEY).toBe('test-api-key');
      expect(process.env.DEBUG).toBe('true');

      mocker.clearMock('process.env');
      // Should restore original or be cleaned up
    });

    it('should mock system commands', async () => {
      mocker.mockSystemCommands();
      const mockExec = mocker.getMock('system');

      const result = await mockExec('whoami');
      expect(result.stdout).toBe('testuser');

      const psResult = await mockExec('ps aux');
      expect(psResult.stdout).toContain('USER  PID');

      await expect(mockExec('unknown-command')).rejects.toThrow('Unknown system command');
    });
  });

  describe('Command Line Tools Mocking', () => {
    it('should mock Git operations', async () => {
      mocker.mockGitOperations();
      const mockGit = mocker.getMock('git');

      const statusResult = await mockGit('git status');
      expect(statusResult.stdout).toContain('working tree clean');

      const branchResult = await mockGit('git branch');
      expect(branchResult.stdout).toContain('main');
      expect(branchResult.stdout).toContain('develop');
    });

    it('should mock npm operations', async () => {
      mocker.mockPackageManager();
      const mockNpm = mocker.getMock('npm');

      const testResult = await mockNpm('npm test');
      expect(testResult.stdout).toContain('All tests passed');

      const buildResult = await mockNpm('npm run build');
      expect(buildResult.stdout).toContain('Build completed');
    });

    it('should mock Docker operations', async () => {
      mocker.mockDockerOperations();
      const mockDocker = mocker.getMock('docker');

      const psResult = await mockDocker('docker ps');
      expect(psResult.stdout).toContain('CONTAINER ID');

      const buildResult = await mockDocker('docker build -t test:latest .');
      expect(buildResult.stdout).toContain('Successfully built');
    });
  });

  describe('Mock Management', () => {
    it('should track active mocks', () => {
      mocker.mockGeminiAPI();
      mocker.mockFileSystemOperations();
      mocker.mockDatabaseOperations();

      const stats = mocker.getMockStatistics();
      expect(stats.activeMocks).toBe(3);
      expect(stats.services).toContain('gemini-api');
      expect(stats.services).toContain('filesystem');
      expect(stats.services).toContain('database');
    });

    it('should clear specific mocks', () => {
      mocker.mockGeminiAPI();
      mocker.mockFileSystemOperations();

      expect(mocker.getMockStatistics().activeMocks).toBe(2);

      mocker.clearMock('gemini-api');
      expect(mocker.getMockStatistics().activeMocks).toBe(1);
      expect(mocker.getMockStatistics().services).not.toContain('gemini-api');
    });

    it('should clear all mocks', () => {
      mocker.mockGeminiAPI();
      mocker.mockFileSystemOperations();
      mocker.mockDatabaseOperations();
      mocker.mockCacheOperations();

      expect(mocker.getMockStatistics().activeMocks).toBe(4);

      mocker.clearAllMocks();
      expect(mocker.getMockStatistics().activeMocks).toBe(0);
    });

    it('should provide mock usage statistics', async () => {
      mocker.mockExternalAPIs();
      
      // Make some API calls
      await fetch('https://api.github.com/user');
      await fetch('https://api.github.com/repos');
      await fetch('https://jsonplaceholder.typicode.com/posts');

      const stats = mocker.getMockStatistics();
      expect(stats.callCounts['external-apis']).toBe(3);
    });
  });

  describe('Integration Testing', () => {
    it('should mock multiple services for integration tests', async () => {
      // Set up complete mock environment
      mocker.mockGeminiAPI();
      mocker.mockFileSystemOperations();
      mocker.mockDatabaseOperations();
      mocker.mockCacheOperations();
      mocker.mockEnvironmentVariables({ NODE_ENV: 'test' });

      const mockFs = mocker.getMock('filesystem');
      const mockDb = mocker.getMock('database');
      const mockCache = mocker.getMock('cache');

      // Simulate a complete workflow
      expect(mockFs.hasFile('/test/project/package.json')).toBe(true);

      await mockDb.connect();
      const users = await mockDb.query('SELECT * FROM users');
      expect(users).toBeDefined();

      await mockCache.set('users', JSON.stringify(users));
      const cachedUsers = await mockCache.get('users');
      expect(JSON.parse(cachedUsers)).toEqual(users);

      const apiResponse = await fetch('https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent');
      expect(apiResponse.ok).toBe(true);

      expect(process.env.NODE_ENV).toBe('test');
    });

    it('should handle complex error scenarios across services', async () => {
      mocker.mockDatabaseOperations();
      mocker.mockCacheOperations();

      const mockDb = mocker.getMock('database');
      const mockCache = mocker.getMock('cache');

      // Simulate database failure
      mockDb.query.mockRejectedValueOnce(new Error('Database connection lost'));

      await expect(mockDb.query('SELECT * FROM users')).rejects.toThrow('Database connection lost');

      // Simulate cache fallback
      await mockCache.set('fallback-data', 'cached-response');
      const fallbackData = await mockCache.get('fallback-data');
      expect(fallbackData).toBe('cached-response');
    });
  });
});