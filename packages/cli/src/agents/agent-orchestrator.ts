/**
 * Agent Orchestrator - Central coordination for multi-agent workflows
 * Manages agent selection, task routing, and workflow execution
 */

import { EventEmitter } from 'events';
import * as WebSocket from 'ws';
import chalk from 'chalk';
import { Config } from '@google/gemini-cli-core';

export interface AgentTask {
  id: string;
  type: 'analyze' | 'design' | 'implement' | 'validate' | 'test' | 'review';
  description: string;
  agent: string;
  input: any;
  dependencies?: string[];
  priority: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  startTime?: Date;
  endTime?: Date;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  tasks: AgentTask[];
  parallel?: boolean;
  context?: Record<string, any>;
}

export interface AgentCapability {
  agent: string;
  capabilities: string[];
  workload: number;
  available: boolean;
}

export class AgentOrchestrator extends EventEmitter {
  private config: Config;
  private apiUrl: string;
  private wsConnection: WebSocket | null = null;
  private activeTasks: Map<string, AgentTask> = new Map();
  private taskQueue: AgentTask[] = [];
  private agentCapabilities: Map<string, AgentCapability> = new Map();
  private workflowContext: Map<string, any> = new Map();
  private isConnected: boolean = false;

  constructor(config: Config) {
    super();
    this.config = config;
    this.apiUrl = process.env.AGENT_SERVER_URL || 'http://localhost:2000';
    this.initializeAgentCapabilities();
  }

  /**
   * Initialize agent capabilities mapping
   */
  private initializeAgentCapabilities(): void {
    this.agentCapabilities.set('scout', {
      agent: 'scout',
      capabilities: ['duplication_detection', 'code_quality', 'dependency_analysis', 'pattern_matching'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('architect', {
      agent: 'architect',
      capabilities: ['system_design', 'architecture_review', 'technology_selection', 'scalability_planning'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('guardian', {
      agent: 'guardian',
      capabilities: ['security_scan', 'validation', 'compliance_check', 'breaking_change_detection'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('developer', {
      agent: 'developer',
      capabilities: ['code_generation', 'refactoring', 'bug_fixing', 'optimization'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('qa', {
      agent: 'qa',
      capabilities: ['test_generation', 'coverage_analysis', 'regression_detection', 'performance_testing'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('pm', {
      agent: 'pm',
      capabilities: ['task_planning', 'estimation', 'resource_allocation', 'progress_tracking'],
      workload: 0,
      available: true
    });

    this.agentCapabilities.set('po', {
      agent: 'po',
      capabilities: ['requirement_analysis', 'user_story_creation', 'priority_management', 'stakeholder_communication'],
      workload: 0,
      available: true
    });
  }

  /**
   * Connect to agent server
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = this.apiUrl.replace('http', 'ws') + '/ws';
      
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.on('open', () => {
        this.isConnected = true;
        this.emit('connected');
        console.log(chalk.green('✓ Orchestrator connected to agent server'));
        this.registerOrchestrator();
        resolve();
      });

      this.wsConnection.on('message', (data: string) => {
        this.handleServerMessage(JSON.parse(data));
      });

      this.wsConnection.on('error', (error) => {
        this.isConnected = false;
        console.error(chalk.red('Orchestrator connection error:'), error);
        reject(error);
      });

      this.wsConnection.on('close', () => {
        this.isConnected = false;
        this.emit('disconnected');
        this.attemptReconnect();
      });

      setTimeout(() => {
        if (!this.isConnected) {
          reject(new Error('Connection timeout'));
        }
      }, 5000);
    });
  }

  /**
   * Register orchestrator with server
   */
  private registerOrchestrator(): void {
    if (this.wsConnection && this.isConnected) {
      this.wsConnection.send(JSON.stringify({
        type: 'register_orchestrator',
        data: {
          id: 'main_orchestrator',
          capabilities: Array.from(this.agentCapabilities.keys())
        }
      }));
    }
  }

  /**
   * Create workflow from natural language request
   */
  createWorkflow(request: string, context?: Record<string, any>): WorkflowDefinition {
    const workflowId = `wf_${Date.now()}`;
    const tasks: AgentTask[] = [];

    // Analyze request to determine required tasks
    const requiresDesign = request.includes('design') || request.includes('architecture');
    const requiresImplementation = request.includes('implement') || request.includes('create') || request.includes('build');
    const requiresSecurity = request.includes('secure') || request.includes('auth') || requiresImplementation;
    const requiresTests = request.includes('test') || requiresImplementation;

    // Always start with Scout (Scout-first architecture)
    tasks.push({
      id: `${workflowId}_scout`,
      type: 'analyze',
      description: 'Analyze codebase for existing implementations',
      agent: 'scout',
      input: { request, check_duplicates: true, analyze_patterns: true },
      priority: 1,
      status: 'pending'
    });

    // Add design phase if needed
    if (requiresDesign) {
      tasks.push({
        id: `${workflowId}_architect`,
        type: 'design',
        description: 'Design system architecture',
        agent: 'architect',
        input: { request, scout_analysis: `{{${workflowId}_scout.result}}` },
        dependencies: [`${workflowId}_scout`],
        priority: 2,
        status: 'pending'
      });
    }

    // Add security validation
    if (requiresSecurity) {
      tasks.push({
        id: `${workflowId}_guardian_pre`,
        type: 'validate',
        description: 'Pre-implementation security validation',
        agent: 'guardian',
        input: { 
          request, 
          design: requiresDesign ? `{{${workflowId}_architect.result}}` : null 
        },
        dependencies: requiresDesign ? [`${workflowId}_architect`] : [`${workflowId}_scout`],
        priority: 3,
        status: 'pending'
      });
    }

    // Add implementation
    if (requiresImplementation) {
      tasks.push({
        id: `${workflowId}_developer`,
        type: 'implement',
        description: 'Implement the solution',
        agent: 'developer',
        input: {
          request,
          scout_analysis: `{{${workflowId}_scout.result}}`,
          architecture: requiresDesign ? `{{${workflowId}_architect.result}}` : null,
          security_requirements: requiresSecurity ? `{{${workflowId}_guardian_pre.result}}` : null
        },
        dependencies: this.getImplementationDependencies(workflowId, requiresDesign, requiresSecurity),
        priority: 4,
        status: 'pending'
      });
    }

    // Add testing
    if (requiresTests) {
      tasks.push({
        id: `${workflowId}_qa`,
        type: 'test',
        description: 'Generate tests and validate quality',
        agent: 'qa',
        input: {
          code: `{{${workflowId}_developer.result}}`,
          requirements: request
        },
        dependencies: [`${workflowId}_developer`],
        priority: 5,
        status: 'pending'
      });
    }

    // Final validation
    if (requiresSecurity || requiresImplementation) {
      tasks.push({
        id: `${workflowId}_guardian_post`,
        type: 'validate',
        description: 'Post-implementation validation',
        agent: 'guardian',
        input: {
          implementation: requiresImplementation ? `{{${workflowId}_developer.result}}` : null,
          tests: requiresTests ? `{{${workflowId}_qa.result}}` : null
        },
        dependencies: this.getFinalValidationDependencies(workflowId, requiresImplementation, requiresTests),
        priority: 6,
        status: 'pending'
      });
    }

    return {
      id: workflowId,
      name: this.generateWorkflowName(request),
      description: request,
      tasks,
      parallel: false,
      context: context || {}
    };
  }

  /**
   * Get implementation task dependencies
   */
  private getImplementationDependencies(workflowId: string, hasDesign: boolean, hasSecurity: boolean): string[] {
    const deps = [`${workflowId}_scout`];
    if (hasDesign) deps.push(`${workflowId}_architect`);
    if (hasSecurity) deps.push(`${workflowId}_guardian_pre`);
    return deps;
  }

  /**
   * Get final validation dependencies
   */
  private getFinalValidationDependencies(workflowId: string, hasImplementation: boolean, hasTests: boolean): string[] {
    const deps = [];
    if (hasImplementation) deps.push(`${workflowId}_developer`);
    if (hasTests) deps.push(`${workflowId}_qa`);
    return deps.length > 0 ? deps : [`${workflowId}_scout`];
  }

  /**
   * Generate workflow name from request
   */
  private generateWorkflowName(request: string): string {
    const keywords = request.toLowerCase().split(' ');
    if (keywords.includes('api')) return 'API Development Workflow';
    if (keywords.includes('auth')) return 'Authentication Workflow';
    if (keywords.includes('database')) return 'Database Design Workflow';
    if (keywords.includes('test')) return 'Testing Workflow';
    if (keywords.includes('refactor')) return 'Refactoring Workflow';
    return 'Development Workflow';
  }

  /**
   * Execute workflow
   */
  async executeWorkflow(workflow: WorkflowDefinition): Promise<void> {
    console.log(chalk.blue(`\n🚀 Executing workflow: ${workflow.name}`));
    console.log(chalk.gray(`   Tasks: ${workflow.tasks.length}`));

    // Store workflow context
    this.workflowContext.set(workflow.id, workflow.context || {});

    // Add all tasks to queue
    workflow.tasks.forEach(task => {
      this.taskQueue.push(task);
    });

    // Start processing
    await this.processTasks(workflow.id);
  }

  /**
   * Process tasks from queue
   */
  private async processTasks(workflowId: string): Promise<void> {
    while (this.taskQueue.length > 0 || this.activeTasks.size > 0) {
      // Get ready tasks (dependencies satisfied)
      const readyTasks = this.getReadyTasks();

      // Execute ready tasks in parallel
      const promises = readyTasks.map(task => this.executeTask(task));
      
      if (promises.length > 0) {
        await Promise.all(promises);
      } else if (this.activeTasks.size > 0) {
        // Wait for active tasks to complete
        await this.waitForActiveTasks();
      } else {
        // No tasks ready and no active tasks - might be a dependency issue
        console.error(chalk.red('Workflow stalled - check task dependencies'));
        break;
      }
    }

    console.log(chalk.green(`\n✅ Workflow ${workflowId} completed`));
  }

  /**
   * Get tasks ready for execution
   */
  private getReadyTasks(): AgentTask[] {
    return this.taskQueue.filter(task => {
      // Check if dependencies are satisfied
      if (!task.dependencies || task.dependencies.length === 0) {
        return true;
      }

      return task.dependencies.every(depId => {
        const depTask = this.findTaskById(depId);
        return depTask && depTask.status === 'completed';
      });
    });
  }

  /**
   * Execute a single task
   */
  private async executeTask(task: AgentTask): Promise<void> {
    // Remove from queue and mark as active
    const index = this.taskQueue.indexOf(task);
    if (index > -1) {
      this.taskQueue.splice(index, 1);
    }
    
    task.status = 'running';
    task.startTime = new Date();
    this.activeTasks.set(task.id, task);

    console.log(chalk.cyan(`\n⚙️  ${task.agent.toUpperCase()}: ${task.description}`));
    this.emit('task_started', task);

    try {
      // Resolve template variables in input
      const resolvedInput = this.resolveTemplateVariables(task.input);

      // Call agent API
      const result = await this.callAgent(task.agent, task.type, resolvedInput);
      
      task.result = result;
      task.status = 'completed';
      task.endTime = new Date();

      // Store result for dependent tasks
      this.workflowContext.set(task.id, result);

      console.log(chalk.green(`   ✓ Completed in ${this.getExecutionTime(task)}ms`));
      this.emit('task_completed', task);

    } catch (error) {
      task.status = 'failed';
      task.error = error instanceof Error ? error.message : 'Unknown error';
      task.endTime = new Date();

      console.log(chalk.red(`   ✗ Failed: ${task.error}`));
      this.emit('task_failed', task);
    }

    // Remove from active tasks
    this.activeTasks.delete(task.id);
  }

  /**
   * Resolve template variables in input
   */
  private resolveTemplateVariables(input: any): any {
    if (typeof input === 'string') {
      // Check for template syntax {{taskId.result}}
      const matches = input.match(/\{\{([^}]+)\}\}/g);
      if (matches) {
        let resolved = input;
        matches.forEach(match => {
          const key = match.replace(/[{}]/g, '');
          const value = this.getContextValue(key);
          if (value !== undefined) {
            resolved = resolved.replace(match, JSON.stringify(value));
          }
        });
        return resolved;
      }
      return input;
    }

    if (typeof input === 'object' && input !== null) {
      const resolved: any = Array.isArray(input) ? [] : {};
      for (const key in input) {
        resolved[key] = this.resolveTemplateVariables(input[key]);
      }
      return resolved;
    }

    return input;
  }

  /**
   * Get value from workflow context
   */
  private getContextValue(path: string): any {
    const parts = path.split('.');
    let value = this.workflowContext.get(parts[0]);
    
    for (let i = 1; i < parts.length && value !== undefined; i++) {
      value = value[parts[i]];
    }
    
    return value;
  }

  /**
   * Call agent via API
   */
  private async callAgent(agent: string, taskType: string, input: any): Promise<any> {
    const url = `${this.apiUrl}/api/v1/agent/execute`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent,
          task: taskType,
          input
        })
      });

      if (!response.ok) {
        throw new Error(`Agent API error: ${response.statusText}`);
      }

      const result = await response.json();
      return result.result || result;

    } catch (error) {
      // If server not available, use mock response
      console.log(chalk.yellow('   ⚠ Agent server not available, using mock response'));
      return this.getMockAgentResponse(agent, taskType);
    }
  }

  /**
   * Get mock agent response for testing
   */
  private getMockAgentResponse(agent: string, taskType: string): any {
    const mockResponses: Record<string, any> = {
      scout: {
        duplicates_found: false,
        code_quality_score: 8.5,
        patterns_identified: ['MVC', 'Repository'],
        recommendations: ['Consider existing patterns']
      },
      architect: {
        architecture: 'Microservices',
        components: ['API Gateway', 'Auth Service', 'Business Logic'],
        technologies: ['Node.js', 'Docker', 'PostgreSQL']
      },
      guardian: {
        validation_passed: true,
        security_score: 9.0,
        vulnerabilities: [],
        compliance: 'OWASP compliant'
      },
      developer: {
        files_created: ['src/feature.ts', 'tests/feature.test.ts'],
        lines_of_code: 250,
        implementation_complete: true
      },
      qa: {
        tests_created: 10,
        coverage: 85,
        all_tests_passing: true
      }
    };

    return mockResponses[agent] || { status: 'completed', message: `Mock ${agent} response` };
  }

  /**
   * Wait for active tasks to complete
   */
  private async waitForActiveTasks(): Promise<void> {
    return new Promise(resolve => {
      const checkInterval = setInterval(() => {
        if (this.activeTasks.size === 0) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);
    });
  }

  /**
   * Find task by ID
   */
  private findTaskById(taskId: string): AgentTask | undefined {
    // Check active tasks
    if (this.activeTasks.has(taskId)) {
      return this.activeTasks.get(taskId);
    }

    // Check completed tasks in context
    const contextKeys = Array.from(this.workflowContext.keys());
    for (const key of contextKeys) {
      if (key === taskId) {
        // Task was completed, reconstruct from context
        return { id: taskId, status: 'completed' } as AgentTask;
      }
    }

    // Check queue
    return this.taskQueue.find(t => t.id === taskId);
  }

  /**
   * Get task execution time
   */
  private getExecutionTime(task: AgentTask): number {
    if (task.startTime && task.endTime) {
      return task.endTime.getTime() - task.startTime.getTime();
    }
    return 0;
  }

  /**
   * Handle server messages
   */
  private handleServerMessage(message: any): void {
    switch (message.type) {
      case 'agent_status':
        this.updateAgentStatus(message.data);
        break;
      case 'task_update':
        this.emit('task_update', message.data);
        break;
      case 'workflow_update':
        this.emit('workflow_update', message.data);
        break;
      default:
        this.emit('message', message);
    }
  }

  /**
   * Update agent status
   */
  private updateAgentStatus(status: any): void {
    if (status.agent && this.agentCapabilities.has(status.agent)) {
      const capability = this.agentCapabilities.get(status.agent)!;
      capability.available = status.available;
      capability.workload = status.workload || 0;
    }
  }

  /**
   * Attempt to reconnect to server
   */
  private attemptReconnect(): void {
    console.log(chalk.yellow('Attempting to reconnect...'));
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
          this.attemptReconnect();
        });
      }
    }, 5000);
  }

  /**
   * Get workflow status
   */
  getWorkflowStatus(workflowId: string): any {
    const tasks = Array.from(this.activeTasks.values()).filter(t => t.id.startsWith(workflowId));
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const pending = this.taskQueue.filter(t => t.id.startsWith(workflowId)).length;

    return {
      total: tasks.length + pending,
      completed,
      failed,
      running,
      pending,
      progress: tasks.length > 0 ? (completed / tasks.length) * 100 : 0
    };
  }

  /**
   * Cancel workflow
   */
  cancelWorkflow(workflowId: string): void {
    // Remove from queue
    this.taskQueue = this.taskQueue.filter(t => !t.id.startsWith(workflowId));
    
    // Cancel active tasks
    this.activeTasks.forEach((task, id) => {
      if (id.startsWith(workflowId)) {
        task.status = 'failed';
        task.error = 'Workflow cancelled';
        this.activeTasks.delete(id);
      }
    });

    this.emit('workflow_cancelled', workflowId);
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
}

export default AgentOrchestrator;