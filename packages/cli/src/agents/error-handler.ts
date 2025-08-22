/**
 * Error Handler for Agent Operations
 * Provides comprehensive error handling, recovery, and fallback mechanisms
 */

import chalk from 'chalk';
import { EventEmitter } from 'events';

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum ErrorCategory {
  NETWORK = 'network',
  AGENT = 'agent',
  VALIDATION = 'validation',
  TIMEOUT = 'timeout',
  PERMISSION = 'permission',
  RESOURCE = 'resource',
  CONFIGURATION = 'configuration',
  UNKNOWN = 'unknown'
}

export interface AgentError {
  id: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  message: string;
  details?: any;
  agent?: string;
  task?: string;
  timestamp: Date;
  retryable: boolean;
  retryCount?: number;
  maxRetries?: number;
  resolution?: string;
  stack?: string;
}

export interface ErrorRecoveryStrategy {
  category: ErrorCategory;
  action: (error: AgentError) => Promise<boolean>;
  fallback?: () => Promise<any>;
}

export class AgentErrorHandler extends EventEmitter {
  private errorHistory: AgentError[] = [];
  private recoveryStrategies: Map<ErrorCategory, ErrorRecoveryStrategy> = new Map();
  private errorCounts: Map<string, number> = new Map();
  private circuitBreakers: Map<string, CircuitBreaker> = new Map();
  private maxHistorySize: number = 100;

  constructor() {
    super();
    this.setupDefaultRecoveryStrategies();
  }

  /**
   * Setup default recovery strategies
   */
  private setupDefaultRecoveryStrategies(): void {
    // Network errors
    this.recoveryStrategies.set(ErrorCategory.NETWORK, {
      category: ErrorCategory.NETWORK,
      action: async (error) => {
        console.log(chalk.yellow('⚠ Network error detected, attempting reconnection...'));
        
        // Exponential backoff retry
        const delay = Math.min(1000 * Math.pow(2, error.retryCount || 0), 30000);
        await this.delay(delay);
        
        return error.retryCount! < (error.maxRetries || 3);
      },
      fallback: async () => {
        console.log(chalk.gray('Using cached response or mock data'));
        return { source: 'cache', data: {} };
      }
    });

    // Agent errors
    this.recoveryStrategies.set(ErrorCategory.AGENT, {
      category: ErrorCategory.AGENT,
      action: async (error) => {
        console.log(chalk.yellow(`⚠ Agent ${error.agent} error, trying alternative agent...`));
        
        // Try to route to alternative agent
        const alternative = this.findAlternativeAgent(error.agent!);
        if (alternative) {
          console.log(chalk.blue(`Routing to ${alternative} agent`));
          return true;
        }
        return false;
      }
    });

    // Timeout errors
    this.recoveryStrategies.set(ErrorCategory.TIMEOUT, {
      category: ErrorCategory.TIMEOUT,
      action: async (error) => {
        console.log(chalk.yellow('⚠ Operation timeout, retrying with extended timeout...'));
        
        // Increase timeout and retry
        return error.retryCount! < 2;
      }
    });

    // Validation errors
    this.recoveryStrategies.set(ErrorCategory.VALIDATION, {
      category: ErrorCategory.VALIDATION,
      action: async (error) => {
        console.log(chalk.red('✗ Validation error - cannot auto-recover'));
        
        // Validation errors typically need user intervention
        return false;
      }
    });

    // Permission errors
    this.recoveryStrategies.set(ErrorCategory.PERMISSION, {
      category: ErrorCategory.PERMISSION,
      action: async (error) => {
        console.log(chalk.red('✗ Permission denied'));
        console.log(chalk.gray('Please check your credentials and permissions'));
        return false;
      }
    });

    // Resource errors
    this.recoveryStrategies.set(ErrorCategory.RESOURCE, {
      category: ErrorCategory.RESOURCE,
      action: async (error) => {
        console.log(chalk.yellow('⚠ Resource constraint detected'));
        
        // Try to free resources or scale down
        await this.optimizeResources();
        return error.retryCount! < 1;
      }
    });
  }

  /**
   * Handle error with recovery attempt
   */
  async handleError(error: Error | AgentError, context?: any): Promise<boolean> {
    const agentError = this.normalizeError(error, context);
    
    // Add to history
    this.addToHistory(agentError);
    
    // Emit error event
    this.emit('error', agentError);
    
    // Check circuit breaker
    const breaker = this.getCircuitBreaker(agentError.agent || 'system');
    if (breaker.isOpen()) {
      console.log(chalk.red(`Circuit breaker open for ${agentError.agent}`));
      return false;
    }

    // Log error
    this.logError(agentError);
    
    // Attempt recovery
    const recovered = await this.attemptRecovery(agentError);
    
    if (!recovered) {
      breaker.recordFailure();
      
      // Try fallback
      const fallback = await this.executeFallback(agentError);
      if (fallback) {
        console.log(chalk.green('✓ Fallback successful'));
        return true;
      }
    } else {
      breaker.recordSuccess();
    }
    
    return recovered;
  }

  /**
   * Normalize error to AgentError format
   */
  private normalizeError(error: Error | AgentError, context?: any): AgentError {
    if (this.isAgentError(error)) {
      return error;
    }

    const category = this.categorizeError(error);
    const severity = this.assessSeverity(error, category);
    
    return {
      id: `err_${Date.now()}`,
      category,
      severity,
      message: error.message,
      details: context,
      timestamp: new Date(),
      retryable: this.isRetryable(category),
      retryCount: 0,
      maxRetries: 3,
      stack: error.stack,
      resolution: this.suggestResolution(category, error.message)
    };
  }

  /**
   * Check if error is AgentError
   */
  private isAgentError(error: any): error is AgentError {
    return error && 'category' in error && 'severity' in error;
  }

  /**
   * Categorize error
   */
  private categorizeError(error: Error): ErrorCategory {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('connection') || message.includes('econnrefused')) {
      return ErrorCategory.NETWORK;
    }
    if (message.includes('timeout') || message.includes('timed out')) {
      return ErrorCategory.TIMEOUT;
    }
    if (message.includes('permission') || message.includes('denied') || message.includes('unauthorized')) {
      return ErrorCategory.PERMISSION;
    }
    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorCategory.VALIDATION;
    }
    if (message.includes('memory') || message.includes('resource')) {
      return ErrorCategory.RESOURCE;
    }
    if (message.includes('agent')) {
      return ErrorCategory.AGENT;
    }
    
    return ErrorCategory.UNKNOWN;
  }

  /**
   * Assess error severity
   */
  private assessSeverity(error: Error, category: ErrorCategory): ErrorSeverity {
    // Critical categories
    if (category === ErrorCategory.PERMISSION) {
      return ErrorSeverity.CRITICAL;
    }
    
    // High severity for validation and agent errors
    if (category === ErrorCategory.VALIDATION || category === ErrorCategory.AGENT) {
      return ErrorSeverity.HIGH;
    }
    
    // Medium for network and timeout
    if (category === ErrorCategory.NETWORK || category === ErrorCategory.TIMEOUT) {
      return ErrorSeverity.MEDIUM;
    }
    
    // Resource errors depend on the specific issue
    if (category === ErrorCategory.RESOURCE) {
      if (error.message.includes('out of memory')) {
        return ErrorSeverity.CRITICAL;
      }
      return ErrorSeverity.HIGH;
    }
    
    return ErrorSeverity.LOW;
  }

  /**
   * Check if error is retryable
   */
  private isRetryable(category: ErrorCategory): boolean {
    const retryableCategories = [
      ErrorCategory.NETWORK,
      ErrorCategory.TIMEOUT,
      ErrorCategory.RESOURCE,
      ErrorCategory.AGENT
    ];
    
    return retryableCategories.includes(category);
  }

  /**
   * Suggest resolution for error
   */
  private suggestResolution(category: ErrorCategory, message: string): string {
    const resolutions: Record<ErrorCategory, string> = {
      [ErrorCategory.NETWORK]: 'Check network connection and agent server status. Run: ./start_server.sh',
      [ErrorCategory.TIMEOUT]: 'Operation took too long. Try breaking down into smaller tasks.',
      [ErrorCategory.PERMISSION]: 'Check API keys and authentication credentials.',
      [ErrorCategory.VALIDATION]: 'Review input parameters and ensure they meet requirements.',
      [ErrorCategory.RESOURCE]: 'System resources may be constrained. Close other applications.',
      [ErrorCategory.AGENT]: 'Agent may be unavailable. Check agent server logs.',
      [ErrorCategory.CONFIGURATION]: 'Check configuration files and environment variables.',
      [ErrorCategory.UNKNOWN]: 'Unexpected error. Check logs for more details.'
    };
    
    return resolutions[category];
  }

  /**
   * Log error with formatting
   */
  private logError(error: AgentError): void {
    const icon = this.getSeverityIcon(error.severity);
    const color = this.getSeverityColor(error.severity);
    
    console.log(color(`\n${icon} Error: ${error.message}`));
    
    if (error.agent) {
      console.log(chalk.gray(`   Agent: ${error.agent}`));
    }
    
    if (error.task) {
      console.log(chalk.gray(`   Task: ${error.task}`));
    }
    
    console.log(chalk.gray(`   Category: ${error.category}`));
    console.log(chalk.gray(`   Severity: ${error.severity}`));
    
    if (error.resolution) {
      console.log(chalk.cyan(`   Resolution: ${error.resolution}`));
    }
    
    if (error.details) {
      console.log(chalk.gray(`   Details: ${JSON.stringify(error.details, null, 2)}`));
    }
  }

  /**
   * Get severity icon
   */
  private getSeverityIcon(severity: ErrorSeverity): string {
    const icons: Record<ErrorSeverity, string> = {
      [ErrorSeverity.LOW]: '⚪',
      [ErrorSeverity.MEDIUM]: '🟡',
      [ErrorSeverity.HIGH]: '🟠',
      [ErrorSeverity.CRITICAL]: '🔴'
    };
    return icons[severity];
  }

  /**
   * Get severity color
   */
  private getSeverityColor(severity: ErrorSeverity): (text: string) => string {
    const colors: Record<ErrorSeverity, (text: string) => string> = {
      [ErrorSeverity.LOW]: chalk.gray,
      [ErrorSeverity.MEDIUM]: chalk.yellow,
      [ErrorSeverity.HIGH]: chalk.magenta,
      [ErrorSeverity.CRITICAL]: chalk.red
    };
    return colors[severity];
  }

  /**
   * Attempt error recovery
   */
  private async attemptRecovery(error: AgentError): Promise<boolean> {
    const strategy = this.recoveryStrategies.get(error.category);
    
    if (!strategy) {
      console.log(chalk.gray('No recovery strategy available'));
      return false;
    }
    
    if (!error.retryable) {
      console.log(chalk.gray('Error is not retryable'));
      return false;
    }
    
    if (error.retryCount! >= (error.maxRetries || 3)) {
      console.log(chalk.red('Max retries exceeded'));
      return false;
    }
    
    error.retryCount = (error.retryCount || 0) + 1;
    console.log(chalk.yellow(`Attempting recovery (${error.retryCount}/${error.maxRetries})...`));
    
    try {
      const result = await strategy.action(error);
      
      if (result) {
        console.log(chalk.green('✓ Recovery successful'));
      }
      
      return result;
    } catch (recoveryError) {
      console.log(chalk.red('Recovery failed:', recoveryError));
      return false;
    }
  }

  /**
   * Execute fallback strategy
   */
  private async executeFallback(error: AgentError): Promise<any> {
    const strategy = this.recoveryStrategies.get(error.category);
    
    if (!strategy || !strategy.fallback) {
      return null;
    }
    
    console.log(chalk.yellow('Executing fallback strategy...'));
    
    try {
      return await strategy.fallback();
    } catch (fallbackError) {
      console.log(chalk.red('Fallback failed:', fallbackError));
      return null;
    }
  }

  /**
   * Find alternative agent
   */
  private findAlternativeAgent(failedAgent: string): string | null {
    const alternatives: Record<string, string[]> = {
      'developer': ['architect', 'pm'],
      'architect': ['developer', 'pm'],
      'qa': ['guardian', 'developer'],
      'guardian': ['qa', 'architect'],
      'scout': ['architect', 'developer'],
      'pm': ['po', 'architect'],
      'po': ['pm', 'architect']
    };
    
    const alts = alternatives[failedAgent];
    return alts ? alts[0] : null;
  }

  /**
   * Optimize resources
   */
  private async optimizeResources(): Promise<void> {
    console.log(chalk.blue('Optimizing resources...'));
    
    // Clear caches
    global.gc && global.gc();
    
    // Reduce concurrent operations
    this.emit('optimize_resources');
    
    await this.delay(1000);
  }

  /**
   * Add error to history
   */
  private addToHistory(error: AgentError): void {
    this.errorHistory.push(error);
    
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory.shift();
    }
    
    // Update error counts
    const key = `${error.category}_${error.severity}`;
    this.errorCounts.set(key, (this.errorCounts.get(key) || 0) + 1);
  }

  /**
   * Get circuit breaker for agent
   */
  private getCircuitBreaker(agent: string): CircuitBreaker {
    if (!this.circuitBreakers.has(agent)) {
      this.circuitBreakers.set(agent, new CircuitBreaker(agent));
    }
    return this.circuitBreakers.get(agent)!;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get error statistics
   */
  getStatistics(): any {
    const stats: any = {
      total: this.errorHistory.length,
      byCategory: {},
      bySeverity: {},
      recentErrors: this.errorHistory.slice(-5)
    };
    
    // Count by category
    for (const error of this.errorHistory) {
      stats.byCategory[error.category] = (stats.byCategory[error.category] || 0) + 1;
      stats.bySeverity[error.severity] = (stats.bySeverity[error.severity] || 0) + 1;
    }
    
    return stats;
  }

  /**
   * Clear error history
   */
  clearHistory(): void {
    this.errorHistory = [];
    this.errorCounts.clear();
  }

  /**
   * Reset circuit breakers
   */
  resetCircuitBreakers(): void {
    this.circuitBreakers.forEach(breaker => breaker.reset());
  }
}

/**
 * Circuit Breaker implementation
 */
class CircuitBreaker {
  private name: string;
  private failureCount: number = 0;
  private successCount: number = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private nextAttempt: Date | null = null;
  private threshold: number = 5;
  private timeout: number = 60000; // 1 minute

  constructor(name: string) {
    this.name = name;
  }

  isOpen(): boolean {
    if (this.state === 'open') {
      if (this.nextAttempt && new Date() > this.nextAttempt) {
        this.state = 'half-open';
        return false;
      }
      return true;
    }
    return false;
  }

  recordSuccess(): void {
    this.failureCount = 0;
    this.successCount++;
    
    if (this.state === 'half-open') {
      this.state = 'closed';
    }
  }

  recordFailure(): void {
    this.failureCount++;
    this.successCount = 0;
    
    if (this.failureCount >= this.threshold) {
      this.state = 'open';
      this.nextAttempt = new Date(Date.now() + this.timeout);
      console.log(chalk.red(`Circuit breaker opened for ${this.name}`));
    }
  }

  reset(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.successCount = 0;
    this.nextAttempt = null;
  }

  getState(): string {
    return this.state;
  }
}

export default AgentErrorHandler;