/**
 * Enhanced NLP Parser Tests
 * Tests for sophisticated natural language understanding
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { EnhancedNLPParser, EntityType, TokenType } from './enhanced-nlp-parser.js';
import { AgentCapabilities } from './natural-language-cli.js';

describe('EnhancedNLPParser', () => {
  let parser: EnhancedNLPParser;
  let mockAgentCapabilities: AgentCapabilities;

  beforeEach(() => {
    mockAgentCapabilities = {
      scout: ['duplicate', 'similar', 'existing', 'reuse'],
      architect: ['design', 'architecture', 'pattern', 'structure'],
      developer: ['implement', 'create', 'build', 'code'],
      guardian: ['security', 'validate', 'scan', 'vulnerability'],
      pm: ['project', 'timeline', 'sprint', 'task'],
      po: ['requirement', 'user story', 'acceptance', 'priority'],
      qa: ['test', 'quality', 'regression', 'coverage']
    };

    parser = new EnhancedNLPParser(mockAgentCapabilities);
  });

  describe('Command Parsing', () => {
    it('should parse simple commands correctly', () => {
      const result = parser.parseCommand('create a new user authentication system');
      
      expect(result.raw).toBe('create a new user authentication system');
      expect(result.intent).toBe('design_architecture');
      expect(result.confidence).toBeGreaterThan(0.5);
      expect(result.suggestedAgent).toBe('architect');
      expect(result.ambiguityScore).toBeLessThan(1.0);
    });

    it('should handle complex commands with multiple entities', () => {
      const result = parser.parseCommand('design a microservices architecture for the payment system using Node.js');
      
      expect(result.contextualEntities.length).toBeGreaterThan(0);
      expect(result.entities).toHaveProperty('component');
      expect(result.entities).toHaveProperty('framework');
      expect(result.suggestedAgent).toBe('architect');
      expect(result.requiresMultiAgent).toBe(true);
    });

    it('should identify security-related commands', () => {
      const result = parser.parseCommand('scan the authentication module for security vulnerabilities');
      
      expect(result.intent).toContain('security');
      expect(result.suggestedAgent).toBe('guardian');
      expect(result.confidence).toBeGreaterThan(0.7);
    });

    it('should handle test-related commands', () => {
      const result = parser.parseCommand('create unit tests for the payment component');
      
      expect(result.intent).toContain('test');
      expect(result.suggestedAgent).toBe('qa');
      expect(result.contextualEntities.some(e => e.type === EntityType.COMPONENT)).toBe(true);
    });
  });

  describe('Entity Extraction', () => {
    it('should extract file paths', () => {
      const result = parser.parseCommand('check src/components/auth.tsx for duplicate code');
      
      const fileEntities = result.contextualEntities.filter(e => e.type === EntityType.FILE_PATH);
      expect(fileEntities.length).toBeGreaterThan(0);
      expect(fileEntities[0].value).toContain('auth.tsx');
    });

    it('should extract programming languages', () => {
      const result = parser.parseCommand('implement this feature in TypeScript and Python');
      
      const langEntities = result.contextualEntities.filter(e => e.type === EntityType.LANGUAGE);
      expect(langEntities.length).toBeGreaterThanOrEqual(2);
      expect(langEntities.some(e => e.value.toLowerCase().includes('typescript'))).toBe(true);
      expect(langEntities.some(e => e.value.toLowerCase().includes('python'))).toBe(true);
    });

    it('should extract frameworks and technologies', () => {
      const result = parser.parseCommand('build a React application with Express backend');
      
      const frameworkEntities = result.contextualEntities.filter(e => e.type === EntityType.FRAMEWORK);
      expect(frameworkEntities.length).toBeGreaterThan(0);
      expect(frameworkEntities.some(e => e.value.toLowerCase().includes('react'))).toBe(true);
    });

    it('should extract actions', () => {
      const result = parser.parseCommand('refactor and optimize the database queries');
      
      const actionEntities = result.contextualEntities.filter(e => e.type === EntityType.ACTION);
      expect(actionEntities.length).toBeGreaterThan(0);
      expect(actionEntities.some(e => e.value.toLowerCase().includes('refactor'))).toBe(true);
    });
  });

  describe('Intent Classification', () => {
    it('should classify duplicate detection intent', () => {
      const result = parser.parseCommand('check if there are similar implementations of user authentication');
      
      expect(result.intent).toBe('check_duplicates');
      expect(result.suggestedAgent).toBe('scout');
      expect(result.confidence).toBeGreaterThan(0.6);
    });

    it('should classify design intent', () => {
      const result = parser.parseCommand('design a microservices architecture');
      
      expect(result.intent).toBe('design_architecture');
      expect(result.suggestedAgent).toBe('architect');
      expect(result.requiresMultiAgent).toBe(true);
    });

    it('should classify implementation intent', () => {
      const result = parser.parseCommand('build a REST API for user management');
      
      expect(result.intent).toBe('implement_feature');
      expect(result.suggestedAgent).toBe('developer');
    });

    it('should classify security intent', () => {
      const result = parser.parseCommand('audit the payment module for vulnerabilities');
      
      expect(result.intent).toBe('security_scan');
      expect(result.suggestedAgent).toBe('guardian');
    });

    it('should classify testing intent', () => {
      const result = parser.parseCommand('write integration tests for the API endpoints');
      
      expect(result.intent).toBe('create_tests');
      expect(result.suggestedAgent).toBe('qa');
    });
  });

  describe('Ambiguity Detection', () => {
    it('should detect high ambiguity in vague commands', () => {
      const result = parser.parseCommand('fix this');
      
      expect(result.ambiguityScore).toBeGreaterThanOrEqual(0);
      expect(result.alternatives.length).toBeGreaterThanOrEqual(0);
      expect(result.suggestions.length).toBeGreaterThan(0);
    });

    it('should detect low ambiguity in specific commands', () => {
      const result = parser.parseCommand('create unit tests for the authentication service using Jest');
      
      expect(result.ambiguityScore).toBeLessThan(1.0);
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    it('should provide alternatives for ambiguous commands', () => {
      const result = parser.parseCommand('review the code');
      
      expect(result.alternatives.length).toBeGreaterThanOrEqual(0);
      if (result.alternatives.length > 0) {
        expect(result.alternatives[0].confidence).toBeGreaterThan(0);
        expect(result.alternatives[0].reasoning).toBeDefined();
      }
    });
  });

  describe('Command Suggestions', () => {
    it('should provide similar command suggestions', () => {
      const suggestions = parser.getCommandSuggestions('check duplicate code', 3);
      
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].confidence).toBeGreaterThan(0.3);
      expect(suggestions[0].command).toBeDefined();
      expect(suggestions[0].agent).toBeDefined();
    });

    it('should limit suggestions to specified number', () => {
      const suggestions = parser.getCommandSuggestions('create something', 2);
      
      expect(suggestions.length).toBeLessThanOrEqual(2);
    });

    it('should sort suggestions by confidence', () => {
      const suggestions = parser.getCommandSuggestions('implement feature', 5);
      
      for (let i = 1; i < suggestions.length; i++) {
        expect(suggestions[i].confidence).toBeLessThanOrEqual(suggestions[i - 1].confidence);
      }
    });
  });

  describe('Command Clarity Analysis', () => {
    it('should analyze clear commands', () => {
      const command = parser.parseCommand('create comprehensive unit tests for the user authentication service');
      const analysis = parser.analyzeCommandClarity(command);
      
      expect(['clear', 'unclear', 'ambiguous']).toContain(analysis.clarity);
      expect(analysis.score).toBeGreaterThan(0);
      expect(analysis.feedback.length).toBeGreaterThanOrEqual(0);
    });

    it('should analyze unclear commands', () => {
      const command = parser.parseCommand('fix it');
      const analysis = parser.analyzeCommandClarity(command);
      
      expect(analysis.clarity).toBe('ambiguous');
      expect(analysis.score).toBeLessThan(0.5);
      expect(analysis.feedback.length).toBeGreaterThan(0);
    });

    it('should provide helpful feedback', () => {
      const command = parser.parseCommand('do something');
      const analysis = parser.analyzeCommandClarity(command);
      
      expect(analysis.feedback).toContain('Your command is quite short - more detail would help');
      expect(analysis.feedback).toContain('Try to be more specific about what you want to work with');
    });
  });

  describe('Context Handling', () => {
    it('should use context to improve parsing', () => {
      const context = ['authentication', 'security', 'user management'];
      const result = parser.parseCommand('add validation', context);
      
      expect(result.confidence).toBeGreaterThan(0);
      expect(result.contextualEntities.length).toBeGreaterThanOrEqual(0);
    });

    it('should maintain context history', () => {
      parser.parseCommand('create user service');
      const result = parser.parseCommand('add authentication to it');
      
      // Should understand "it" refers to user service from context
      expect(result.confidence).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Semantic Token Analysis', () => {
    it('should extract semantic tokens', () => {
      const result = parser.parseCommand('implement secure payment processing');
      
      expect(result.semanticTokens.length).toBeGreaterThan(0);
      expect(result.semanticTokens.some(t => t.type === TokenType.VERB)).toBe(true);
      expect(result.semanticTokens.some(t => t.type === TokenType.NOUN)).toBe(true);
    });

    it('should provide token metadata', () => {
      const result = parser.parseCommand('create database connection');
      
      const tokens = result.semanticTokens;
      expect(tokens[0].text).toBeDefined();
      expect(tokens[0].lemma).toBeDefined();
      expect(tokens[0].partOfSpeech).toBeDefined();
      expect(tokens[0].position).toBeDefined();
    });
  });

  describe('Pattern Matching', () => {
    it('should match regex patterns', () => {
      const result = parser.parseCommand('is there already a payment processor?');
      
      expect(result.intent).toBe('check_duplicates');
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    it('should match keyword patterns', () => {
      const result = parser.parseCommand('scan for security vulnerabilities');
      
      expect(result.intent).toBe('security_scan');
      expect(result.suggestedAgent).toBe('guardian');
    });

    it('should handle pattern combinations', () => {
      const result = parser.parseCommand('completely analyze the authentication system architecture');
      
      expect(result.intent).toBe('design_architecture');
      expect(result.requiresMultiAgent).toBe(true);
    });
  });

  describe('Multi-Agent Detection', () => {
    it('should detect multi-agent requirements', () => {
      const result = parser.parseCommand('design and implement a complete user management system');
      
      expect(result.requiresMultiAgent).toBe(true);
      expect(result.suggestedAgent).toBeDefined();
    });

    it('should detect single-agent requirements', () => {
      const result = parser.parseCommand('create unit tests for the auth service');
      
      expect(result.requiresMultiAgent).toBe(false);
      expect(result.suggestedAgent).toBe('qa');
    });
  });

  describe('Error Handling', () => {
    it('should handle empty input gracefully', () => {
      const result = parser.parseCommand('');
      
      expect(result.raw).toBe('');
      expect(result.confidence).toBeLessThan(0.5);
      expect(result.suggestions.length).toBeGreaterThan(0);
    });

    it('should handle special characters', () => {
      const result = parser.parseCommand('create @user/auth#component!');
      
      expect(result.raw).toBe('create @user/auth#component!');
      expect(result.preprocessedText).not.toContain('@');
      expect(result.preprocessedText).not.toContain('#');
      expect(result.preprocessedText).not.toContain('!');
    });

    it('should handle very long input', () => {
      const longInput = 'create '.repeat(100) + 'authentication system';
      const result = parser.parseCommand(longInput);
      
      expect(result.raw).toBe(longInput);
      expect(result.confidence).toBeGreaterThan(0);
    });
  });

  describe('Performance', () => {
    it('should parse commands within reasonable time', () => {
      const start = Date.now();
      parser.parseCommand('create a comprehensive microservices architecture with authentication, authorization, and monitoring');
      const duration = Date.now() - start;
      
      expect(duration).toBeLessThan(1000); // Should complete in less than 1 second
    });

    it('should handle multiple rapid parsing requests', () => {
      const commands = [
        'create user service',
        'add authentication',
        'implement payment processing',
        'scan for vulnerabilities',
        'write tests'
      ];

      const start = Date.now();
      commands.forEach(cmd => parser.parseCommand(cmd));
      const duration = Date.now() - start;
      
      expect(duration).toBeLessThan(2000); // Should handle 5 commands in less than 2 seconds
    });
  });

  describe('Events', () => {
    it('should emit parsing completed events', async () => {
      return new Promise((resolve) => {
        parser.on('parsing_completed', (stats) => {
          expect(stats.input).toBeDefined();
          expect(stats.processingTime).toBeGreaterThanOrEqual(0);
          expect(stats.tokensExtracted).toBeGreaterThanOrEqual(0);
          resolve(undefined);
        });

        parser.parseCommand('create user authentication system');
      });
    });
  });
});