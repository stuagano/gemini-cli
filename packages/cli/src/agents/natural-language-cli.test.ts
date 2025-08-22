/**
 * Natural Language CLI Tests
 * Tests for natural language command processing and agent orchestration
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NaturalLanguageCLI } from './natural-language-cli.js';
import { Config } from '@google/gemini-cli-core';

// Mock dependencies
vi.mock('chalk', () => ({
  default: {
    blue: (text: string) => text,
    green: (text: string) => text,
    yellow: (text: string) => text,
    red: (text: string) => text,
    gray: (text: string) => text,
    cyan: (text: string) => text,
  }
}));

vi.mock('ora', () => ({
  default: vi.fn(() => ({
    start: vi.fn().mockReturnThis(),
    succeed: vi.fn().mockReturnThis(),
    fail: vi.fn().mockReturnThis(),
    text: ''
  }))
}));

vi.mock('ws', () => ({
  default: vi.fn()
}));

// Mock fetch
global.fetch = vi.fn();

describe('NaturalLanguageCLI', () => {
  let cli: NaturalLanguageCLI;
  let mockConfig: Config;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockConfig = {
      apiKey: 'test-key',
      model: 'gemini-pro',
      // Add other config properties as needed
    } as Config;

    cli = new NaturalLanguageCLI(mockConfig);
    
    // Mock console methods to reduce test noise
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cli.disconnect();
  });

  describe('Initialization', () => {
    it('should initialize with correct agent capabilities', () => {
      expect(cli).toBeDefined();
      expect(cli.isReady()).toBe(false);
    });

    it('should set up enhanced NLP parser', () => {
      // Parser should be initialized during construction
      const command = cli.parseCommand('test command');
      expect(command).toBeDefined();
      expect(command.raw).toBe('test command');
    });
  });

  describe('Command Parsing', () => {
    it('should parse simple commands', () => {
      const command = cli.parseCommand('create user authentication');
      
      expect(command.raw).toBe('create user authentication');
      expect(command.intent).toBeDefined();
      expect(command.confidence).toBeGreaterThan(0);
      expect(command.suggestedAgent).toBeDefined();
    });

    it('should parse commands with context', () => {
      const context = ['authentication', 'security'];
      const command = cli.parseCommand('add validation', context);
      
      expect(command.contextualEntities.length).toBeGreaterThanOrEqual(0);
      expect(command.semanticTokens.length).toBeGreaterThan(0);
    });

    it('should provide command suggestions', () => {
      const suggestions = cli.getCommandSuggestions('create auth', 3);
      
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0]).toHaveProperty('command');
      expect(suggestions[0]).toHaveProperty('confidence');
      expect(suggestions[0]).toHaveProperty('agent');
    });

    it('should analyze command clarity', () => {
      const command = cli.parseCommand('create comprehensive user authentication system');
      const analysis = cli.analyzeCommandClarity(command);
      
      expect(analysis).toHaveProperty('clarity');
      expect(analysis).toHaveProperty('score');
      expect(analysis).toHaveProperty('feedback');
    });
  });

  describe('Agent Routing', () => {
    beforeEach(() => {
      // Mock successful API responses
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          result: 'Mock agent response',
          execution_time_ms: 100
        })
      });
    });

    it('should route to single agent', async () => {
      const command = cli.parseCommandSimple('create unit tests for auth service');
      const responses = await cli.routeCommand(command);
      
      expect(responses).toHaveLength(1);
      expect(responses[0].agentId).toBe('qa');
      expect(responses[0].status).toBe('success');
    });

    it('should route to multiple agents for complex commands', async () => {
      const command = cli.parseCommandSimple('design and implement user management system');
      command.requiresMultiAgent = true;
      
      const responses = await cli.routeCommand(command);
      
      expect(responses.length).toBeGreaterThan(1);
      expect(responses.some(r => r.agentId === 'scout')).toBe(true);
      expect(responses.some(r => r.agentId === 'guardian')).toBe(true);
    });

    it('should handle Scout-first workflow', async () => {
      const command = cli.parseCommandSimple('implement payment processing');
      command.requiresMultiAgent = true;
      
      const responses = await cli.routeCommand(command);
      
      // First response should be from Scout
      expect(responses[0].agentId).toBe('scout');
    });

    it('should skip Scout when explicitly requested', async () => {
      const command = cli.parseCommandSimple('skip scout and implement feature');
      command.requiresMultiAgent = true;
      
      const responses = await cli.routeCommand(command);
      
      // Should not include Scout response
      expect(responses.some(r => r.agentId === 'scout')).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      (fetch as any).mockRejectedValue(new Error('Network error'));
      
      const command = cli.parseCommandSimple('test command');
      const responses = await cli.routeCommand(command);
      
      expect(responses).toHaveLength(1);
      expect(responses[0].status).toBe('success'); // Falls back to mock response
    });

    it('should handle malformed commands', () => {
      const command = cli.parseCommand('');
      
      expect(command.confidence).toBeLessThan(0.5);
      expect(command.suggestions.length).toBeGreaterThan(0);
    });
  });

  describe('Enhanced Processing', () => {
    beforeEach(() => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          result: 'Mock response'
        })
      });
    });

    it('should process commands with enhanced NLP', async () => {
      await expect(cli.processCommandEnhanced('create user authentication system')).resolves.toBeUndefined();
      
      // Should have called console.log for processing output
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Processing with Enhanced NLP:'),
        'create user authentication system'
      );
    });

    it('should show clarity analysis for ambiguous commands', async () => {
      await cli.processCommandEnhanced('fix this');
      
      // Should show clarity feedback
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Command interpretation needs clarification')
      );
    });

    it('should display entities found', async () => {
      await cli.processCommandEnhanced('create React application with TypeScript');
      
      // Should display found entities
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Entities found:')
      );
    });

    it('should show alternatives for ambiguous commands', async () => {
      await cli.processCommandEnhanced('review code');
      
      // Should show alternative interpretations
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Alternative interpretations:')
      );
    });
  });

  describe('Legacy Processing', () => {
    it('should process commands with legacy method', async () => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ result: 'Mock response' })
      });

      await expect(cli.processCommand('create user service')).resolves.toBeUndefined();
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Processing:'),
        'create user service'
      );
    });

    it('should show suggestions for low confidence commands', async () => {
      await cli.processCommand('do something');
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Low confidence')
      );
    });
  });

  describe('WebSocket Connection', () => {
    it('should attempt to connect to agent server', async () => {
      // Mock WebSocket success
      const mockWS = {
        on: vi.fn((event, callback) => {
          if (event === 'open') {
            setTimeout(callback, 0);
          }
        }),
        close: vi.fn()
      };
      
      const WS = vi.mocked(require('ws').default);
      WS.mockImplementation(() => mockWS);

      await expect(cli.connect()).resolves.toBeUndefined();
      expect(cli.isReady()).toBe(true);
    });

    it('should handle connection timeout', async () => {
      const mockWS = {
        on: vi.fn(),
        close: vi.fn()
      };
      
      const WS = vi.mocked(require('ws').default);
      WS.mockImplementation(() => mockWS);

      await expect(cli.connect()).rejects.toThrow('Connection timeout');
    });
  });

  describe('Message Handling', () => {
    it('should emit events for server messages', () => {
      const statusListener = vi.fn();
      const responseListener = vi.fn();
      
      cli.on('status', statusListener);
      cli.on('agent_response', responseListener);
      
      // Simulate message handling
      cli['handleServerMessage']({
        type: 'status_update',
        data: { status: 'processing' }
      });
      
      cli['handleServerMessage']({
        type: 'agent_response',
        data: { result: 'completed' }
      });
      
      expect(statusListener).toHaveBeenCalledWith({ status: 'processing' });
      expect(responseListener).toHaveBeenCalledWith({ result: 'completed' });
    });
  });

  describe('Response Display', () => {
    it('should format simple string results', () => {
      const responses = [{
        agentId: 'developer',
        persona: 'developer',
        result: 'Simple string result',
        status: 'success' as const
      }];
      
      cli['displayResponses'](responses);
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('DEVELOPER Agent:')
      );
    });

    it('should format complex object results', () => {
      const responses = [{
        agentId: 'scout',
        persona: 'scout',
        result: {
          duplicates_found: false,
          code_quality_score: 8.5,
          suggestions: ['Use existing utilities', 'Add tests']
        },
        status: 'success' as const,
        executionTime: 150
      }];
      
      cli['displayResponses'](responses);
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('SCOUT Agent:')
      );
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Execution time: 150ms')
      );
    });

    it('should display error responses', () => {
      const responses = [{
        agentId: 'guardian',
        persona: 'guardian',
        result: { error: 'Validation failed' },
        status: 'error' as const
      }];
      
      cli['displayResponses'](responses);
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Error: Validation failed')
      );
    });
  });

  describe('Mock Responses', () => {
    it('should provide appropriate mock responses', () => {
      const scoutMock = cli['getMockResponse']('scout', 'analyze');
      expect(scoutMock).toHaveProperty('duplicates_found');
      expect(scoutMock).toHaveProperty('code_quality_score');
      
      const architectMock = cli['getMockResponse']('architect', 'design');
      expect(architectMock).toHaveProperty('design_pattern');
      expect(architectMock).toHaveProperty('components');
      
      const guardianMock = cli['getMockResponse']('guardian', 'validate');
      expect(guardianMock).toHaveProperty('validation_passed');
      expect(guardianMock).toHaveProperty('security_score');
    });
  });

  describe('Suggestions', () => {
    it('should provide relevant suggestions based on input', () => {
      const checkSuggestions = cli['getSuggestions']('check for issues');
      expect(checkSuggestions.some(s => s.includes('duplicate'))).toBe(true);
      
      const createSuggestions = cli['getSuggestions']('create new feature');
      expect(createSuggestions.some(s => s.includes('tests'))).toBe(true);
      
      const reviewSuggestions = cli['getSuggestions']('review the code');
      expect(reviewSuggestions.some(s => s.includes('security'))).toBe(true);
    });

    it('should limit suggestion count', () => {
      const suggestions = cli['getSuggestions']('create build review check');
      expect(suggestions.length).toBeLessThanOrEqual(3);
    });
  });
});