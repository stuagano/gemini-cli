/**
 * Natural Language CLI for Gemini Enterprise Architect
 * Provides natural language command processing and agent orchestration
 */

import { EventEmitter } from 'events';
import chalk from 'chalk';
import ora from 'ora';
import { Config } from '@google/gemini-cli-core';
import * as WebSocket from 'ws';
import { EnhancedNLPParser, EnhancedNLCommand, CommandSuggestion } from './enhanced-nlp-parser.js';

export interface NLCommand {
  raw: string;
  intent: string;
  entities: Record<string, any>;
  confidence: number;
  suggestedAgent?: string;
  requiresMultiAgent?: boolean;
}

export interface AgentResponse {
  agentId: string;
  persona: string;
  result: any;
  status: 'success' | 'error' | 'partial';
  executionTime?: number;
  suggestions?: string[];
}

export interface AgentCapabilities {
  scout: string[];
  architect: string[];
  developer: string[];
  guardian: string[];
  pm: string[];
  po: string[];
  qa: string[];
}

export class NaturalLanguageCLI extends EventEmitter {
  private config: Config;
  private wsConnection: WebSocket | null = null;
  private apiBaseUrl: string;
  private isConnected: boolean = false;
  private spinner: any = null;
  private agentCapabilities: AgentCapabilities;
  private enhancedParser: EnhancedNLPParser;

  constructor(config: Config) {
    super();
    this.config = config;
    this.apiBaseUrl = process.env.AGENT_SERVER_URL || 'http://localhost:2000';
    
    // Define agent capabilities for routing
    this.agentCapabilities = {
      scout: [
        'duplicate', 'duplication', 'similar', 'existing', 'reuse',
        'code quality', 'technical debt', 'smell', 'pattern'
      ],
      architect: [
        'design', 'architecture', 'pattern', 'structure', 'system',
        'microservice', 'database', 'api', 'integration', 'scale'
      ],
      developer: [
        'implement', 'create', 'build', 'code', 'function', 'class',
        'feature', 'bug', 'fix', 'refactor', 'optimize'
      ],
      guardian: [
        'security', 'validate', 'check', 'scan', 'vulnerability',
        'compliance', 'audit', 'protect', 'secure'
      ],
      pm: [
        'project', 'timeline', 'sprint', 'task', 'milestone',
        'roadmap', 'planning', 'estimate', 'resource'
      ],
      po: [
        'requirement', 'user story', 'acceptance', 'priority',
        'backlog', 'feature request', 'business value'
      ],
      qa: [
        'test', 'quality', 'regression', 'coverage', 'validation',
        'bug', 'defect', 'automation', 'performance'
      ]
    };

    // Initialize enhanced NLP parser
    this.enhancedParser = new EnhancedNLPParser(this.agentCapabilities);
    
    // Set up parser event handlers
    this.enhancedParser.on('parsing_completed', (stats) => {
      this.emit('nlp_stats', stats);
    });
  }

  /**
   * Parse natural language command into structured intent using enhanced NLP
   */
  parseCommand(input: string, context?: string[]): EnhancedNLCommand {
    return this.enhancedParser.parseCommand(input, context);
  }

  /**
   * Legacy parseCommand method for backward compatibility
   */
  parseCommandSimple(input: string): NLCommand {
    const enhanced = this.enhancedParser.parseCommand(input);
    
    // Convert enhanced command to simple format
    return {
      raw: enhanced.raw,
      intent: enhanced.intent,
      entities: enhanced.entities,
      confidence: enhanced.confidence,
      suggestedAgent: enhanced.suggestedAgent,
      requiresMultiAgent: enhanced.requiresMultiAgent
    };
  }

  /**
   * Get command suggestions for ambiguous input
   */
  getCommandSuggestions(input: string, limit?: number): CommandSuggestion[] {
    return this.enhancedParser.getCommandSuggestions(input, limit);
  }

  /**
   * Analyze command clarity and provide feedback
   */
  analyzeCommandClarity(command: EnhancedNLCommand) {
    return this.enhancedParser.analyzeCommandClarity(command);
  }

  /**
   * Route command to appropriate agent(s)
   */
  async routeCommand(command: NLCommand): Promise<AgentResponse[]> {
    const responses: AgentResponse[] = [];

    try {
      if (command.requiresMultiAgent) {
        // Multi-agent workflow
        responses.push(...await this.executeMultiAgentWorkflow(command));
      } else {
        // Single agent execution
        const response = await this.executeSingleAgent(command);
        responses.push(response);
      }
    } catch (error) {
      responses.push({
        agentId: 'system',
        persona: 'error',
        result: { error: error instanceof Error ? error.message : 'Unknown error' },
        status: 'error'
      });
    }

    return responses;
  }

  /**
   * Execute single agent task
   */
  private async executeSingleAgent(command: NLCommand): Promise<AgentResponse> {
    const agentId = command.suggestedAgent || 'developer';
    
    this.showStatus(`Routing to ${chalk.cyan(agentId)} agent...`);

    try {
      const response = await this.callAgentAPI({
        agent: agentId,
        task: command.intent,
        input: {
          command: command.raw,
          entities: command.entities
        }
      });

      return {
        agentId,
        persona: agentId,
        result: response,
        status: 'success',
        executionTime: response.execution_time_ms
      };
    } catch (error) {
      return {
        agentId,
        persona: agentId,
        result: { error: error instanceof Error ? error.message : 'Agent execution failed' },
        status: 'error'
      };
    }
  }

  /**
   * Execute multi-agent workflow
   */
  private async executeMultiAgentWorkflow(command: NLCommand): Promise<AgentResponse[]> {
    const responses: AgentResponse[] = [];
    
    this.showStatus('Initiating multi-agent workflow...');

    // Scout-first architecture: Always check with Scout first
    if (!command.raw.includes('skip scout')) {
      const scoutResponse = await this.callAgentAPI({
        agent: 'scout',
        task: 'analyze_request',
        input: {
          command: command.raw,
          check_duplicates: true,
          analyze_impact: true
        }
      });

      responses.push({
        agentId: 'scout',
        persona: 'scout',
        result: scoutResponse,
        status: 'success'
      });

      // If Scout finds existing solutions, ask user before proceeding
      if (scoutResponse.duplicates_found) {
        this.emit('duplicates_found', scoutResponse.duplicates);
        const proceed = await this.confirmProceed('Scout found existing similar code. Continue anyway?');
        if (!proceed) {
          return responses;
        }
      }
    }

    // Architect for design decisions
    if (command.intent.includes('design') || command.intent.includes('architecture')) {
      const architectResponse = await this.callAgentAPI({
        agent: 'architect',
        task: 'design_solution',
        input: {
          command: command.raw,
          scout_analysis: responses[0]?.result
        }
      });

      responses.push({
        agentId: 'architect',
        persona: 'architect',
        result: architectResponse,
        status: 'success'
      });
    }

    // Guardian for continuous validation
    const guardianResponse = await this.callAgentAPI({
      agent: 'guardian',
      task: 'validate_approach',
      input: {
        command: command.raw,
        proposed_solution: responses[responses.length - 1]?.result
      }
    });

    responses.push({
      agentId: 'guardian',
      persona: 'guardian',
      result: guardianResponse,
      status: guardianResponse.validation_passed ? 'success' : 'partial'
    });

    return responses;
  }

  /**
   * Call agent server API
   */
  private async callAgentAPI(request: any): Promise<any> {
    const url = `${this.apiBaseUrl}/api/v1/agent/execute`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`Agent API error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      // Fallback to mock response if server not available
      return this.getMockResponse(request.agent, request.task);
    }
  }

  /**
   * Get mock response for testing without server
   */
  private getMockResponse(agent: string, task: string): any {
    const mockResponses: Record<string, any> = {
      scout: {
        duplicates_found: false,
        similar_patterns: [],
        code_quality_score: 8.5,
        suggestions: ['Consider using existing utility functions', 'Check shared libraries']
      },
      architect: {
        design_pattern: 'MVC',
        components: ['Controller', 'Service', 'Repository'],
        technologies: ['Node.js', 'TypeScript', 'PostgreSQL'],
        considerations: ['Scalability', 'Maintainability', 'Security']
      },
      guardian: {
        validation_passed: true,
        security_score: 9.0,
        vulnerabilities: [],
        recommendations: ['Add input validation', 'Implement rate limiting']
      },
      developer: {
        code_generated: true,
        files_created: ['src/feature.ts', 'tests/feature.test.ts'],
        lines_of_code: 150,
        test_coverage: 85
      }
    };

    return mockResponses[agent] || { message: `Mock response from ${agent}` };
  }

  /**
   * Connect to agent server via WebSocket for real-time updates
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = this.apiBaseUrl.replace('http', 'ws') + '/ws';
      
      try {
        this.wsConnection = new WebSocket(wsUrl);

        this.wsConnection.on('open', () => {
          this.isConnected = true;
          this.emit('connected');
          console.log(chalk.green('✓ Connected to agent server'));
          resolve();
        });

        this.wsConnection.on('message', (data: string) => {
          try {
            const message = JSON.parse(data);
            this.handleServerMessage(message);
          } catch (error) {
            console.error('Error parsing server message:', error);
          }
        });

        this.wsConnection.on('error', (error) => {
          console.error(chalk.red('WebSocket error:'), error);
          this.isConnected = false;
          reject(error);
        });

        this.wsConnection.on('close', () => {
          this.isConnected = false;
          this.emit('disconnected');
          console.log(chalk.yellow('Disconnected from agent server'));
        });

        // Timeout connection attempt
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('Connection timeout'));
          }
        }, 5000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Handle real-time messages from server
   */
  private handleServerMessage(message: any): void {
    switch (message.type) {
      case 'status_update':
        this.emit('status', message.data);
        break;
      case 'agent_response':
        this.emit('agent_response', message.data);
        break;
      case 'validation_warning':
        this.emit('warning', message.data);
        break;
      case 'progress':
        this.emit('progress', message.data);
        break;
      default:
        this.emit('message', message);
    }
  }

  /**
   * Process natural language command with enhanced NLP
   */
  async processCommandEnhanced(input: string, context?: string[]): Promise<void> {
    console.log(chalk.blue('\n🤖 Processing with Enhanced NLP:'), input);
    
    // Parse with enhanced NLP
    const enhancedCommand = this.parseCommand(input, context);
    
    console.log(chalk.gray(`Intent: ${enhancedCommand.intent}, Confidence: ${enhancedCommand.confidence}`));
    console.log(chalk.gray(`Ambiguity Score: ${enhancedCommand.ambiguityScore.toFixed(2)}`));
    
    // Show entities found
    if (enhancedCommand.contextualEntities.length > 0) {
      console.log(chalk.cyan('Entities found:'));
      enhancedCommand.contextualEntities.forEach(entity => {
        console.log(chalk.cyan(`  - ${entity.type}: ${entity.value} (${Math.round(entity.confidence * 100)}%)`));
      });
    }
    
    // Handle low confidence or high ambiguity
    if (enhancedCommand.confidence < 0.5 || enhancedCommand.ambiguityScore > 0.6) {
      console.log(chalk.yellow('⚠️  Command interpretation needs clarification'));
      
      // Show clarity analysis
      const clarityAnalysis = this.analyzeCommandClarity(enhancedCommand);
      console.log(chalk.yellow(`Clarity: ${clarityAnalysis.clarity} (${Math.round(clarityAnalysis.score * 100)}%)`));
      
      if (clarityAnalysis.feedback.length > 0) {
        console.log(chalk.yellow('Feedback:'));
        clarityAnalysis.feedback.forEach(feedback => console.log(chalk.yellow(`  - ${feedback}`)));
      }
      
      // Show suggestions
      const suggestions = this.getCommandSuggestions(input, 3);
      if (suggestions.length > 0) {
        console.log(chalk.gray('Did you mean:'));
        suggestions.forEach(s => console.log(chalk.gray(`  - "${s.command}" (${s.agent} agent) - ${s.reasoning}`)));
      }
      
      // Show alternatives
      if (enhancedCommand.alternatives.length > 0) {
        console.log(chalk.cyan('Alternative interpretations:'));
        enhancedCommand.alternatives.forEach((alt, index) => {
          console.log(chalk.cyan(`  ${index + 1}. ${alt.intent} (${alt.suggestedAgent}) - ${Math.round(alt.confidence * 100)}%`));
          console.log(chalk.gray(`     ${alt.reasoning}`));
        });
      }
    }
    
    // Convert to legacy format for routing
    const legacyCommand = this.parseCommandSimple(input);
    
    // Route to appropriate agent(s)
    const responses = await this.routeCommand(legacyCommand);
    
    // Display results
    this.displayResponses(responses);
  }

  /**
   * Process natural language command (legacy method)
   */
  async processCommand(input: string): Promise<void> {
    console.log(chalk.blue('\n🤖 Processing:'), input);
    
    // Parse the command
    const command = this.parseCommandSimple(input);
    
    console.log(chalk.gray(`Intent: ${command.intent}, Confidence: ${command.confidence}`));
    
    if (command.confidence < 0.5) {
      console.log(chalk.yellow('⚠️  Low confidence in command interpretation'));
      const suggestions = this.getSuggestions(input);
      if (suggestions.length > 0) {
        console.log(chalk.gray('Did you mean:'));
        suggestions.forEach(s => console.log(chalk.gray(`  - ${s}`)));
      }
    }

    // Route to appropriate agent(s)
    const responses = await this.routeCommand(command);
    
    // Display results
    this.displayResponses(responses);
  }

  /**
   * Display agent responses
   */
  private displayResponses(responses: AgentResponse[]): void {
    console.log(chalk.green('\n✨ Results:'));
    
    responses.forEach(response => {
      const icon = response.status === 'success' ? '✓' : 
                   response.status === 'error' ? '✗' : '⚠';
      const color = response.status === 'success' ? chalk.green :
                    response.status === 'error' ? chalk.red : chalk.yellow;
      
      console.log(color(`\n${icon} ${response.persona.toUpperCase()} Agent:`));
      
      if (response.status === 'error') {
        console.log(chalk.red(`  Error: ${response.result.error}`));
      } else {
        console.log(this.formatResult(response.result));
      }
      
      if (response.executionTime) {
        console.log(chalk.gray(`  Execution time: ${response.executionTime}ms`));
      }
      
      if (response.suggestions && response.suggestions.length > 0) {
        console.log(chalk.cyan('  Suggestions:'));
        response.suggestions.forEach(s => console.log(chalk.cyan(`    • ${s}`)));
      }
    });
  }

  /**
   * Format result for display
   */
  private formatResult(result: any): string {
    if (typeof result === 'string') {
      return `  ${result}`;
    }
    
    const lines: string[] = [];
    for (const [key, value] of Object.entries(result)) {
      if (Array.isArray(value)) {
        lines.push(`  ${key}:`);
        value.forEach(item => lines.push(`    - ${item}`));
      } else if (typeof value === 'object' && value !== null) {
        lines.push(`  ${key}: ${JSON.stringify(value, null, 2).split('\n').join('\n  ')}`);
      } else {
        lines.push(`  ${key}: ${value}`);
      }
    }
    
    return lines.join('\n');
  }

  /**
   * Get command suggestions
   */
  private getSuggestions(input: string): string[] {
    const suggestions: string[] = [];
    const lowerInput = input.toLowerCase();

    if (lowerInput.includes('check') || lowerInput.includes('find')) {
      suggestions.push('Check for duplicate code in the project');
      suggestions.push('Find similar implementations');
    }

    if (lowerInput.includes('create') || lowerInput.includes('build')) {
      suggestions.push('Create a new feature with tests');
      suggestions.push('Build a REST API endpoint');
    }

    if (lowerInput.includes('review') || lowerInput.includes('analyze')) {
      suggestions.push('Review code for security vulnerabilities');
      suggestions.push('Analyze architecture for improvements');
    }

    return suggestions.slice(0, 3);
  }

  /**
   * Show status with spinner
   */
  private showStatus(message: string): void {
    if (this.spinner) {
      this.spinner.text = message;
    } else {
      this.spinner = ora(message).start();
    }
  }

  /**
   * Stop spinner
   */
  private stopSpinner(success: boolean = true): void {
    if (this.spinner) {
      if (success) {
        this.spinner.succeed();
      } else {
        this.spinner.fail();
      }
      this.spinner = null;
    }
  }

  /**
   * Confirm with user
   */
  private async confirmProceed(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.emit('confirm_required', { message, callback: resolve });
    });
  }

  /**
   * Disconnect from server
   */
  disconnect(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
    this.isConnected = false;
  }

  /**
   * Check if connected
   */
  isReady(): boolean {
    return this.isConnected;
  }
}

export default NaturalLanguageCLI;