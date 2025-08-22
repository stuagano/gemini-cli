/**
 * DORA Metrics Dashboard
 * Interactive terminal dashboard for DORA metrics visualization
 */

import chalk from 'chalk';
import { terminal as term } from 'terminal-kit';
import blessed from 'blessed';
import { DORAMetricsCollector, DORAMetrics, DeploymentEvent, IncidentEvent } from './dora-metrics.js';

export interface DashboardConfig {
  refreshInterval: number; // milliseconds
  historicalPeriod: number; // days
  showTrends: boolean;
  environments: string[];
}

export class DORADashboard {
  private collector: DORAMetricsCollector;
  private config: DashboardConfig;
  private screen: any;
  private boxes: Record<string, any> = {};
  private isRunning: boolean = false;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor(collector: DORAMetricsCollector, config?: Partial<DashboardConfig>) {
    this.collector = collector;
    this.config = {
      refreshInterval: 30000, // 30 seconds
      historicalPeriod: 30, // 30 days
      showTrends: true,
      environments: ['development', 'staging', 'production'],
      ...config
    };
  }

  /**
   * Start the interactive dashboard
   */
  async start(): Promise<void> {
    this.setupScreen();
    this.createLayout();
    
    // Initial render
    await this.refreshData();
    
    // Start auto-refresh
    this.startAutoRefresh();
    
    this.isRunning = true;
    console.log(chalk.green('📊 DORA Dashboard started - Press Ctrl+C to exit'));
  }

  /**
   * Stop the dashboard
   */
  stop(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    
    if (this.screen) {
      this.screen.destroy();
    }
    
    this.isRunning = false;
    console.log(chalk.yellow('Dashboard stopped'));
  }

  /**
   * Display simple text dashboard (non-interactive)
   */
  async displaySimple(): Promise<void> {
    const metrics = this.collector.calculateMetrics();
    
    console.clear();
    this.renderHeader();
    this.renderMetricsSummary(metrics);
    this.renderRecentActivity();
  }

  /**
   * Setup blessed screen
   */
  private setupScreen(): void {
    this.screen = blessed.screen({
      smartCSR: true,
      title: 'DORA Metrics Dashboard'
    });

    // Handle exit
    this.screen.key(['escape', 'q', 'C-c'], () => {
      this.stop();
      process.exit(0);
    });

    // Handle refresh
    this.screen.key(['r'], () => {
      this.refreshData();
    });

    // Handle help
    this.screen.key(['h', '?'], () => {
      this.showHelp();
    });
  }

  /**
   * Create dashboard layout
   */
  private createLayout(): void {
    // Header
    this.boxes.header = blessed.box({
      top: 0,
      left: 0,
      width: '100%',
      height: 3,
      content: '',
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        bg: 'blue',
        border: {
          fg: 'blue'
        }
      }
    });

    // Deployment Frequency
    this.boxes.deploymentFrequency = blessed.box({
      top: 3,
      left: 0,
      width: '25%',
      height: 12,
      label: 'Deployment Frequency',
      content: '',
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        border: {
          fg: 'green'
        }
      }
    });

    // Lead Time
    this.boxes.leadTime = blessed.box({
      top: 3,
      left: '25%',
      width: '25%',
      height: 12,
      label: 'Lead Time for Changes',
      content: '',
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        border: {
          fg: 'blue'
        }
      }
    });

    // MTTR
    this.boxes.mttr = blessed.box({
      top: 3,
      left: '50%',
      width: '25%',
      height: 12,
      label: 'Mean Time to Recovery',
      content: '',
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        border: {
          fg: 'yellow'
        }
      }
    });

    // Change Failure Rate
    this.boxes.changeFailureRate = blessed.box({
      top: 3,
      left: '75%',
      width: '25%',
      height: 12,
      label: 'Change Failure Rate',
      content: '',
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        border: {
          fg: 'red'
        }
      }
    });

    // Recent Deployments
    this.boxes.recentDeployments = blessed.box({
      top: 15,
      left: 0,
      width: '50%',
      height: 12,
      label: 'Recent Deployments',
      content: '',
      border: {
        type: 'line'
      },
      scrollable: true,
      style: {
        fg: 'white',
        border: {
          fg: 'cyan'
        }
      }
    });

    // Recent Incidents
    this.boxes.recentIncidents = blessed.box({
      top: 15,
      left: '50%',
      width: '50%',
      height: 12,
      label: 'Recent Incidents',
      content: '',
      border: {
        type: 'line'
      },
      scrollable: true,
      style: {
        fg: 'white',
        border: {
          fg: 'magenta'
        }
      }
    });

    // Status Bar
    this.boxes.statusBar = blessed.box({
      bottom: 0,
      left: 0,
      width: '100%',
      height: 3,
      content: '',
      style: {
        fg: 'white',
        bg: 'black'
      }
    });

    // Add all boxes to screen
    Object.values(this.boxes).forEach(box => {
      this.screen.append(box);
    });
  }

  /**
   * Refresh dashboard data
   */
  private async refreshData(): Promise<void> {
    try {
      const metrics = this.collector.calculateMetrics();
      const recentDeployments = this.collector.getDeployments(undefined, 10);
      const recentIncidents = this.collector.getIncidents(undefined, undefined, 10);

      this.updateHeader();
      this.updateMetricsBoxes(metrics);
      this.updateRecentDeployments(recentDeployments);
      this.updateRecentIncidents(recentIncidents);
      this.updateStatusBar();

      this.screen.render();
    } catch (error) {
      console.error('Failed to refresh dashboard data:', error);
    }
  }

  /**
   * Update header
   */
  private updateHeader(): void {
    const now = new Date().toLocaleString();
    this.boxes.header.setContent(`{center}🚀 DORA Metrics Dashboard - ${now}{/center}`);
  }

  /**
   * Update metrics boxes
   */
  private updateMetricsBoxes(metrics: DORAMetrics): void {
    // Deployment Frequency
    const dfClass = this.getClassificationColor(metrics.deploymentFrequency.classification);
    const dfTrend = this.getTrendIcon(metrics.deploymentFrequency.trend);
    this.boxes.deploymentFrequency.setContent(`
{center}{${dfClass}-fg}${metrics.deploymentFrequency.value.toFixed(1)} ${metrics.deploymentFrequency.unit}{/}

Classification: {${dfClass}-fg}${metrics.deploymentFrequency.classification.toUpperCase()}{/}
Trend: ${dfTrend}

Target:
Elite: Daily+
High: Weekly
Medium: Monthly
Low: <Monthly`);

    // Lead Time
    const ltClass = this.getClassificationColor(metrics.leadTime.classification);
    const ltTrend = this.getTrendIcon(metrics.leadTime.trend);
    this.boxes.leadTime.setContent(`
{center}{${ltClass}-fg}${metrics.leadTime.value.toFixed(1)} ${metrics.leadTime.unit}{/}

Classification: {${ltClass}-fg}${metrics.leadTime.classification.toUpperCase()}{/}
Trend: ${ltTrend}
Median: ${metrics.leadTime.median.toFixed(1)}h
P90: ${metrics.leadTime.p90.toFixed(1)}h

Target:
Elite: <1 day
High: <1 week`);

    // MTTR
    const mttrClass = this.getClassificationColor(metrics.mttr.classification);
    const mttrTrend = this.getTrendIcon(metrics.mttr.trend);
    this.boxes.mttr.setContent(`
{center}{${mttrClass}-fg}${metrics.mttr.value.toFixed(1)} ${metrics.mttr.unit}{/}

Classification: {${mttrClass}-fg}${metrics.mttr.classification.toUpperCase()}{/}
Trend: ${mttrTrend}
Incidents: ${metrics.mttr.incidents}
Median: ${metrics.mttr.median.toFixed(1)}h

Target:
Elite: <1 hour
High: <1 day`);

    // Change Failure Rate
    const cfrClass = this.getClassificationColor(metrics.changeFailureRate.classification);
    const cfrTrend = this.getTrendIcon(metrics.changeFailureRate.trend);
    this.boxes.changeFailureRate.setContent(`
{center}{${cfrClass}-fg}${metrics.changeFailureRate.value.toFixed(1)}%{/}

Classification: {${cfrClass}-fg}${metrics.changeFailureRate.classification.toUpperCase()}{/}
Trend: ${cfrTrend}
Failed: ${metrics.changeFailureRate.failed}
Total: ${metrics.changeFailureRate.total}

Target:
Elite: <5%
High: 5-10%`);
  }

  /**
   * Update recent deployments
   */
  private updateRecentDeployments(deployments: DeploymentEvent[]): void {
    const lines = deployments.map(d => {
      const status = d.success ? '{green-fg}✓{/}' : '{red-fg}✗{/}';
      const env = this.getEnvironmentColor(d.environment);
      const time = d.timestamp.toLocaleDateString();
      const version = d.version || 'unknown';
      return `${status} {${env}-fg}${d.environment.toUpperCase()}{/} ${version} - ${time}`;
    });

    this.boxes.recentDeployments.setContent(lines.join('\n') || 'No recent deployments');
  }

  /**
   * Update recent incidents
   */
  private updateRecentIncidents(incidents: IncidentEvent[]): void {
    const lines = incidents.map(i => {
      const status = i.resolved ? '{green-fg}✓{/}' : '{red-fg}●{/}';
      const severity = this.getSeverityColor(i.severity);
      const env = this.getEnvironmentColor(i.environment);
      const time = i.timestamp.toLocaleDateString();
      const mttr = i.mttr ? ` (${Math.round(i.mttr / (1000 * 60))}m)` : '';
      return `${status} {${severity}-fg}${i.severity.toUpperCase()}{/} {${env}-fg}${i.environment}{/} - ${i.description.substring(0, 30)}...${mttr}`;
    });

    this.boxes.recentIncidents.setContent(lines.join('\n') || 'No recent incidents');
  }

  /**
   * Update status bar
   */
  private updateStatusBar(): void {
    const refreshInterval = Math.round(this.config.refreshInterval / 1000);
    this.boxes.statusBar.setContent(`
Press 'r' to refresh | 'h' for help | 'q' to quit | Auto-refresh: ${refreshInterval}s | Period: ${this.config.historicalPeriod} days`);
  }

  /**
   * Get classification color
   */
  private getClassificationColor(classification: string): string {
    switch (classification) {
      case 'elite': return 'green';
      case 'high': return 'cyan';
      case 'medium': return 'yellow';
      case 'low': return 'red';
      default: return 'white';
    }
  }

  /**
   * Get trend icon
   */
  private getTrendIcon(trend: string): string {
    switch (trend) {
      case 'improving': return '{green-fg}↗{/}';
      case 'degrading': return '{red-fg}↘{/}';
      case 'stable': return '{yellow-fg}→{/}';
      default: return '?';
    }
  }

  /**
   * Get environment color
   */
  private getEnvironmentColor(environment: string): string {
    switch (environment) {
      case 'production': return 'red';
      case 'staging': return 'yellow';
      case 'development': return 'green';
      default: return 'white';
    }
  }

  /**
   * Get severity color
   */
  private getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'magenta';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'white';
    }
  }

  /**
   * Show help dialog
   */
  private showHelp(): void {
    const helpContent = `
DORA Metrics Dashboard Help

KEYBOARD SHORTCUTS:
r       - Refresh data
h, ?    - Show this help
q, Esc  - Quit dashboard

DORA METRICS:
• Deployment Frequency - How often you deploy
• Lead Time - Time from commit to production
• MTTR - Mean Time to Recovery from incidents
• Change Failure Rate - % of deployments causing issues

CLASSIFICATIONS:
• Elite - Top 20% of performers
• High - Top 20-50% of performers
• Medium - Top 50-80% of performers
• Low - Bottom 20% of performers

ENVIRONMENT COLORS:
• Production - Red
• Staging - Yellow  
• Development - Green

Press any key to close this help.`;

    const helpBox = blessed.box({
      top: 'center',
      left: 'center',
      width: '80%',
      height: '80%',
      content: helpContent,
      border: {
        type: 'line'
      },
      style: {
        fg: 'white',
        bg: 'black',
        border: {
          fg: 'white'
        }
      }
    });

    this.screen.append(helpBox);
    helpBox.focus();
    
    helpBox.key(['escape', 'enter', 'space'], () => {
      this.screen.remove(helpBox);
      this.screen.render();
    });
    
    this.screen.render();
  }

  /**
   * Start auto-refresh timer
   */
  private startAutoRefresh(): void {
    this.refreshTimer = setInterval(() => {
      if (this.isRunning) {
        this.refreshData();
      }
    }, this.config.refreshInterval);
  }

  /**
   * Render header for simple display
   */
  private renderHeader(): void {
    console.log(chalk.blue.bold('╔════════════════════════════════════════════════════════════════╗'));
    console.log(chalk.blue.bold('║                    DORA Metrics Dashboard                      ║'));
    console.log(chalk.blue.bold('╚════════════════════════════════════════════════════════════════╝'));
    console.log();
  }

  /**
   * Render metrics summary for simple display
   */
  private renderMetricsSummary(metrics: DORAMetrics): void {
    console.log(chalk.cyan('📊 DORA Metrics Summary'));
    console.log(chalk.gray(`Period: ${metrics.period.start.toLocaleDateString()} - ${metrics.period.end.toLocaleDateString()} (${metrics.period.days} days)`));
    console.log();

    // Deployment Frequency
    const dfColor = this.getConsoleColor(metrics.deploymentFrequency.classification);
    console.log(chalk.blue('🚀 Deployment Frequency'));
    console.log(`   Value: ${dfColor(metrics.deploymentFrequency.value.toFixed(1))} ${metrics.deploymentFrequency.unit}`);
    console.log(`   Classification: ${dfColor(metrics.deploymentFrequency.classification.toUpperCase())}`);
    console.log();

    // Lead Time
    const ltColor = this.getConsoleColor(metrics.leadTime.classification);
    console.log(chalk.blue('⏱️  Lead Time for Changes'));
    console.log(`   Value: ${ltColor(metrics.leadTime.value.toFixed(1))} ${metrics.leadTime.unit}`);
    console.log(`   Median: ${metrics.leadTime.median.toFixed(1)} hours`);
    console.log(`   Classification: ${ltColor(metrics.leadTime.classification.toUpperCase())}`);
    console.log();

    // MTTR
    const mttrColor = this.getConsoleColor(metrics.mttr.classification);
    console.log(chalk.blue('🔧 Mean Time to Recovery'));
    console.log(`   Value: ${mttrColor(metrics.mttr.value.toFixed(1))} ${metrics.mttr.unit}`);
    console.log(`   Incidents: ${metrics.mttr.incidents}`);
    console.log(`   Classification: ${mttrColor(metrics.mttr.classification.toUpperCase())}`);
    console.log();

    // Change Failure Rate
    const cfrColor = this.getConsoleColor(metrics.changeFailureRate.classification);
    console.log(chalk.blue('💥 Change Failure Rate'));
    console.log(`   Value: ${cfrColor(metrics.changeFailureRate.value.toFixed(1))}%`);
    console.log(`   Failed: ${metrics.changeFailureRate.failed} / ${metrics.changeFailureRate.total}`);
    console.log(`   Classification: ${cfrColor(metrics.changeFailureRate.classification.toUpperCase())}`);
    console.log();
  }

  /**
   * Render recent activity for simple display
   */
  private renderRecentActivity(): void {
    const deployments = this.collector.getDeployments(undefined, 5);
    const incidents = this.collector.getIncidents(undefined, undefined, 5);

    console.log(chalk.cyan('📦 Recent Deployments'));
    if (deployments.length > 0) {
      deployments.forEach(d => {
        const status = d.success ? chalk.green('✓') : chalk.red('✗');
        const env = d.environment.toUpperCase().padEnd(11);
        const time = d.timestamp.toLocaleString();
        console.log(`   ${status} ${env} ${d.version || 'unknown'} - ${time}`);
      });
    } else {
      console.log(chalk.gray('   No recent deployments'));
    }
    console.log();

    console.log(chalk.cyan('🚨 Recent Incidents'));
    if (incidents.length > 0) {
      incidents.forEach(i => {
        const status = i.resolved ? chalk.green('✓') : chalk.red('●');
        const severity = i.severity.toUpperCase().padEnd(8);
        const time = i.timestamp.toLocaleString();
        const mttr = i.mttr ? ` (MTTR: ${Math.round(i.mttr / (1000 * 60))}m)` : '';
        console.log(`   ${status} ${severity} ${i.description.substring(0, 50)}...${mttr}`);
      });
    } else {
      console.log(chalk.gray('   No recent incidents'));
    }
    console.log();
  }

  /**
   * Get console color for classification
   */
  private getConsoleColor(classification: string): (text: string) => string {
    switch (classification) {
      case 'elite': return chalk.green.bold;
      case 'high': return chalk.cyan.bold;
      case 'medium': return chalk.yellow.bold;
      case 'low': return chalk.red.bold;
      default: return chalk.white;
    }
  }
}

export default DORADashboard;