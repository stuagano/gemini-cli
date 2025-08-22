/**
 * Scaling Issue Detector - The "Killer Demo" 
 * Detects scaling issues before they reach production
 * Implements N+1 queries, memory leaks, and inefficient algorithm detection
 */

import { EventEmitter } from 'events';
import chalk from 'chalk';
import crypto from 'crypto';

export interface ScalingIssue {
  id: string;
  type: 'n_plus_one' | 'memory_leak' | 'inefficient_algorithm' | 'blocking_operation' | 'resource_exhaustion';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  location: {
    file: string;
    line?: number;
    function?: string;
    codeSnippet?: string;
  };
  impact: {
    loadIncrease: number; // Percentage increase under load
    memoryGrowth: number; // MB growth per operation
    responseTimeIncrease: number; // Milliseconds per additional item
    estimatedBreakingPoint: string; // "100 users", "1000 records", etc.
  };
  recommendation: {
    solution: string;
    priority: 'immediate' | 'next_sprint' | 'backlog';
    estimatedFixTime: string;
    preventionStrategy: string;
  };
  examples: {
    goodCode: string;
    badCode: string;
    explanation: string;
  };
}

export interface ScalingAnalysisRequest {
  filePath?: string;
  codeSnippet?: string;
  projectPath?: string;
  analysisDepth: 'quick' | 'thorough' | 'comprehensive';
  includeExamples?: boolean;
}

export interface ScalingAnalysisResult {
  analysisId: string;
  timestamp: Date;
  issues: ScalingIssue[];
  overallRisk: 'low' | 'medium' | 'high' | 'critical';
  estimatedUserCapacity: number;
  recommendedActions: string[];
  analysisTime: number;
  confidence: number;
}

export class ScalingDetector extends EventEmitter {
  private detectionRules: Map<string, DetectionRule> = new Map();
  private analysisHistory: ScalingAnalysisResult[] = [];

  constructor() {
    super();
    this.initializeDetectionRules();
  }

  /**
   * Initialize all detection rules
   */
  private initializeDetectionRules(): void {
    // N+1 Query Detection Rules
    this.detectionRules.set('n_plus_one_loops', {
      name: 'N+1 Query in Loops',
      pattern: /for\s*\([^)]*\)\s*{[^}]*(?:query|find|get|select|fetch)[^}]*}/gi,
      severity: 'critical',
      check: this.checkNPlusOneInLoops.bind(this),
      recommendation: 'Use batch queries, eager loading, or data loaders to fetch all needed data in a single query'
    });

    this.detectionRules.set('n_plus_one_map', {
      name: 'N+1 Query in Array.map',
      pattern: /\.map\s*\([^)]*(?:query|find|get|select|fetch)[^)]*\)/gi,
      severity: 'critical',
      check: this.checkNPlusOneInMap.bind(this),
      recommendation: 'Collect IDs first, then batch fetch all related data'
    });

    this.detectionRules.set('n_plus_one_foreach', {
      name: 'N+1 Query in forEach',
      pattern: /\.forEach\s*\([^}]*(?:await|query|find|get|select|fetch|update)[^}]*\)/gi,
      severity: 'critical',
      check: this.checkNPlusOneInForEach.bind(this),
      recommendation: 'Replace forEach with batch operations'
    });

    // Memory Leak Detection Rules
    this.detectionRules.set('unclosed_connections', {
      name: 'Unclosed Database Connections',
      pattern: /(?:connection|client|pool)\.(?:query|execute)[^}]*(?!\.close|\.end|\.release)/gi,
      severity: 'high',
      check: this.checkUnmanagedConnections.bind(this),
      recommendation: 'Always close connections in finally blocks or use connection pooling'
    });

    this.detectionRules.set('event_listeners', {
      name: 'Unremoved Event Listeners',
      pattern: /addEventListener|on\('|\.on\s*\(/gi,
      severity: 'medium',
      check: this.checkEventListenerLeaks.bind(this),
      recommendation: 'Remove event listeners in cleanup methods or use weak references'
    });

    this.detectionRules.set('global_variables', {
      name: 'Growing Global Variables',
      pattern: /(?:global|window)\.[\w]+\s*=|var\s+[\w]+\s*=.*\[\]/gi,
      severity: 'medium',
      check: this.checkGlobalVariableGrowth.bind(this),
      recommendation: 'Use local variables or implement proper cleanup mechanisms'
    });

    // Inefficient Algorithm Detection
    this.detectionRules.set('nested_loops', {
      name: 'Nested Loops O(n²) or worse',
      pattern: /for\s*\([^)]*\)\s*{[^}]*for\s*\([^)]*\)\s*{/gi,
      severity: 'high',
      check: this.checkNestedLoops.bind(this),
      recommendation: 'Use hash maps, sets, or more efficient algorithms to reduce complexity'
    });

    this.detectionRules.set('linear_search', {
      name: 'Linear Search in Loops',
      pattern: /for\s*\([^)]*\)\s*{[^}]*\.find\s*\(|\.indexOf\s*\(/gi,
      severity: 'medium',
      check: this.checkLinearSearchInLoops.bind(this),
      recommendation: 'Create lookup maps outside loops for O(1) access'
    });

    this.detectionRules.set('repeated_calculations', {
      name: 'Repeated Expensive Calculations',
      pattern: /for\s*\([^)]*\)\s*{[^}]*(?:Math\.|crypto\.|JSON\.parse|JSON\.stringify)/gi,
      severity: 'medium',
      check: this.checkRepeatedCalculations.bind(this),
      recommendation: 'Cache expensive calculations outside loops'
    });

    // Blocking Operations
    this.detectionRules.set('sync_file_operations', {
      name: 'Synchronous File Operations',
      pattern: /fs\.readFileSync|fs\.writeFileSync|fs\.existsSync/gi,
      severity: 'high',
      check: this.checkSyncFileOperations.bind(this),
      recommendation: 'Use async file operations to prevent blocking the event loop'
    });

    this.detectionRules.set('sync_network_calls', {
      name: 'Synchronous Network Calls',
      pattern: /XMLHttpRequest|fetch.*(?!async)|request\.get(?!.*async)/gi,
      severity: 'critical',
      check: this.checkSyncNetworkCalls.bind(this),
      recommendation: 'Use async/await or promises for all network operations'
    });
  }

  /**
   * Analyze code for scaling issues
   */
  async analyzeForScalingIssues(request: ScalingAnalysisRequest): Promise<ScalingAnalysisResult> {
    const startTime = Date.now();
    const analysisId = this.generateAnalysisId();

    console.log(chalk.blue('🔍 Analyzing for scaling issues...'));
    this.emit('analysis_started', { analysisId, request });

    try {
      const issues: ScalingIssue[] = [];
      
      // Get code to analyze
      const codeToAnalyze = request.codeSnippet || await this.getCodeFromFile(request.filePath);
      
      if (!codeToAnalyze) {
        // Return empty result instead of throwing error for graceful handling
        return {
          analysisId,
          timestamp: new Date(),
          issues: [],
          overallRisk: 'low' as const,
          estimatedUserCapacity: 10000,
          recommendedActions: ['No code provided for analysis'],
          analysisTime: Date.now() - startTime,
          confidence: 0.1
        };
      }

      // Run all detection rules
      for (const [ruleId, rule] of this.detectionRules.entries()) {
        const ruleIssues = await this.runDetectionRule(rule, codeToAnalyze, ruleId, request);
        issues.push(...ruleIssues);
      }

      // Calculate overall risk
      const overallRisk = this.calculateOverallRisk(issues);
      
      // Estimate user capacity
      const estimatedUserCapacity = this.estimateUserCapacity(issues);
      
      // Generate recommended actions
      const recommendedActions = this.generateRecommendedActions(issues);
      
      // Calculate confidence
      const confidence = this.calculateConfidence(issues, codeToAnalyze);

      const result: ScalingAnalysisResult = {
        analysisId,
        timestamp: new Date(),
        issues,
        overallRisk,
        estimatedUserCapacity,
        recommendedActions,
        analysisTime: Date.now() - startTime,
        confidence
      };

      // Store in history
      this.analysisHistory.push(result);
      if (this.analysisHistory.length > 50) {
        this.analysisHistory.shift();
      }

      // Display results
      this.displayAnalysisResult(result);

      this.emit('analysis_completed', result);
      return result;

    } catch (error) {
      console.log(chalk.red('❌ Scaling analysis failed:', error));
      this.emit('analysis_failed', { analysisId, error });
      throw error;
    }
  }

  /**
   * Run a specific detection rule
   */
  private async runDetectionRule(
    rule: DetectionRule, 
    code: string, 
    ruleId: string, 
    request: ScalingAnalysisRequest
  ): Promise<ScalingIssue[]> {
    const issues: ScalingIssue[] = [];
    const matches = code.match(rule.pattern);

    if (matches) {
      for (const match of matches) {
        const issue = await rule.check(match, code, request);
        if (issue) {
          issue.id = `${ruleId}_${crypto.randomBytes(4).toString('hex')}`;
          issues.push(issue);
        }
      }
    }

    return issues;
  }

  /**
   * N+1 Query Detection Methods
   */
  private async checkNPlusOneInLoops(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    // Check if this looks like an N+1 query pattern
    if (match.includes('query') || match.includes('find') || match.includes('get')) {
      return {
        id: '', // Will be set by caller
        type: 'n_plus_one',
        severity: 'critical',
        title: 'N+1 Query Pattern in Loop',
        description: 'Database query inside a loop will execute once per iteration, causing exponential performance degradation',
        location: {
          file: request.filePath || 'code snippet',
          codeSnippet: match
        },
        impact: {
          loadIncrease: 10000, // 100x worse with 100 items
          memoryGrowth: 50,
          responseTimeIncrease: 100,
          estimatedBreakingPoint: '50-100 records'
        },
        recommendation: {
          solution: 'Collect all IDs first, then use a single batch query with IN clause',
          priority: 'immediate',
          estimatedFixTime: '2-4 hours',
          preventionStrategy: 'Code review checklist for database queries in loops'
        },
        examples: {
          badCode: `// ❌ N+1 Query Pattern
for (const user of users) {
  const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
  user.orders = orders;
}`,
          goodCode: `// ✅ Batch Query Solution
const userIds = users.map(u => u.id);
const allOrders = await db.query('SELECT * FROM orders WHERE user_id IN (?)', [userIds]);
const ordersByUserId = groupBy(allOrders, 'user_id');
users.forEach(user => {
  user.orders = ordersByUserId[user.id] || [];
});`,
          explanation: 'Instead of N queries (one per user), we execute just 2 queries total regardless of user count'
        }
      };
    }
    return null;
  }

  private async checkNPlusOneInMap(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'n_plus_one',
      severity: 'critical',
      title: 'N+1 Query in Array.map',
      description: 'Async database calls inside map operations create race conditions and scale poorly',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 5000,
        memoryGrowth: 100,
        responseTimeIncrease: 150,
        estimatedBreakingPoint: '20-50 items'
      },
      recommendation: {
        solution: 'Use Promise.all with batch queries or data loaders',
        priority: 'immediate',
        estimatedFixTime: '1-2 hours',
        preventionStrategy: 'Lint rule to detect async operations in map'
      },
      examples: {
        badCode: `// ❌ N+1 in map
const enrichedUsers = users.map(async user => ({
  ...user,
  profile: await getProfile(user.id) // N queries!
}));`,
        goodCode: `// ✅ Batch approach
const userIds = users.map(u => u.id);
const profiles = await getProfilesBatch(userIds);
const enrichedUsers = users.map(user => ({
  ...user,
  profile: profiles[user.id]
}));`,
        explanation: 'Batch fetch all profiles first, then map synchronously'
      }
    };
  }

  private async checkNPlusOneInForEach(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'n_plus_one',
      severity: 'critical',
      title: 'N+1 Query in forEach',
      description: 'forEach with database queries creates sequential bottleneck',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 8000,
        memoryGrowth: 75,
        responseTimeIncrease: 200,
        estimatedBreakingPoint: '30-75 items'
      },
      recommendation: {
        solution: 'Replace with bulk operations or batch processing',
        priority: 'immediate',
        estimatedFixTime: '2-3 hours',
        preventionStrategy: 'Database access layer with automatic batching'
      },
      examples: {
        badCode: `// ❌ Sequential queries
users.forEach(async user => {
  await updateUserStats(user.id); // N separate updates!
});`,
        goodCode: `// ✅ Bulk update
const userIds = users.map(u => u.id);
await updateUserStatsBulk(userIds);`,
        explanation: 'Single bulk operation instead of N individual updates'
      }
    };
  }

  /**
   * Memory Leak Detection Methods
   */
  private async checkUnmanagedConnections(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    if (!match.includes('close') && !match.includes('release') && !match.includes('end')) {
      return {
        id: '',
        type: 'memory_leak',
        severity: 'high',
        title: 'Unclosed Database Connection',
        description: 'Database connections not properly closed will exhaust connection pool',
        location: {
          file: request.filePath || 'code snippet',
          codeSnippet: match
        },
        impact: {
          loadIncrease: 2000,
          memoryGrowth: 200,
          responseTimeIncrease: 50,
          estimatedBreakingPoint: '100-200 concurrent operations'
        },
        recommendation: {
          solution: 'Use try/finally blocks or connection pooling with auto-cleanup',
          priority: 'immediate',
          estimatedFixTime: '1 hour',
          preventionStrategy: 'Use ORM or database library with automatic connection management'
        },
        examples: {
          badCode: `// ❌ Connection leak
const connection = await pool.getConnection();
const result = await connection.query('SELECT * FROM users');
return result; // Connection never closed!`,
          goodCode: `// ✅ Proper cleanup
const connection = await pool.getConnection();
try {
  const result = await connection.query('SELECT * FROM users');
  return result;
} finally {
  connection.release(); // Always cleanup
}`,
          explanation: 'Always release connections back to pool, even if errors occur'
        }
      };
    }
    return null;
  }

  private async checkEventListenerLeaks(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'memory_leak',
      severity: 'medium',
      title: 'Potential Event Listener Leak',
      description: 'Event listeners without cleanup accumulate over time',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 300,
        memoryGrowth: 10,
        responseTimeIncrease: 5,
        estimatedBreakingPoint: '1000+ component instances'
      },
      recommendation: {
        solution: 'Remove listeners in cleanup/unmount methods',
        priority: 'next_sprint',
        estimatedFixTime: '30 minutes',
        preventionStrategy: 'Use framework-specific lifecycle methods or AbortController'
      },
      examples: {
        badCode: `// ❌ Listener leak
element.addEventListener('click', handler);
// No cleanup when component unmounts`,
        goodCode: `// ✅ Proper cleanup
const controller = new AbortController();
element.addEventListener('click', handler, { 
  signal: controller.signal 
});
// Later: controller.abort(); // Removes listener`,
        explanation: 'Use AbortController or manual removeEventListener for cleanup'
      }
    };
  }

  private async checkGlobalVariableGrowth(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'memory_leak',
      severity: 'medium',
      title: 'Global Variable Growth',
      description: 'Global variables that grow without bounds cause memory leaks',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 500,
        memoryGrowth: 50,
        responseTimeIncrease: 10,
        estimatedBreakingPoint: 'Depends on growth rate'
      },
      recommendation: {
        solution: 'Implement size limits, cleanup strategies, or use local variables',
        priority: 'next_sprint',
        estimatedFixTime: '1-2 hours',
        preventionStrategy: 'Avoid global state, use proper state management'
      },
      examples: {
        badCode: `// ❌ Growing global cache
global.cache = global.cache || [];
global.cache.push(newData); // Grows forever!`,
        goodCode: `// ✅ LRU cache with limits
const cache = new LRUCache({ max: 1000 });
cache.set(key, value); // Auto-evicts old entries`,
        explanation: 'Use bounded collections that automatically clean up old data'
      }
    };
  }

  /**
   * Inefficient Algorithm Detection Methods
   */
  private async checkNestedLoops(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'inefficient_algorithm',
      severity: 'high',
      title: 'Nested Loops - O(n²) Complexity',
      description: 'Nested loops scale quadratically, becoming extremely slow with large datasets',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 10000,
        memoryGrowth: 20,
        responseTimeIncrease: 1000,
        estimatedBreakingPoint: '1000+ items'
      },
      recommendation: {
        solution: 'Use hash maps, sets, or sorting for O(n log n) or O(n) complexity',
        priority: 'immediate',
        estimatedFixTime: '2-4 hours',
        preventionStrategy: 'Algorithm complexity review in code reviews'
      },
      examples: {
        badCode: `// ❌ O(n²) nested loops
for (const user of users) {
  for (const order of orders) {
    if (order.userId === user.id) {
      user.orders.push(order);
    }
  }
}`,
        goodCode: `// ✅ O(n) hash map approach
const ordersByUserId = groupBy(orders, 'userId');
users.forEach(user => {
  user.orders = ordersByUserId[user.id] || [];
});`,
        explanation: 'Create lookup map once, then access in O(1) time per user'
      }
    };
  }

  private async checkLinearSearchInLoops(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'inefficient_algorithm',
      severity: 'medium',
      title: 'Linear Search in Loop',
      description: 'Repeated linear searches create O(n²) behavior',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 2500,
        memoryGrowth: 5,
        responseTimeIncrease: 250,
        estimatedBreakingPoint: '500+ items'
      },
      recommendation: {
        solution: 'Create lookup maps or sets outside the loop',
        priority: 'next_sprint',
        estimatedFixTime: '1 hour',
        preventionStrategy: 'Prefer Map/Set over Array.find in performance-critical code'
      },
      examples: {
        badCode: `// ❌ Repeated linear search
results = items.map(item => {
  return lookup.find(l => l.id === item.id); // O(n) per item
});`,
        goodCode: `// ✅ Hash map lookup
const lookupMap = new Map(lookup.map(l => [l.id, l]));
results = items.map(item => {
  return lookupMap.get(item.id); // O(1) per item
});`,
        explanation: 'Build lookup map once, then access in constant time'
      }
    };
  }

  private async checkRepeatedCalculations(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'inefficient_algorithm',
      severity: 'medium',
      title: 'Repeated Expensive Calculations',
      description: 'Expensive operations repeated unnecessarily in loops',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 1000,
        memoryGrowth: 10,
        responseTimeIncrease: 100,
        estimatedBreakingPoint: '100+ iterations'
      },
      recommendation: {
        solution: 'Cache expensive calculations outside loops',
        priority: 'backlog',
        estimatedFixTime: '30 minutes',
        preventionStrategy: 'Move expensive operations outside loops where possible'
      },
      examples: {
        badCode: `// ❌ Repeated expensive calculation
for (const item of items) {
  const hash = crypto.createHash('sha256')
    .update(item.data)
    .digest('hex'); // Expensive!
}`,
        goodCode: `// ✅ Optimized calculation
const hasher = crypto.createHash('sha256');
for (const item of items) {
  hasher.update(item.data);
}
const hash = hasher.digest('hex');`,
        explanation: 'Reuse expensive objects and batch operations when possible'
      }
    };
  }

  /**
   * Blocking Operations Detection
   */
  private async checkSyncFileOperations(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'blocking_operation',
      severity: 'high',
      title: 'Synchronous File Operation',
      description: 'Sync file operations block the event loop, preventing other requests',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 0,
        memoryGrowth: 0,
        responseTimeIncrease: 1000,
        estimatedBreakingPoint: '10+ concurrent users'
      },
      recommendation: {
        solution: 'Replace with async file operations',
        priority: 'immediate',
        estimatedFixTime: '15 minutes',
        preventionStrategy: 'Lint rule to ban sync file operations'
      },
      examples: {
        badCode: `// ❌ Blocks event loop
const data = fs.readFileSync('large-file.json');
return JSON.parse(data);`,
        goodCode: `// ✅ Non-blocking
const data = await fs.promises.readFile('large-file.json');
return JSON.parse(data);`,
        explanation: 'Async operations allow other requests to be processed while waiting for I/O'
      }
    };
  }

  private async checkSyncNetworkCalls(match: string, code: string, request: ScalingAnalysisRequest): Promise<ScalingIssue | null> {
    return {
      id: '',
      type: 'blocking_operation',
      severity: 'critical',
      title: 'Synchronous Network Call',
      description: 'Sync network calls completely block the server',
      location: {
        file: request.filePath || 'code snippet',
        codeSnippet: match
      },
      impact: {
        loadIncrease: 0,
        memoryGrowth: 0,
        responseTimeIncrease: 5000,
        estimatedBreakingPoint: '1 concurrent user'
      },
      recommendation: {
        solution: 'Use async/await for all network operations',
        priority: 'immediate',
        estimatedFixTime: '30 minutes',
        preventionStrategy: 'Use HTTP clients that default to async operations'
      },
      examples: {
        badCode: `// ❌ Completely blocks server
const xhr = new XMLHttpRequest();
xhr.open('GET', url, false); // Sync mode!
xhr.send();`,
        goodCode: `// ✅ Non-blocking
const response = await fetch(url);
const data = await response.json();`,
        explanation: 'Always use async network operations in server environments'
      }
    };
  }

  /**
   * Helper methods
   */
  private async getCodeFromFile(filePath?: string): Promise<string | null> {
    if (!filePath) return null;
    
    try {
      const fs = await import('fs/promises');
      return await fs.readFile(filePath, 'utf-8');
    } catch (error) {
      console.warn(`Could not read file ${filePath}:`, error);
      return null;
    }
  }

  private calculateOverallRisk(issues: ScalingIssue[]): 'low' | 'medium' | 'high' | 'critical' {
    if (issues.some(i => i.severity === 'critical')) return 'critical';
    if (issues.some(i => i.severity === 'high')) return 'high';
    if (issues.some(i => i.severity === 'medium')) return 'medium';
    return 'low';
  }

  private estimateUserCapacity(issues: ScalingIssue[]): number {
    if (issues.length === 0) return 10000;
    
    const criticalIssues = issues.filter(i => i.severity === 'critical');
    if (criticalIssues.length > 0) return 50;
    
    const highIssues = issues.filter(i => i.severity === 'high');
    if (highIssues.length > 0) return 200;
    
    const mediumIssues = issues.filter(i => i.severity === 'medium');
    if (mediumIssues.length > 0) return 1000;
    
    return 5000;
  }

  private generateRecommendedActions(issues: ScalingIssue[]): string[] {
    const actions: string[] = [];
    
    const immediateIssues = issues.filter(i => i.recommendation.priority === 'immediate');
    if (immediateIssues.length > 0) {
      actions.push(`Fix ${immediateIssues.length} immediate scaling issue(s) before deployment`);
    }
    
    const nPlusOneIssues = issues.filter(i => i.type === 'n_plus_one');
    if (nPlusOneIssues.length > 0) {
      actions.push('Implement database query optimization and caching strategy');
    }
    
    const memoryLeaks = issues.filter(i => i.type === 'memory_leak');
    if (memoryLeaks.length > 0) {
      actions.push('Add resource cleanup and monitoring');
    }
    
    const blockingOps = issues.filter(i => i.type === 'blocking_operation');
    if (blockingOps.length > 0) {
      actions.push('Replace all synchronous operations with async alternatives');
    }
    
    if (actions.length === 0) {
      actions.push('Code looks good for scaling - consider load testing');
    }
    
    return actions;
  }

  private calculateConfidence(issues: ScalingIssue[], code: string): number {
    let confidence = 0.7; // Base confidence
    
    // Higher confidence with more code to analyze
    if (code.length > 1000) confidence += 0.1;
    if (code.length > 5000) confidence += 0.1;
    
    // Higher confidence when issues are found
    if (issues.length > 0) confidence += 0.1;
    
    return Math.min(confidence, 1.0);
  }

  private displayAnalysisResult(result: ScalingAnalysisResult): void {
    const { issues, overallRisk, estimatedUserCapacity, analysisTime } = result;
    
    console.log(chalk.gray(`\n📊 Scaling Analysis Complete (${analysisTime}ms)`));
    console.log(chalk.gray(`   Confidence: ${Math.round(result.confidence * 100)}%`));
    
    // Risk level
    const riskColor = overallRisk === 'critical' ? chalk.red :
                     overallRisk === 'high' ? chalk.yellow :
                     overallRisk === 'medium' ? chalk.blue : chalk.green;
    
    console.log(riskColor(`\n🎯 Risk Level: ${overallRisk.toUpperCase()}`));
    console.log(chalk.gray(`   Estimated User Capacity: ${estimatedUserCapacity} concurrent users`));
    
    // Issues by type
    if (issues.length > 0) {
      const byType = issues.reduce((acc, issue) => {
        acc[issue.type] = (acc[issue.type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      console.log(chalk.red(`\n🚨 Found ${issues.length} scaling issue(s):`));
      Object.entries(byType).forEach(([type, count]) => {
        const emoji = type === 'n_plus_one' ? '💥' :
                     type === 'memory_leak' ? '🧠' :
                     type === 'inefficient_algorithm' ? '🐌' : '🚫';
        console.log(chalk.red(`   ${emoji} ${type.replace('_', ' ')}: ${count}`));
      });
      
      // Show top 3 critical issues
      const criticalIssues = issues
        .filter(i => i.severity === 'critical' || i.severity === 'high')
        .slice(0, 3);
        
      if (criticalIssues.length > 0) {
        console.log(chalk.red(`\n🔥 Critical Issues:`));
        criticalIssues.forEach(issue => {
          console.log(chalk.red(`   • ${issue.title}`));
          console.log(chalk.gray(`     Impact: ${issue.impact.estimatedBreakingPoint}`));
          console.log(chalk.cyan(`     Fix: ${issue.recommendation.solution}`));
        });
      }
    } else {
      console.log(chalk.green(`\n✅ No scaling issues detected!`));
    }
    
    // Recommended actions
    if (result.recommendedActions.length > 0) {
      console.log(chalk.blue(`\n💡 Recommended Actions:`));
      result.recommendedActions.forEach(action => {
        console.log(chalk.blue(`   • ${action}`));
      });
    }
  }

  private generateAnalysisId(): string {
    return `scale_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;
  }

  /**
   * Public API methods
   */
  
  getAnalysisHistory(): ScalingAnalysisResult[] {
    return this.analysisHistory;
  }
  
  getDetectionRules(): string[] {
    return Array.from(this.detectionRules.keys());
  }
}

interface DetectionRule {
  name: string;
  pattern: RegExp;
  severity: 'low' | 'medium' | 'high' | 'critical';
  check: (match: string, code: string, request: ScalingAnalysisRequest) => Promise<ScalingIssue | null>;
  recommendation: string;
}

export default ScalingDetector;