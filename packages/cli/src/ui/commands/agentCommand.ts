/**
 * Agent Command - Main integration point for agent orchestration in CLI
 * Provides slash commands for agent operations
 */

import { SlashCommand, CommandContext } from './types.js';
import { NaturalLanguageCLI } from '../../agents/natural-language-cli.js';
import { AgentOrchestrator } from '../../agents/agent-orchestrator.js';
import { RealTimeStatusManager } from '../../agents/real-time-status.js';
import { ScoutPipeline, ScoutAnalysisRequest } from '../../agents/scout-pipeline.js';
import chalk from 'chalk';

let nlCLI: NaturalLanguageCLI | null = null;
let orchestrator: AgentOrchestrator | null = null;
let statusManager: RealTimeStatusManager | null = null;
let scoutPipeline: ScoutPipeline | null = null;
let isInitialized = false;

/**
 * Initialize agent systems
 */
async function initializeAgentSystems(context: CommandContext): Promise<boolean> {
  if (isInitialized) {
    return true;
  }

  try {
    context.addMessage({
      type: 'system',
      text: chalk.blue('🚀 Initializing agent systems...')
    });

    // Initialize status manager
    statusManager = new RealTimeStatusManager();
    statusManager.setDisplayMode('simple');

    // Initialize natural language CLI
    nlCLI = new NaturalLanguageCLI(context.config);
    
    // Initialize orchestrator
    orchestrator = new AgentOrchestrator(context.config);
    
    // Initialize Scout pipeline
    const projectRoot = context.config?.getProjectRoot() || process.cwd();
    scoutPipeline = new ScoutPipeline(projectRoot);

    // Setup event handlers
    setupEventHandlers(context);

    // Try to connect to agent server
    try {
      await Promise.all([
        nlCLI.connect(),
        orchestrator.connect()
      ]);

      context.addMessage({
        type: 'success',
        text: chalk.green('✓ Connected to agent server - Full intelligence mode active')
      });
    } catch (error) {
      context.addMessage({
        type: 'warning',
        text: chalk.yellow('⚠ Agent server not available - Running in basic mode')
      });
      context.addMessage({
        type: 'info',
        text: chalk.gray('Start the agent server with: ./start_server.sh')
      });
    }

    isInitialized = true;
    return true;

  } catch (error) {
    context.addMessage({
      type: 'error',
      text: `Failed to initialize agent systems: ${error}`
    });
    return false;
  }
}

/**
 * Setup event handlers for agent systems
 */
function setupEventHandlers(context: CommandContext): void {
  if (!nlCLI || !orchestrator || !statusManager) return;

  // Natural Language CLI events
  nlCLI.on('status', (data) => {
    statusManager!.displayStatus({
      type: 'info',
      agent: data.agent,
      message: data.message,
      timestamp: new Date()
    });
  });

  nlCLI.on('agent_response', (data) => {
    context.addMessage({
      type: 'assistant',
      text: formatAgentResponse(data)
    });
  });

  nlCLI.on('warning', (data) => {
    statusManager!.displayStatus({
      type: 'warning',
      message: data.message,
      details: data.details,
      timestamp: new Date()
    });
  });

  nlCLI.on('duplicates_found', (duplicates) => {
    context.addMessage({
      type: 'warning',
      text: chalk.yellow('⚠ Scout found existing similar code:')
    });
    duplicates.forEach((dup: any) => {
      context.addMessage({
        type: 'info',
        text: `  ${dup.file}: ${dup.similarity}% similar (lines ${dup.lines.join('-')})`
      });
    });
  });

  nlCLI.on('confirm_required', ({ message, callback }) => {
    context.requestConfirmation(message).then(callback);
  });

  // Orchestrator events
  orchestrator.on('task_started', (task) => {
    statusManager!.startSpinner(task.id, task.description, task.agent);
  });

  orchestrator.on('task_completed', (task) => {
    statusManager!.succeedSpinner(task.id, `✓ ${task.description}`);
  });

  orchestrator.on('task_failed', (task) => {
    statusManager!.failSpinner(task.id, `✗ ${task.description}: ${task.error}`);
  });

  orchestrator.on('workflow_update', (status) => {
    statusManager!.displayWorkflowProgress(status.workflowId, status);
  });

  // Status manager events
  statusManager.on('status_update', (update) => {
    // Log to context if needed
    if (context.config?.getDebugMode()) {
      context.addDebugMessage(`[${update.agent || 'system'}] ${update.message}`);
    }
  });

  // Scout pipeline events
  scoutPipeline!.on('analysis_started', ({ requestId, operation }) => {
    statusManager!.displayStatus({
      type: 'info',
      agent: 'Scout',
      message: `🔍 Analyzing: ${operation}`,
      timestamp: new Date()
    });
  });

  scoutPipeline!.on('analysis_completed', (result) => {
    if (!result.shouldProceed) {
      context.addMessage({
        type: 'warning',
        text: chalk.red('🛑 Scout recommends reviewing findings before proceeding')
      });
    }
    
    if (result.duplications.length > 0) {
      context.addMessage({
        type: 'warning',
        text: chalk.yellow(`⚠ Found ${result.duplications.length} potential duplication(s)`)
      });
    }
  });

  scoutPipeline!.on('analysis_failed', ({ requestId, error }) => {
    context.addMessage({
      type: 'warning',
      text: chalk.yellow('⚠ Scout analysis failed, proceeding without pre-check')
    });
  });
}

/**
 * Format agent response for display
 */
function formatAgentResponse(response: any): string {
  const lines: string[] = [];
  
  lines.push(chalk.cyan(`\n${response.persona.toUpperCase()} Agent Response:`));
  
  if (response.status === 'error') {
    lines.push(chalk.red(`Error: ${response.result.error}`));
  } else {
    if (typeof response.result === 'object') {
      for (const [key, value] of Object.entries(response.result)) {
        lines.push(`  ${key}: ${formatValue(value)}`);
      }
    } else {
      lines.push(`  ${response.result}`);
    }
  }

  if (response.executionTime) {
    lines.push(chalk.gray(`  Execution time: ${response.executionTime}ms`));
  }

  return lines.join('\n');
}

/**
 * Format value for display
 */
function formatValue(value: any): string {
  if (Array.isArray(value)) {
    return `\n${value.map(v => `    - ${v}`).join('\n')}`;
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2).split('\n').map(l => `    ${l}`).join('\n');
  }
  return String(value);
}

/**
 * Extract intent from natural language command
 */
function extractIntent(command: string): string {
  const lowercaseCommand = command.toLowerCase();
  
  if (lowercaseCommand.includes('implement') || lowercaseCommand.includes('create') || lowercaseCommand.includes('build')) {
    return 'implementation';
  }
  if (lowercaseCommand.includes('check') || lowercaseCommand.includes('analyze') || lowercaseCommand.includes('review')) {
    return 'analysis';
  }
  if (lowercaseCommand.includes('refactor') || lowercaseCommand.includes('improve') || lowercaseCommand.includes('optimize')) {
    return 'refactoring';
  }
  if (lowercaseCommand.includes('test') || lowercaseCommand.includes('unit test') || lowercaseCommand.includes('testing')) {
    return 'testing';
  }
  if (lowercaseCommand.includes('design') || lowercaseCommand.includes('architecture') || lowercaseCommand.includes('plan')) {
    return 'design';
  }
  if (lowercaseCommand.includes('security') || lowercaseCommand.includes('vulnerable') || lowercaseCommand.includes('secure')) {
    return 'security';
  }
  
  return 'general';
}

/**
 * Main agent command
 */
export const agentCommand: SlashCommand = {
  name: 'agent',
  description: 'Execute agent operations with natural language',
  pattern: /^\/agent(?:\s+(.+))?$/,
  help: `Usage: /agent <natural language command>
  
Examples:
  /agent check for duplicate authentication code
  /agent design a REST API for user management
  /agent implement a payment processing system
  /agent review code for security vulnerabilities
  /agent create unit tests for the auth module
  
Special commands:
  /agent status     - Show agent status summary
  /agent dashboard  - Open live status dashboard
  /agent workflow   - Show active workflows
  /agent help       - Show detailed help`,
  
  handler: async (context: CommandContext, args?: string) => {
    // Initialize if needed
    if (!isInitialized) {
      const success = await initializeAgentSystems(context);
      if (!success) {
        return { redraw: false };
      }
    }

    // Handle special commands
    if (!args || args.trim() === '') {
      context.addMessage({
        type: 'info',
        text: 'Please provide a command. Use "/agent help" for examples.'
      });
      return { redraw: true };
    }

    const command = args.trim().toLowerCase();

    if (command === 'help') {
      displayHelp(context);
      return { redraw: true };
    }

    if (command === 'status') {
      statusManager!.displayAgentSummary();
      return { redraw: true };
    }

    if (command === 'dashboard') {
      context.addMessage({
        type: 'info',
        text: 'Opening live dashboard... Press Ctrl+C to exit.'
      });
      statusManager!.startDashboard();
      return { redraw: false };
    }

    if (command === 'workflow' || command === 'workflows') {
      displayWorkflows(context);
      return { redraw: true };
    }

    // Process natural language command
    try {
      context.addMessage({
        type: 'user',
        text: args
      });

      // Scout-first workflow: Analyze command before execution
      const scoutRequest: ScoutAnalysisRequest = {
        operation: `Agent command: ${args}`,
        description: args,
        context: {
          intent: extractIntent(args),
          language: 'typescript',
          framework: 'nodejs'
        }
      };

      // Run Scout analysis first (unless explicitly skipped)
      const shouldSkipScout = args.toLowerCase().includes('skip scout');
      let scoutResult = null;
      
      if (!shouldSkipScout) {
        scoutResult = await scoutPipeline!.analyzeBeforeOperation(scoutRequest);
        
        // Check if Scout recommends not proceeding
        if (!scoutResult.shouldProceed) {
          const confirmed = await context.requestConfirmation(
            'Scout found issues. Continue anyway?'
          );
          if (!confirmed) {
            context.addMessage({
              type: 'info',
              text: chalk.yellow('Operation cancelled by user.')
            });
            return { redraw: true };
          }
        }
      }

      // Parse and process command
      await nlCLI!.processCommand(args);

      // If complex task, create and execute workflow
      const nlCommand = nlCLI!.parseCommand(args);
      if (nlCommand.requiresMultiAgent) {
        const workflow = orchestrator!.createWorkflow(args);
        
        context.addMessage({
          type: 'info',
          text: chalk.blue(`Created workflow: ${workflow.name} with ${workflow.tasks.length} tasks`)
        });

        await orchestrator!.executeWorkflow(workflow);
      }

    } catch (error) {
      context.addMessage({
        type: 'error',
        text: `Agent execution failed: ${error}`
      });
    }

    return { redraw: true };
  }
};

/**
 * Display detailed help
 */
function displayHelp(context: CommandContext): void {
  const helpText = `
${chalk.blue.bold('Gemini Agent System - Natural Language Commands')}

${chalk.yellow('Available Agents:')}
  ${chalk.cyan('Scout')}      - Duplication detection, code quality analysis
  ${chalk.cyan('Architect')}  - System design, architecture planning
  ${chalk.cyan('Guardian')}   - Security scanning, validation
  ${chalk.cyan('Developer')}  - Code generation, refactoring
  ${chalk.cyan('QA')}         - Test creation, quality assurance
  ${chalk.cyan('PM')}         - Project planning, task management
  ${chalk.cyan('PO')}         - Requirements analysis, user stories

${chalk.yellow('Example Commands:')}

${chalk.gray('# Check for duplicates before implementing')}
  /agent check if user authentication already exists

${chalk.gray('# Design and implement a feature')}
  /agent design and implement a REST API for product catalog

${chalk.gray('# Security review')}
  /agent scan the auth module for security vulnerabilities

${chalk.gray('# Generate tests')}
  /agent create comprehensive unit tests for payment processing

${chalk.gray('# Refactor code')}
  /agent refactor the database connection module for better performance

${chalk.yellow('Multi-Agent Workflows:')}
  Commands that include words like "review", "analyze", or "complete"
  will automatically trigger multi-agent workflows where agents
  collaborate to provide comprehensive solutions.

${chalk.yellow('Scout-First Architecture:')}
  All operations automatically run Scout analysis first to prevent
  code duplication, identify technical debt, and assess impact.
  Add "skip scout" to bypass this check for emergency operations.

${chalk.yellow('Tips:')}
  • Be specific in your requests for better results
  • Use domain terms (API, database, auth) for targeted help
  • Agent server must be running for full intelligence
  • Check /agent status to see agent availability`;

  context.addMessage({
    type: 'info',
    text: helpText
  });
}

/**
 * Display active workflows
 */
function displayWorkflows(context: CommandContext): void {
  // This would show active workflows from the orchestrator
  context.addMessage({
    type: 'info',
    text: 'No active workflows at the moment.'
  });
}

/**
 * Scout command - Quick duplication check
 */
export const scoutCommand: SlashCommand = {
  name: 'scout',
  description: 'Quick duplication and quality check',
  pattern: /^\/scout(?:\s+(.+))?$/,
  help: `Usage: /scout <file or description>
  
Examples:
  /scout authentication logic
  /scout payment processing module
  /scout src/utils/validation.ts`,
  
  handler: async (context: CommandContext, args?: string) => {
    if (!isInitialized) {
      await initializeAgentSystems(context);
    }

    if (!args) {
      context.addMessage({
        type: 'info',
        text: 'Please specify what to check. Example: /scout authentication logic'
      });
      return { redraw: true };
    }

    try {
      // Use Scout pipeline directly for analysis
      const scoutRequest: ScoutAnalysisRequest = {
        operation: 'Scout analysis',
        description: args,
        context: {
          filePath: args.includes('.') ? args : undefined,
          intent: extractIntent(args),
          language: 'typescript'
        }
      };

      context.addMessage({
        type: 'info',
        text: chalk.blue(`🔍 Running Scout analysis on: ${args}`)
      });

      const result = await scoutPipeline!.analyzeBeforeOperation(scoutRequest);

      // Display detailed results
      if (result.duplications.length > 0) {
        context.addMessage({
          type: 'warning',
          text: chalk.yellow(`\n🔍 Found ${result.duplications.length} potential duplication(s):`)
        });
        
        result.duplications.slice(0, 5).forEach((dup, index) => {
          const similarity = Math.round(dup.similarity * 100);
          context.addMessage({
            type: 'info',
            text: `  ${index + 1}. ${dup.filePath} (${similarity}% similar)\n     ${chalk.gray(dup.suggestion)}`
          });
        });

        if (result.duplications.length > 5) {
          context.addMessage({
            type: 'info',
            text: chalk.gray(`     ... and ${result.duplications.length - 5} more`)
          });
        }
      }

      if (result.technicalDebt.length > 0) {
        context.addMessage({
          type: 'warning',
          text: chalk.yellow(`\n⚠️ Found ${result.technicalDebt.length} technical debt issue(s):`)
        });
        
        result.technicalDebt.forEach((debt, index) => {
          const severityColor = debt.severity === 'critical' ? chalk.red :
                               debt.severity === 'error' ? chalk.red :
                               debt.severity === 'warning' ? chalk.yellow : chalk.blue;
          
          context.addMessage({
            type: 'info',
            text: `  ${index + 1}. ${severityColor(debt.severity.toUpperCase())}: ${debt.description}\n     ${chalk.gray(debt.recommendation)}`
          });
        });
      }

      if (result.suggestions.length > 0) {
        context.addMessage({
          type: 'info',
          text: chalk.cyan(`\n💡 Suggestions:\n${result.suggestions.map(s => `  • ${s}`).join('\n')}`)
        });
      }

      if (result.alternatives.length > 0) {
        context.addMessage({
          type: 'info',
          text: chalk.blue(`\n🔄 Alternatives:\n${result.alternatives.map(a => `  • ${a}`).join('\n')}`)
        });
      }

      // Summary
      const riskLevel = result.impactVisualization.riskScore > 60 ? 'high' :
                       result.impactVisualization.riskScore > 30 ? 'medium' : 'low';
      const riskColor = riskLevel === 'high' ? chalk.red :
                       riskLevel === 'medium' ? chalk.yellow : chalk.green;
      
      context.addMessage({
        type: 'info',
        text: `\n📊 Analysis Summary: ${riskColor(riskLevel.toUpperCase())} risk (${result.impactVisualization.riskScore}% score)`
      });

    } catch (error) {
      context.addMessage({
        type: 'error',
        text: `Scout analysis failed: ${error}`
      });
    }

    return { redraw: true };
  }
};

/**
 * Guardian command - Quick security check
 */
export const guardianCommand: SlashCommand = {
  name: 'guardian',
  description: 'Quick security validation',
  pattern: /^\/guardian(?:\s+(.+))?$/,
  help: 'Usage: /guardian <file or module>',
  
  handler: async (context: CommandContext, args?: string) => {
    if (!isInitialized) {
      await initializeAgentSystems(context);
    }

    if (!args) {
      context.addMessage({
        type: 'info',
        text: 'Please specify what to validate. Example: /guardian auth module'
      });
      return { redraw: true };
    }

    const command = `scan ${args} for security vulnerabilities`;
    await nlCLI!.processCommand(command);

    return { redraw: true };
  }
};

/**
 * Workflow command - Create custom workflow
 */
export const workflowCommand: SlashCommand = {
  name: 'workflow',
  description: 'Create and execute custom workflow',
  pattern: /^\/workflow(?:\s+(.+))?$/,
  help: 'Usage: /workflow <description of tasks>',
  
  handler: async (context: CommandContext, args?: string) => {
    if (!isInitialized) {
      await initializeAgentSystems(context);
    }

    if (!args) {
      displayWorkflows(context);
      return { redraw: true };
    }

    try {
      const workflow = orchestrator!.createWorkflow(args);
      
      context.addMessage({
        type: 'info',
        text: chalk.blue(`📋 Workflow: ${workflow.name}`)
      });

      workflow.tasks.forEach((task, index) => {
        context.addMessage({
          type: 'info',
          text: `  ${index + 1}. [${task.agent}] ${task.description}`
        });
      });

      const confirmed = await context.requestConfirmation('Execute this workflow?');
      if (confirmed) {
        await orchestrator!.executeWorkflow(workflow);
      }

    } catch (error) {
      context.addMessage({
        type: 'error',
        text: `Workflow creation failed: ${error}`
      });
    }

    return { redraw: true };
  }
};

// Export all agent-related commands
export const agentCommands = [
  agentCommand,
  scoutCommand,
  guardianCommand,
  workflowCommand
];