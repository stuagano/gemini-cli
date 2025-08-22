/**
 * DORA Metrics Implementation
 * Tracks and calculates DevOps Research and Assessment metrics
 */

import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';
import { execSync } from 'child_process';
import chalk from 'chalk';

export interface DeploymentEvent {
  id: string;
  timestamp: Date;
  environment: 'development' | 'staging' | 'production';
  version: string;
  commit: string;
  success: boolean;
  duration?: number; // milliseconds
  rollback?: boolean;
  changes?: string[];
}

export interface IncidentEvent {
  id: string;
  timestamp: Date;
  environment: 'development' | 'staging' | 'production';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  resolved?: boolean;
  resolvedAt?: Date;
  mttr?: number; // milliseconds
  deploymentId?: string; // deployment that caused the incident
}

export interface CommitEvent {
  hash: string;
  timestamp: Date;
  author: string;
  message: string;
  files: string[];
  additions: number;
  deletions: number;
  branch: string;
  pullRequestId?: string;
  deployedAt?: Date;
}

export interface DORAMetrics {
  deploymentFrequency: {
    value: number;
    unit: 'per-day' | 'per-week' | 'per-month';
    trend: 'increasing' | 'decreasing' | 'stable';
    classification: 'elite' | 'high' | 'medium' | 'low';
  };
  leadTime: {
    value: number; // milliseconds
    unit: 'hours' | 'days' | 'weeks';
    median: number;
    p90: number;
    trend: 'improving' | 'degrading' | 'stable';
    classification: 'elite' | 'high' | 'medium' | 'low';
  };
  mttr: {
    value: number; // milliseconds
    unit: 'minutes' | 'hours' | 'days';
    median: number;
    incidents: number;
    trend: 'improving' | 'degrading' | 'stable';
    classification: 'elite' | 'high' | 'medium' | 'low';
  };
  changeFailureRate: {
    value: number; // percentage
    failed: number;
    total: number;
    trend: 'improving' | 'degrading' | 'stable';
    classification: 'elite' | 'high' | 'medium' | 'low';
  };
  period: {
    start: Date;
    end: Date;
    days: number;
  };
}

export interface DORAConfiguration {
  dataPath: string;
  gitRepository?: string;
  environments: string[];
  deploymentPatterns: {
    commitMessagePattern?: RegExp;
    tagPattern?: RegExp;
    branchPattern?: RegExp;
  };
  incidentPatterns: {
    keywords: string[];
    severityKeywords: Record<string, string[]>;
  };
}

export class DORAMetricsCollector extends EventEmitter {
  private config: DORAConfiguration;
  private deployments: DeploymentEvent[] = [];
  private incidents: IncidentEvent[] = [];
  private commits: CommitEvent[] = [];
  private isInitialized: boolean = false;

  constructor(config?: Partial<DORAConfiguration>) {
    super();
    
    this.config = {
      dataPath: path.join(process.cwd(), '.gemini', 'dora-metrics'),
      environments: ['development', 'staging', 'production'],
      deploymentPatterns: {
        commitMessagePattern: /^(deploy|release|ship):\s/i,
        tagPattern: /^v?\d+\.\d+\.\d+/,
        branchPattern: /^(main|master|release\/.+)$/
      },
      incidentPatterns: {
        keywords: ['fix', 'bug', 'hotfix', 'incident', 'rollback', 'revert'],
        severityKeywords: {
          critical: ['critical', 'urgent', 'p0', 'sev1'],
          high: ['high', 'important', 'p1', 'sev2'],
          medium: ['medium', 'moderate', 'p2', 'sev3'],
          low: ['low', 'minor', 'p3', 'sev4']
        }
      },
      ...config
    };
  }

  /**
   * Initialize the DORA metrics collector
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Ensure data directory exists
      await fs.mkdir(this.config.dataPath, { recursive: true });

      // Load existing data
      await this.loadData();

      // Initialize Git integration if repository is specified
      if (this.config.gitRepository || await this.isGitRepository()) {
        await this.initializeGitIntegration();
      }

      this.isInitialized = true;
      console.log(chalk.green('✓ DORA metrics collector initialized'));

      this.emit('initialized');
    } catch (error) {
      console.error(chalk.red('Failed to initialize DORA metrics collector:'), error);
      throw error;
    }
  }

  /**
   * Record a deployment event
   */
  async recordDeployment(deployment: Omit<DeploymentEvent, 'id' | 'timestamp'>): Promise<void> {
    const event: DeploymentEvent = {
      id: `deploy_${Date.now()}_${Math.random().toString(36).substring(7)}`,
      timestamp: new Date(),
      ...deployment
    };

    this.deployments.push(event);
    await this.saveData();

    console.log(chalk.blue(`📦 Deployment recorded: ${event.version} to ${event.environment}`));
    this.emit('deployment_recorded', event);
  }

  /**
   * Record an incident event
   */
  async recordIncident(incident: Omit<IncidentEvent, 'id' | 'timestamp'>): Promise<void> {
    const event: IncidentEvent = {
      id: `incident_${Date.now()}_${Math.random().toString(36).substring(7)}`,
      timestamp: new Date(),
      ...incident
    };

    this.incidents.push(event);
    await this.saveData();

    console.log(chalk.red(`🚨 Incident recorded: ${event.severity} in ${event.environment}`));
    this.emit('incident_recorded', event);
  }

  /**
   * Resolve an incident
   */
  async resolveIncident(incidentId: string, resolution?: string): Promise<void> {
    const incident = this.incidents.find(i => i.id === incidentId);
    if (!incident) {
      throw new Error(`Incident ${incidentId} not found`);
    }

    incident.resolved = true;
    incident.resolvedAt = new Date();
    incident.mttr = incident.resolvedAt.getTime() - incident.timestamp.getTime();

    await this.saveData();

    const mttrHours = Math.round(incident.mttr / (1000 * 60 * 60) * 100) / 100;
    console.log(chalk.green(`✓ Incident ${incidentId} resolved (MTTR: ${mttrHours}h)`));
    
    this.emit('incident_resolved', incident);
  }

  /**
   * Calculate DORA metrics for a given period
   */
  calculateMetrics(startDate?: Date, endDate?: Date): DORAMetrics {
    const end = endDate || new Date();
    const start = startDate || new Date(end.getTime() - (30 * 24 * 60 * 60 * 1000)); // 30 days default
    
    const periodDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));

    // Filter events to period
    const periodDeployments = this.deployments.filter(d => 
      d.timestamp >= start && d.timestamp <= end
    );
    const periodIncidents = this.incidents.filter(i => 
      i.timestamp >= start && i.timestamp <= end && i.resolved
    );
    const periodCommits = this.commits.filter(c => 
      c.timestamp >= start && c.timestamp <= end
    );

    // Calculate Deployment Frequency
    const deploymentFrequency = this.calculateDeploymentFrequency(periodDeployments, periodDays);

    // Calculate Lead Time
    const leadTime = this.calculateLeadTime(periodCommits, periodDeployments);

    // Calculate MTTR
    const mttr = this.calculateMTTR(periodIncidents);

    // Calculate Change Failure Rate
    const changeFailureRate = this.calculateChangeFailureRate(periodDeployments);

    return {
      deploymentFrequency,
      leadTime,
      mttr,
      changeFailureRate,
      period: {
        start,
        end,
        days: periodDays
      }
    };
  }

  /**
   * Calculate deployment frequency
   */
  private calculateDeploymentFrequency(deployments: DeploymentEvent[], days: number): DORAMetrics['deploymentFrequency'] {
    const productionDeployments = deployments.filter(d => d.environment === 'production');
    const frequency = productionDeployments.length / days;

    let unit: 'per-day' | 'per-week' | 'per-month';
    let value: number;
    let classification: 'elite' | 'high' | 'medium' | 'low';

    if (frequency >= 1) {
      unit = 'per-day';
      value = frequency;
      classification = 'elite';
    } else if (frequency >= 1/7) {
      unit = 'per-week';
      value = frequency * 7;
      classification = 'high';
    } else if (frequency >= 1/30) {
      unit = 'per-month';
      value = frequency * 30;
      classification = 'medium';
    } else {
      unit = 'per-month';
      value = frequency * 30;
      classification = 'low';
    }

    return {
      value: Math.round(value * 100) / 100,
      unit,
      trend: 'stable', // TODO: Calculate trend from historical data
      classification
    };
  }

  /**
   * Calculate lead time for changes
   */
  private calculateLeadTime(commits: CommitEvent[], deployments: DeploymentEvent[]): DORAMetrics['leadTime'] {
    const leadTimes: number[] = [];

    commits.forEach(commit => {
      const deployment = deployments.find(d => 
        d.commit === commit.hash || 
        (commit.deployedAt && Math.abs(d.timestamp.getTime() - commit.deployedAt.getTime()) < 60000)
      );

      if (deployment && commit.deployedAt) {
        const leadTime = commit.deployedAt.getTime() - commit.timestamp.getTime();
        leadTimes.push(leadTime);
      }
    });

    if (leadTimes.length === 0) {
      return {
        value: 0,
        unit: 'hours',
        median: 0,
        p90: 0,
        trend: 'stable',
        classification: 'low'
      };
    }

    const sorted = leadTimes.sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    const p90 = sorted[Math.floor(sorted.length * 0.9)];
    const average = leadTimes.reduce((sum, lt) => sum + lt, 0) / leadTimes.length;

    const medianHours = median / (1000 * 60 * 60);
    
    let unit: 'hours' | 'days' | 'weeks';
    let value: number;
    let classification: 'elite' | 'high' | 'medium' | 'low';

    if (medianHours < 24) {
      unit = 'hours';
      value = medianHours;
      classification = 'elite';
    } else if (medianHours < 7 * 24) {
      unit = 'days';
      value = medianHours / 24;
      classification = 'high';
    } else if (medianHours < 30 * 24) {
      unit = 'weeks';
      value = medianHours / (7 * 24);
      classification = 'medium';
    } else {
      unit = 'weeks';
      value = medianHours / (7 * 24);
      classification = 'low';
    }

    return {
      value: Math.round(value * 100) / 100,
      unit,
      median: Math.round(medianHours * 100) / 100,
      p90: Math.round((p90 / (1000 * 60 * 60)) * 100) / 100,
      trend: 'stable',
      classification
    };
  }

  /**
   * Calculate Mean Time To Recovery (MTTR)
   */
  private calculateMTTR(incidents: IncidentEvent[]): DORAMetrics['mttr'] {
    const resolvedIncidents = incidents.filter(i => i.resolved && i.mttr);
    
    if (resolvedIncidents.length === 0) {
      return {
        value: 0,
        unit: 'hours',
        median: 0,
        incidents: 0,
        trend: 'stable',
        classification: 'elite'
      };
    }

    const mttrs = resolvedIncidents.map(i => i.mttr!);
    const sorted = mttrs.sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    const average = mttrs.reduce((sum, mttr) => sum + mttr, 0) / mttrs.length;

    const medianHours = median / (1000 * 60 * 60);
    
    let unit: 'minutes' | 'hours' | 'days';
    let value: number;
    let classification: 'elite' | 'high' | 'medium' | 'low';

    if (medianHours < 1) {
      unit = 'minutes';
      value = medianHours * 60;
      classification = 'elite';
    } else if (medianHours < 24) {
      unit = 'hours';
      value = medianHours;
      classification = 'high';
    } else if (medianHours < 7 * 24) {
      unit = 'days';
      value = medianHours / 24;
      classification = 'medium';
    } else {
      unit = 'days';
      value = medianHours / 24;
      classification = 'low';
    }

    return {
      value: Math.round(value * 100) / 100,
      unit,
      median: Math.round(medianHours * 100) / 100,
      incidents: resolvedIncidents.length,
      trend: 'stable',
      classification
    };
  }

  /**
   * Calculate change failure rate
   */
  private calculateChangeFailureRate(deployments: DeploymentEvent[]): DORAMetrics['changeFailureRate'] {
    const productionDeployments = deployments.filter(d => d.environment === 'production');
    const failedDeployments = productionDeployments.filter(d => !d.success || d.rollback);
    
    const total = productionDeployments.length;
    const failed = failedDeployments.length;
    const rate = total > 0 ? (failed / total) * 100 : 0;

    let classification: 'elite' | 'high' | 'medium' | 'low';
    if (rate < 5) {
      classification = 'elite';
    } else if (rate < 10) {
      classification = 'high';
    } else if (rate < 20) {
      classification = 'medium';
    } else {
      classification = 'low';
    }

    return {
      value: Math.round(rate * 100) / 100,
      failed,
      total,
      trend: 'stable',
      classification
    };
  }

  /**
   * Initialize Git integration
   */
  private async initializeGitIntegration(): Promise<void> {
    try {
      // Load recent commits
      await this.loadGitCommits();
      console.log(chalk.blue(`📊 Loaded ${this.commits.length} Git commits`));
    } catch (error) {
      console.warn(chalk.yellow('⚠ Git integration failed:'), error);
    }
  }

  /**
   * Load Git commits
   */
  private async loadGitCommits(limit: number = 1000): Promise<void> {
    try {
      const gitLog = execSync(
        `git log --oneline --pretty=format:"%H|%ct|%an|%s" -n ${limit}`,
        { encoding: 'utf-8', cwd: this.config.gitRepository || process.cwd() }
      ).trim();

      if (!gitLog) return;

      const commits: CommitEvent[] = gitLog.split('\n').map(line => {
        const [hash, timestamp, author, message] = line.split('|');
        return {
          hash,
          timestamp: new Date(parseInt(timestamp) * 1000),
          author,
          message,
          files: [],
          additions: 0,
          deletions: 0,
          branch: 'main' // TODO: Get actual branch
        };
      });

      // Detect deployment commits
      commits.forEach(commit => {
        if (this.isDeploymentCommit(commit)) {
          commit.deployedAt = commit.timestamp;
        }
      });

      this.commits = commits;
    } catch (error) {
      throw new Error(`Failed to load Git commits: ${error}`);
    }
  }

  /**
   * Check if commit is a deployment commit
   */
  private isDeploymentCommit(commit: CommitEvent): boolean {
    const message = commit.message.toLowerCase();
    const patterns = this.config.deploymentPatterns;
    
    if (patterns.commitMessagePattern?.test(commit.message)) {
      return true;
    }

    // Check for deployment keywords
    const deploymentKeywords = ['deploy', 'release', 'ship', 'publish'];
    return deploymentKeywords.some(keyword => message.includes(keyword));
  }

  /**
   * Check if directory is a Git repository
   */
  private async isGitRepository(): Promise<boolean> {
    try {
      execSync('git rev-parse --git-dir', { 
        stdio: 'ignore', 
        cwd: this.config.gitRepository || process.cwd() 
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Load data from storage
   */
  private async loadData(): Promise<void> {
    try {
      const deploymentsPath = path.join(this.config.dataPath, 'deployments.json');
      const incidentsPath = path.join(this.config.dataPath, 'incidents.json');
      const commitsPath = path.join(this.config.dataPath, 'commits.json');

      // Load deployments
      try {
        const deploymentsData = await fs.readFile(deploymentsPath, 'utf-8');
        this.deployments = JSON.parse(deploymentsData).map((d: any) => ({
          ...d,
          timestamp: new Date(d.timestamp)
        }));
      } catch (error) {
        this.deployments = [];
      }

      // Load incidents
      try {
        const incidentsData = await fs.readFile(incidentsPath, 'utf-8');
        this.incidents = JSON.parse(incidentsData).map((i: any) => ({
          ...i,
          timestamp: new Date(i.timestamp),
          resolvedAt: i.resolvedAt ? new Date(i.resolvedAt) : undefined
        }));
      } catch (error) {
        this.incidents = [];
      }

      // Load commits
      try {
        const commitsData = await fs.readFile(commitsPath, 'utf-8');
        this.commits = JSON.parse(commitsData).map((c: any) => ({
          ...c,
          timestamp: new Date(c.timestamp),
          deployedAt: c.deployedAt ? new Date(c.deployedAt) : undefined
        }));
      } catch (error) {
        this.commits = [];
      }

      console.log(chalk.gray(`Loaded ${this.deployments.length} deployments, ${this.incidents.length} incidents, ${this.commits.length} commits`));
    } catch (error) {
      console.warn(chalk.yellow('Failed to load existing data:'), error);
    }
  }

  /**
   * Save data to storage
   */
  private async saveData(): Promise<void> {
    try {
      const deploymentsPath = path.join(this.config.dataPath, 'deployments.json');
      const incidentsPath = path.join(this.config.dataPath, 'incidents.json');
      const commitsPath = path.join(this.config.dataPath, 'commits.json');

      await Promise.all([
        fs.writeFile(deploymentsPath, JSON.stringify(this.deployments, null, 2)),
        fs.writeFile(incidentsPath, JSON.stringify(this.incidents, null, 2)),
        fs.writeFile(commitsPath, JSON.stringify(this.commits, null, 2))
      ]);
    } catch (error) {
      console.error(chalk.red('Failed to save DORA metrics data:'), error);
      throw error;
    }
  }

  /**
   * Get deployment history
   */
  getDeployments(environment?: string, limit?: number): DeploymentEvent[] {
    let filtered = this.deployments;
    
    if (environment) {
      filtered = filtered.filter(d => d.environment === environment);
    }

    filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    if (limit) {
      filtered = filtered.slice(0, limit);
    }

    return filtered;
  }

  /**
   * Get incident history
   */
  getIncidents(environment?: string, severity?: string, limit?: number): IncidentEvent[] {
    let filtered = this.incidents;
    
    if (environment) {
      filtered = filtered.filter(i => i.environment === environment);
    }

    if (severity) {
      filtered = filtered.filter(i => i.severity === severity);
    }

    filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    if (limit) {
      filtered = filtered.slice(0, limit);
    }

    return filtered;
  }

  /**
   * Export metrics data
   */
  async exportData(format: 'json' | 'csv' = 'json'): Promise<string> {
    const data = {
      deployments: this.deployments,
      incidents: this.incidents,
      commits: this.commits,
      exportDate: new Date()
    };

    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    }

    // TODO: Implement CSV export
    throw new Error('CSV export not yet implemented');
  }

  /**
   * Import metrics data
   */
  async importData(data: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    if (format === 'json') {
      const parsed = JSON.parse(data);
      
      if (parsed.deployments) {
        this.deployments = parsed.deployments.map((d: any) => ({
          ...d,
          timestamp: new Date(d.timestamp)
        }));
      }

      if (parsed.incidents) {
        this.incidents = parsed.incidents.map((i: any) => ({
          ...i,
          timestamp: new Date(i.timestamp),
          resolvedAt: i.resolvedAt ? new Date(i.resolvedAt) : undefined
        }));
      }

      if (parsed.commits) {
        this.commits = parsed.commits.map((c: any) => ({
          ...c,
          timestamp: new Date(c.timestamp),
          deployedAt: c.deployedAt ? new Date(c.deployedAt) : undefined
        }));
      }

      await this.saveData();
      console.log(chalk.green('✓ DORA metrics data imported successfully'));
    } else {
      throw new Error('CSV import not yet implemented');
    }
  }
}

export default DORAMetricsCollector;