/**
 * Real-time Status Manager
 * Provides live updates and progress tracking for agent operations
 */

import { EventEmitter } from 'events';
import chalk from 'chalk';
import ora, { Ora } from 'ora';
import cliProgress from 'cli-progress';
import { terminal as term } from 'terminal-kit';

export interface StatusUpdate {
  type: 'info' | 'success' | 'warning' | 'error' | 'progress';
  agent?: string;
  message: string;
  details?: any;
  timestamp: Date;
}

export interface ProgressInfo {
  taskId: string;
  taskName: string;
  current: number;
  total: number;
  agent: string;
  startTime: Date;
  eta?: number;
}

export interface AgentStatus {
  agent: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  tasksCompleted: number;
  successRate: number;
  averageTime: number;
}

export class RealTimeStatusManager extends EventEmitter {
  private statusHistory: StatusUpdate[] = [];
  private activeSpinners: Map<string, Ora> = new Map();
  private progressBars: Map<string, any> = new Map();
  private agentStatuses: Map<string, AgentStatus> = new Map();
  private multiBar: any;
  private displayMode: 'simple' | 'detailed' | 'compact' = 'simple';
  private maxHistorySize: number = 100;
  private isInteractive: boolean = true;

  constructor() {
    super();
    this.initializeAgentStatuses();
    this.setupMultiBar();
  }

  /**
   * Initialize agent status tracking
   */
  private initializeAgentStatuses(): void {
    const agents = ['scout', 'architect', 'guardian', 'developer', 'qa', 'pm', 'po'];
    agents.forEach(agent => {
      this.agentStatuses.set(agent, {
        agent,
        status: 'idle',
        tasksCompleted: 0,
        successRate: 100,
        averageTime: 0
      });
    });
  }

  /**
   * Setup multi-progress bar
   */
  private setupMultiBar(): void {
    this.multiBar = new cliProgress.MultiBar({
      format: '{agent} |{bar}| {percentage}% | {taskName} | ETA: {eta_formatted}',
      barCompleteChar: '\u2588',
      barIncompleteChar: '\u2591',
      hideCursor: true,
      clearOnComplete: true,
      stopOnComplete: true
    }, cliProgress.Presets.shades_classic);
  }

  /**
   * Set display mode
   */
  setDisplayMode(mode: 'simple' | 'detailed' | 'compact'): void {
    this.displayMode = mode;
  }

  /**
   * Display status update
   */
  displayStatus(update: StatusUpdate): void {
    // Add to history
    this.statusHistory.push(update);
    if (this.statusHistory.length > this.maxHistorySize) {
      this.statusHistory.shift();
    }

    // Format and display based on mode
    switch (this.displayMode) {
      case 'detailed':
        this.displayDetailed(update);
        break;
      case 'compact':
        this.displayCompact(update);
        break;
      default:
        this.displaySimple(update);
    }

    // Emit for external listeners
    this.emit('status_update', update);
  }

  /**
   * Simple display mode
   */
  private displaySimple(update: StatusUpdate): void {
    const icon = this.getStatusIcon(update.type);
    const color = this.getStatusColor(update.type);
    const agentTag = update.agent ? `[${update.agent.toUpperCase()}]` : '';
    
    console.log(color(`${icon} ${agentTag} ${update.message}`));
    
    if (update.details && this.displayMode !== 'compact') {
      this.displayDetails(update.details);
    }
  }

  /**
   * Detailed display mode
   */
  private displayDetailed(update: StatusUpdate): void {
    const timestamp = update.timestamp.toLocaleTimeString();
    const icon = this.getStatusIcon(update.type);
    const color = this.getStatusColor(update.type);
    const agentTag = update.agent ? chalk.cyan(`[${update.agent.toUpperCase()}]`) : '';
    
    console.log(chalk.gray(timestamp), color(icon), agentTag, color(update.message));
    
    if (update.details) {
      this.displayDetails(update.details, true);
    }
  }

  /**
   * Compact display mode
   */
  private displayCompact(update: StatusUpdate): void {
    const icon = this.getStatusIcon(update.type);
    const color = this.getStatusColor(update.type);
    const agent = update.agent ? update.agent.substr(0, 3).toUpperCase() : '---';
    
    // Single line output
    process.stdout.write(color(`${icon} [${agent}] ${update.message.substr(0, 60)}...\r`));
  }

  /**
   * Display details object
   */
  private displayDetails(details: any, verbose: boolean = false): void {
    const indent = '    ';
    
    if (typeof details === 'string') {
      console.log(chalk.gray(indent + details));
      return;
    }

    if (Array.isArray(details)) {
      details.forEach(item => {
        console.log(chalk.gray(indent + '• ' + item));
      });
      return;
    }

    if (typeof details === 'object') {
      Object.entries(details).forEach(([key, value]) => {
        if (verbose || this.isImportantDetail(key)) {
          const formattedKey = chalk.gray(key.replace(/_/g, ' '));
          const formattedValue = this.formatDetailValue(value);
          console.log(`${indent}${formattedKey}: ${formattedValue}`);
        }
      });
    }
  }

  /**
   * Check if detail is important
   */
  private isImportantDetail(key: string): boolean {
    const importantKeys = ['error', 'warning', 'success', 'result', 'recommendation', 'action'];
    return importantKeys.some(k => key.toLowerCase().includes(k));
  }

  /**
   * Format detail value
   */
  private formatDetailValue(value: any): string {
    if (typeof value === 'boolean') {
      return value ? chalk.green('✓') : chalk.red('✗');
    }
    if (typeof value === 'number') {
      return chalk.yellow(value.toString());
    }
    if (Array.isArray(value)) {
      return chalk.cyan(`[${value.length} items]`);
    }
    if (typeof value === 'object' && value !== null) {
      return chalk.cyan('{...}');
    }
    return chalk.white(String(value));
  }

  /**
   * Start spinner for a task
   */
  startSpinner(taskId: string, message: string, agent?: string): void {
    if (!this.isInteractive) {
      this.displayStatus({
        type: 'info',
        agent,
        message,
        timestamp: new Date()
      });
      return;
    }

    const spinner = ora({
      text: message,
      prefixText: agent ? chalk.cyan(`[${agent.toUpperCase()}]`) : '',
      spinner: 'dots'
    }).start();

    this.activeSpinners.set(taskId, spinner);
  }

  /**
   * Update spinner text
   */
  updateSpinner(taskId: string, message: string): void {
    const spinner = this.activeSpinners.get(taskId);
    if (spinner) {
      spinner.text = message;
    }
  }

  /**
   * Success spinner
   */
  succeedSpinner(taskId: string, message?: string): void {
    const spinner = this.activeSpinners.get(taskId);
    if (spinner) {
      if (message) spinner.text = message;
      spinner.succeed();
      this.activeSpinners.delete(taskId);
    }
  }

  /**
   * Fail spinner
   */
  failSpinner(taskId: string, message?: string): void {
    const spinner = this.activeSpinners.get(taskId);
    if (spinner) {
      if (message) spinner.text = message;
      spinner.fail();
      this.activeSpinners.delete(taskId);
    }
  }

  /**
   * Start progress bar
   */
  startProgress(info: ProgressInfo): void {
    if (!this.isInteractive) {
      return;
    }

    const bar = this.multiBar.create(info.total, info.current, {
      agent: info.agent.toUpperCase().padEnd(10),
      taskName: info.taskName.substr(0, 30).padEnd(30)
    });

    this.progressBars.set(info.taskId, {
      bar,
      info
    });
  }

  /**
   * Update progress
   */
  updateProgress(taskId: string, current: number, message?: string): void {
    const progress = this.progressBars.get(taskId);
    if (progress) {
      progress.bar.update(current, {
        taskName: message || progress.info.taskName
      });

      // Calculate ETA
      const elapsed = Date.now() - progress.info.startTime.getTime();
      const rate = current / elapsed;
      const remaining = progress.info.total - current;
      const eta = remaining / rate;
      
      progress.info.eta = eta;
    }
  }

  /**
   * Complete progress
   */
  completeProgress(taskId: string): void {
    const progress = this.progressBars.get(taskId);
    if (progress) {
      progress.bar.stop();
      this.progressBars.delete(taskId);
    }

    // Stop multi-bar if no active progress bars
    if (this.progressBars.size === 0) {
      this.multiBar.stop();
    }
  }

  /**
   * Update agent status
   */
  updateAgentStatus(agent: string, status: Partial<AgentStatus>): void {
    const current = this.agentStatuses.get(agent);
    if (current) {
      Object.assign(current, status);
      this.emit('agent_status_changed', current);
    }
  }

  /**
   * Display agent summary
   */
  displayAgentSummary(): void {
    console.log(chalk.blue('\n📊 Agent Status Summary:'));
    console.log(chalk.gray('─'.repeat(50)));

    const headers = ['Agent', 'Status', 'Current Task', 'Completed', 'Success Rate'];
    const rows: string[][] = [];

    this.agentStatuses.forEach(status => {
      rows.push([
        status.agent.toUpperCase(),
        this.formatAgentStatus(status.status),
        status.currentTask || '-',
        status.tasksCompleted.toString(),
        `${status.successRate}%`
      ]);
    });

    this.displayTable(headers, rows);
  }

  /**
   * Format agent status
   */
  private formatAgentStatus(status: string): string {
    switch (status) {
      case 'busy':
        return chalk.yellow('● Busy');
      case 'idle':
        return chalk.green('● Idle');
      case 'error':
        return chalk.red('● Error');
      case 'offline':
        return chalk.gray('● Offline');
      default:
        return status;
    }
  }

  /**
   * Display table
   */
  private displayTable(headers: string[], rows: string[][]): void {
    // Calculate column widths
    const widths = headers.map((h, i) => {
      const columnValues = [h, ...rows.map(r => r[i])];
      return Math.max(...columnValues.map(v => v.length)) + 2;
    });

    // Display headers
    console.log(headers.map((h, i) => h.padEnd(widths[i])).join(''));
    console.log(chalk.gray('─'.repeat(widths.reduce((a, b) => a + b, 0))));

    // Display rows
    rows.forEach(row => {
      console.log(row.map((v, i) => v.padEnd(widths[i])).join(''));
    });
  }

  /**
   * Display workflow progress
   */
  displayWorkflowProgress(workflowId: string, status: any): void {
    const percentage = Math.round(status.progress);
    const barLength = 30;
    const filled = Math.round(barLength * (percentage / 100));
    const empty = barLength - filled;

    const bar = chalk.green('█'.repeat(filled)) + chalk.gray('░'.repeat(empty));
    
    console.log(chalk.blue('\n📈 Workflow Progress:'));
    console.log(`   ${bar} ${percentage}%`);
    console.log(chalk.gray(`   Tasks: ${status.completed}/${status.total} completed`));
    
    if (status.running > 0) {
      console.log(chalk.yellow(`   Running: ${status.running} task(s)`));
    }
    
    if (status.failed > 0) {
      console.log(chalk.red(`   Failed: ${status.failed} task(s)`));
    }
  }

  /**
   * Get status icon
   */
  private getStatusIcon(type: string): string {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      case 'progress':
        return '◷';
      default:
        return '•';
    }
  }

  /**
   * Get status color
   */
  private getStatusColor(type: string): (text: string) => string {
    switch (type) {
      case 'success':
        return chalk.green;
      case 'error':
        return chalk.red;
      case 'warning':
        return chalk.yellow;
      case 'info':
        return chalk.blue;
      case 'progress':
        return chalk.cyan;
      default:
        return chalk.white;
    }
  }

  /**
   * Clear all active spinners
   */
  clearSpinners(): void {
    this.activeSpinners.forEach(spinner => {
      spinner.stop();
    });
    this.activeSpinners.clear();
  }

  /**
   * Clear all progress bars
   */
  clearProgress(): void {
    this.progressBars.forEach(progress => {
      progress.bar.stop();
    });
    this.progressBars.clear();
    this.multiBar.stop();
  }

  /**
   * Get status history
   */
  getHistory(limit?: number): StatusUpdate[] {
    if (limit) {
      return this.statusHistory.slice(-limit);
    }
    return [...this.statusHistory];
  }

  /**
   * Clear history
   */
  clearHistory(): void {
    this.statusHistory = [];
  }

  /**
   * Set interactive mode
   */
  setInteractive(interactive: boolean): void {
    this.isInteractive = interactive;
    if (!interactive) {
      this.clearSpinners();
      this.clearProgress();
    }
  }

  /**
   * Display real-time dashboard
   */
  async displayDashboard(): Promise<void> {
    // Clear screen
    console.clear();

    // Header
    console.log(chalk.blue.bold('╔════════════════════════════════════════════════════╗'));
    console.log(chalk.blue.bold('║     Gemini Enterprise Architect - Live Status      ║'));
    console.log(chalk.blue.bold('╚════════════════════════════════════════════════════╝'));

    // Agent status section
    this.displayAgentSummary();

    // Recent activity
    console.log(chalk.blue('\n📜 Recent Activity:'));
    console.log(chalk.gray('─'.repeat(50)));
    
    const recentUpdates = this.getHistory(5);
    recentUpdates.forEach(update => {
      const time = update.timestamp.toLocaleTimeString();
      const agent = update.agent ? `[${update.agent}]` : '';
      console.log(chalk.gray(time), agent, update.message);
    });

    // Active tasks
    if (this.activeSpinners.size > 0) {
      console.log(chalk.blue('\n⚙️  Active Tasks:'));
      console.log(chalk.gray('─'.repeat(50)));
      this.activeSpinners.forEach((spinner, taskId) => {
        console.log(chalk.cyan(`   • ${taskId}: ${spinner.text}`));
      });
    }

    // Footer
    console.log(chalk.gray('\n─'.repeat(50)));
    console.log(chalk.gray('Press Ctrl+C to exit dashboard view'));
  }

  /**
   * Start dashboard mode
   */
  startDashboard(): void {
    const interval = setInterval(() => {
      this.displayDashboard();
    }, 1000);

    // Handle exit
    process.on('SIGINT', () => {
      clearInterval(interval);
      console.clear();
      console.log(chalk.yellow('Dashboard mode ended'));
      process.exit(0);
    });
  }
}

export default RealTimeStatusManager;