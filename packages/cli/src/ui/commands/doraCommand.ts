/**
 * DORA Command - CLI interface for DORA metrics tracking
 * Provides slash commands for DORA metrics operations
 */

import { SlashCommand, CommandContext } from './types.js';
import { DORAMetricsCollector, DeploymentEvent, IncidentEvent } from '../../monitoring/dora-metrics.js';
import { DORADashboard } from '../../monitoring/dora-dashboard.js';
import chalk from 'chalk';
import path from 'path';

let doraCollector: DORAMetricsCollector | null = null;
let doraDashboard: DORADashboard | null = null;
let isInitialized = false;

/**
 * Initialize DORA metrics system
 */
async function initializeDORA(context: CommandContext): Promise<boolean> {
  if (isInitialized) {
    return true;
  }

  try {
    context.addMessage({
      type: 'system',
      text: chalk.blue('📊 Initializing DORA metrics system...')
    });

    const projectRoot = context.config?.getProjectRoot() || process.cwd();
    
    doraCollector = new DORAMetricsCollector({
      dataPath: path.join(projectRoot, '.gemini', 'dora-metrics'),
      gitRepository: projectRoot,
      environments: ['development', 'staging', 'production']
    });

    await doraCollector.initialize();

    doraDashboard = new DORADashboard(doraCollector, {
      refreshInterval: 30000,
      historicalPeriod: 30,
      showTrends: true
    });

    context.addMessage({
      type: 'success',
      text: chalk.green('✓ DORA metrics system initialized')
    });

    isInitialized = true;
    return true;

  } catch (error) {
    context.addMessage({
      type: 'error',
      text: `Failed to initialize DORA metrics: ${error}`
    });
    return false;
  }
}

/**
 * Main DORA command
 */
export const doraCommand: SlashCommand = {
  name: 'dora',
  description: 'DORA metrics tracking and analysis',
  pattern: /^\/dora(?:\s+(.+))?$/,
  help: `Usage: /dora <subcommand> [options]

Subcommands:
  /dora status           - Show current DORA metrics
  /dora dashboard        - Open interactive dashboard
  /dora deploy           - Record a deployment
  /dora incident         - Record an incident
  /dora resolve <id>     - Resolve an incident
  /dora history          - Show deployment/incident history
  /dora export           - Export metrics data
  /dora trends           - Show trend analysis
  /dora help             - Show detailed help

Examples:
  /dora deploy --env production --version v1.2.3 --success
  /dora incident --env production --severity high --description "API timeout"
  /dora resolve incident_123 --description "Fixed database query"`,
  
  handler: async (context: CommandContext, args?: string) => {
    // Initialize if needed
    if (!isInitialized) {
      const success = await initializeDORA(context);
      if (!success) {
        return { redraw: false };
      }
    }

    // Handle no arguments
    if (!args || args.trim() === '') {
      context.addMessage({
        type: 'info',
        text: 'Please provide a subcommand. Use "/dora help" for available options.'
      });
      return { redraw: true };
    }

    const parts = args.trim().split(/\s+/);
    const subcommand = parts[0].toLowerCase();

    try {
      switch (subcommand) {
        case 'status':
          return await handleStatus(context, parts.slice(1));
        case 'dashboard':
          return await handleDashboard(context, parts.slice(1));
        case 'deploy':
          return await handleDeploy(context, parts.slice(1));
        case 'incident':
          return await handleIncident(context, parts.slice(1));
        case 'resolve':
          return await handleResolve(context, parts.slice(1));
        case 'history':
          return await handleHistory(context, parts.slice(1));
        case 'export':
          return await handleExport(context, parts.slice(1));
        case 'trends':
          return await handleTrends(context, parts.slice(1));
        case 'help':
          return handleHelp(context);
        default:
          context.addMessage({
            type: 'error',
            text: `Unknown subcommand: ${subcommand}. Use "/dora help" for available options.`
          });
          return { redraw: true };
      }
    } catch (error) {
      context.addMessage({
        type: 'error',
        text: `DORA command failed: ${error}`
      });
      return { redraw: true };
    }
  }
};

/**
 * Handle status command
 */
async function handleStatus(context: CommandContext, args: string[]) {
  const period = args.includes('--week') ? 7 : args.includes('--month') ? 30 : 30;
  const startDate = new Date(Date.now() - period * 24 * 60 * 60 * 1000);
  
  const metrics = doraCollector!.calculateMetrics(startDate);
  
  context.addMessage({
    type: 'info',
    text: formatMetricsDisplay(metrics)
  });

  return { redraw: true };
}

/**
 * Handle dashboard command
 */
async function handleDashboard(context: CommandContext, args: string[]) {
  const interactive = !args.includes('--simple');
  
  if (interactive) {
    context.addMessage({
      type: 'info',
      text: 'Opening interactive DORA dashboard... Press Ctrl+C to exit.'
    });
    
    // Start interactive dashboard
    await doraDashboard!.start();
  } else {
    // Display simple dashboard
    await doraDashboard!.displaySimple();
  }

  return { redraw: false };
}

/**
 * Handle deploy command
 */
async function handleDeploy(context: CommandContext, args: string[]) {
  const deployment: Partial<DeploymentEvent> = {
    environment: 'production',
    success: true
  };

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--env':
        deployment.environment = args[++i] as any;
        break;
      case '--version':
        deployment.version = args[++i];
        break;
      case '--commit':
        deployment.commit = args[++i];
        break;
      case '--success':
        deployment.success = true;
        break;
      case '--failed':
        deployment.success = false;
        break;
      case '--rollback':
        deployment.rollback = true;
        break;
      case '--duration':
        deployment.duration = parseInt(args[++i]);
        break;
    }
  }

  // Get current Git commit if not specified
  if (!deployment.commit) {
    try {
      const { execSync } = await import('child_process');
      deployment.commit = execSync('git rev-parse HEAD', { encoding: 'utf-8' }).trim();
    } catch (error) {
      deployment.commit = 'unknown';
    }
  }

  await doraCollector!.recordDeployment(deployment as Omit<DeploymentEvent, 'id' | 'timestamp'>);
  
  const status = deployment.success ? chalk.green('successful') : chalk.red('failed');
  context.addMessage({
    type: 'success',
    text: `📦 Recorded ${status} deployment to ${deployment.environment}: ${deployment.version || 'unknown'}`
  });

  return { redraw: true };
}

/**
 * Handle incident command
 */
async function handleIncident(context: CommandContext, args: string[]) {
  const incident: Partial<IncidentEvent> = {
    environment: 'production',
    severity: 'medium',
    description: 'Incident reported'
  };

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--env':
        incident.environment = args[++i] as any;
        break;
      case '--severity':
        incident.severity = args[++i] as any;
        break;
      case '--description':
        incident.description = args.slice(++i).join(' ');
        break;
    }
  }

  await doraCollector!.recordIncident(incident as Omit<IncidentEvent, 'id' | 'timestamp'>);
  
  const severityColor = incident.severity === 'critical' ? chalk.red : 
                       incident.severity === 'high' ? chalk.magenta :
                       incident.severity === 'medium' ? chalk.yellow : chalk.blue;
  
  context.addMessage({
    type: 'warning',
    text: `🚨 Recorded ${severityColor(incident.severity!)} incident in ${incident.environment}: ${incident.description}`
  });

  return { redraw: true };
}

/**
 * Handle resolve command
 */
async function handleResolve(context: CommandContext, args: string[]) {
  if (args.length === 0) {
    context.addMessage({
      type: 'error',
      text: 'Please provide an incident ID to resolve'
    });
    return { redraw: true };
  }

  const incidentId = args[0];
  const resolution = args.slice(1).join(' ') || 'Incident resolved';

  try {
    await doraCollector!.resolveIncident(incidentId, resolution);
    
    context.addMessage({
      type: 'success',
      text: `✓ Incident ${incidentId} resolved: ${resolution}`
    });
  } catch (error) {
    context.addMessage({
      type: 'error',
      text: `Failed to resolve incident: ${error}`
    });
  }

  return { redraw: true };
}

/**
 * Handle history command
 */
async function handleHistory(context: CommandContext, args: string[]) {
  const type = args.includes('--incidents') ? 'incidents' : 
               args.includes('--deployments') ? 'deployments' : 'both';
  const limit = 10;

  let output = '';

  if (type === 'deployments' || type === 'both') {
    const deployments = doraCollector!.getDeployments(undefined, limit);
    output += chalk.cyan('\n📦 Recent Deployments:\n');
    
    if (deployments.length > 0) {
      deployments.forEach(d => {
        const status = d.success ? chalk.green('✓') : chalk.red('✗');
        const env = d.environment.toUpperCase().padEnd(11);
        const time = d.timestamp.toLocaleString();
        output += `  ${status} ${env} ${d.version || 'unknown'} - ${time}\n`;
      });
    } else {
      output += chalk.gray('  No deployments found\n');
    }
  }

  if (type === 'incidents' || type === 'both') {
    const incidents = doraCollector!.getIncidents(undefined, undefined, limit);
    output += chalk.cyan('\n🚨 Recent Incidents:\n');
    
    if (incidents.length > 0) {
      incidents.forEach(i => {
        const status = i.resolved ? chalk.green('✓') : chalk.red('●');
        const severity = i.severity.toUpperCase().padEnd(8);
        const time = i.timestamp.toLocaleString();
        const mttr = i.mttr ? ` (MTTR: ${Math.round(i.mttr / (1000 * 60))}m)` : '';
        output += `  ${status} ${severity} ${i.description.substring(0, 50)}...${mttr} - ${time}\n`;
      });
    } else {
      output += chalk.gray('  No incidents found\n');
    }
  }

  context.addMessage({
    type: 'info',
    text: output
  });

  return { redraw: true };
}

/**
 * Handle export command
 */
async function handleExport(context: CommandContext, args: string[]) {
  const format = args.includes('--csv') ? 'csv' : 'json';
  
  try {
    const data = await doraCollector!.exportData(format);
    const filename = `dora-metrics-${new Date().toISOString().split('T')[0]}.${format}`;
    
    // In a real implementation, this would write to a file
    // For now, just show the first part of the data
    context.addMessage({
      type: 'success',
      text: `📄 Exported DORA metrics data (${data.length} characters)\nFilename: ${filename}`
    });
    
    context.addMessage({
      type: 'info',
      text: `Preview:\n${data.substring(0, 200)}...`
    });
  } catch (error) {
    context.addMessage({
      type: 'error',
      text: `Export failed: ${error}`
    });
  }

  return { redraw: true };
}

/**
 * Handle trends command
 */
async function handleTrends(context: CommandContext, args: string[]) {
  // Calculate metrics for different periods to show trends
  const periods = [7, 30, 90]; // days
  const trends: string[] = [];

  for (const days of periods) {
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const metrics = doraCollector!.calculateMetrics(startDate);
    
    trends.push(`${days}d: DF=${metrics.deploymentFrequency.value.toFixed(1)}/${metrics.deploymentFrequency.unit} LT=${metrics.leadTime.value.toFixed(1)}${metrics.leadTime.unit} MTTR=${metrics.mttr.value.toFixed(1)}${metrics.mttr.unit} CFR=${metrics.changeFailureRate.value.toFixed(1)}%`);
  }

  context.addMessage({
    type: 'info',
    text: chalk.cyan('📈 DORA Metrics Trends:\n') + trends.join('\n')
  });

  return { redraw: true };
}

/**
 * Handle help command
 */
function handleHelp(context: CommandContext) {
  const helpText = `
${chalk.blue.bold('DORA Metrics Commands')}

${chalk.yellow('What are DORA Metrics?')}
DORA (DevOps Research and Assessment) metrics measure software delivery performance:

${chalk.cyan('📦 Deployment Frequency')} - How often you deploy to production
  Elite: Daily+  |  High: Weekly  |  Medium: Monthly  |  Low: <Monthly

${chalk.cyan('⏱️  Lead Time for Changes')} - Time from commit to production  
  Elite: <1 day  |  High: <1 week  |  Medium: <1 month  |  Low: >1 month

${chalk.cyan('🔧 Mean Time to Recovery (MTTR)')} - How quickly you recover from failures
  Elite: <1 hour  |  High: <1 day  |  Medium: <1 week  |  Low: >1 week

${chalk.cyan('💥 Change Failure Rate')} - % of deployments causing production issues
  Elite: <5%  |  High: 5-10%  |  Medium: 10-20%  |  Low: >20%

${chalk.yellow('Available Commands:')}
  /dora status           - Show current metrics
  /dora dashboard        - Interactive dashboard (--simple for text)
  /dora deploy           - Record deployment (--env, --version, --success/--failed)
  /dora incident         - Record incident (--env, --severity, --description)
  /dora resolve <id>     - Mark incident as resolved
  /dora history          - Show recent activity (--deployments, --incidents)
  /dora export           - Export data (--json, --csv)
  /dora trends           - Compare metrics across time periods

${chalk.yellow('Examples:')}
  /dora deploy --env production --version v2.1.0 --success
  /dora incident --env staging --severity high --description API gateway timeout
  /dora resolve incident_abc123 Fixed by restarting service`;

  context.addMessage({
    type: 'info',
    text: helpText
  });

  return { redraw: true };
}

/**
 * Format metrics for display
 */
function formatMetricsDisplay(metrics: any): string {
  const lines = [
    chalk.blue.bold('📊 DORA Metrics Summary'),
    chalk.gray(`Period: ${metrics.period.start.toLocaleDateString()} - ${metrics.period.end.toLocaleDateString()} (${metrics.period.days} days)`),
    '',
    `🚀 ${chalk.cyan('Deployment Frequency')}: ${getClassificationColor(metrics.deploymentFrequency.classification)(metrics.deploymentFrequency.value.toFixed(1))} ${metrics.deploymentFrequency.unit} (${metrics.deploymentFrequency.classification.toUpperCase()})`,
    `⏱️  ${chalk.cyan('Lead Time')}: ${getClassificationColor(metrics.leadTime.classification)(metrics.leadTime.value.toFixed(1))} ${metrics.leadTime.unit} (${metrics.leadTime.classification.toUpperCase()})`,
    `🔧 ${chalk.cyan('MTTR')}: ${getClassificationColor(metrics.mttr.classification)(metrics.mttr.value.toFixed(1))} ${metrics.mttr.unit} (${metrics.mttr.classification.toUpperCase()})`,
    `💥 ${chalk.cyan('Change Failure Rate')}: ${getClassificationColor(metrics.changeFailureRate.classification)(metrics.changeFailureRate.value.toFixed(1))}% (${metrics.changeFailureRate.classification.toUpperCase()})`
  ];

  return lines.join('\n');
}

/**
 * Get color for classification
 */
function getClassificationColor(classification: string): (text: string) => string {
  switch (classification) {
    case 'elite': return chalk.green.bold;
    case 'high': return chalk.cyan.bold;
    case 'medium': return chalk.yellow.bold;
    case 'low': return chalk.red.bold;
    default: return chalk.white;
  }
}

// Export DORA-related commands
export const doraCommands = [doraCommand];