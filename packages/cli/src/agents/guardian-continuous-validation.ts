/**
 * Guardian Continuous Validation
 * TypeScript CLI integration for real-time validation during development
 * Integrates with Python Guardian backend for comprehensive validation
 */

import { EventEmitter } from 'events';
import chokidar from 'chokidar';
import chalk from 'chalk';
import { Config } from '@google/gemini-cli-core';
import path from 'path';
import fs from 'fs/promises';

export enum ValidationSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export enum ValidationCategory {
  SECURITY = 'security',
  PERFORMANCE = 'performance',
  QUALITY = 'quality',
  ARCHITECTURE = 'architecture',
  TESTING = 'testing',
  DEPLOYMENT = 'deployment'
}

export interface ValidationIssue {
  id: string;
  rule_id: string;
  severity: ValidationSeverity;
  category: ValidationCategory;
  title: string;
  description: string;
  file_path: string;
  line_number?: number;
  column_number?: number;
  code_snippet?: string;
  suggestion?: string;
  auto_fixable: boolean;
  timestamp: Date;
  resolved: boolean;
  resolution_notes?: string;
}

export interface ValidationReport {
  session_id: string;
  timestamp: Date;
  duration_seconds: number;
  files_checked: number;
  rules_executed: number;
  issues_found: ValidationIssue[];
  performance_metrics: Record<string, any>;
  summary: Record<ValidationSeverity, number>;
}

export interface GuardianConfig {
  real_time_validation: boolean;
  auto_fix_enabled: boolean;
  validation_interval: number;
  batch_size: number;
  exclude_patterns: string[];
  include_patterns: string[];
  severity_thresholds: Record<ValidationSeverity, number>;
  notification_enabled: boolean;
  breaking_change_detection: boolean;
  test_coverage_monitoring: boolean;
  performance_regression_alerts: boolean;
}

export interface ValidationStats {
  validations_run: number;
  issues_found: number;
  issues_auto_fixed: number;
  avg_validation_time: number;
  files_monitored: number;
  last_validation: Date | null;
}

export class GuardianContinuousValidation extends EventEmitter {
  private config: Config;
  private guardianConfig: GuardianConfig;
  private apiBaseUrl: string;
  private fileWatcher: chokidar.FSWatcher | null = null;
  private validationQueue: Set<string> = new Set();
  private isValidating: boolean = false;
  private validationTimer: NodeJS.Timeout | null = null;
  private stats: ValidationStats;
  private recentIssues: ValidationIssue[] = [];
  private projectPath: string = process.cwd();

  constructor(config: Config) {
    super();
    this.config = config;
    this.apiBaseUrl = process.env.AGENT_SERVER_URL || 'http://localhost:2000';
    
    this.guardianConfig = {
      real_time_validation: true,
      auto_fix_enabled: true,
      validation_interval: 5000, // 5 seconds
      batch_size: 10,
      exclude_patterns: ['.git/', 'node_modules/', '__pycache__/', '*.pyc', 'dist/', 'build/'],
      include_patterns: ['*.ts', '*.js', '*.tsx', '*.jsx', '*.py', '*.java', '*.go'],
      severity_thresholds: {
        [ValidationSeverity.CRITICAL]: 0,
        [ValidationSeverity.ERROR]: 5,
        [ValidationSeverity.WARNING]: 20,
        [ValidationSeverity.INFO]: 50
      },
      notification_enabled: true,
      breaking_change_detection: true,
      test_coverage_monitoring: true,
      performance_regression_alerts: true
    };

    this.stats = {
      validations_run: 0,
      issues_found: 0,
      issues_auto_fixed: 0,
      avg_validation_time: 0,
      files_monitored: 0,
      last_validation: null
    };

    // Set up event handlers
    this.setupEventHandlers();
  }

  /**
   * Start continuous validation
   */
  async startContinuousValidation(projectPath: string = process.cwd()): Promise<void> {
    this.projectPath = projectPath;
    
    console.log(chalk.blue('🛡️  Starting Guardian Continuous Validation...'));
    
    try {
      // Initialize Python Guardian backend
      await this.initializeGuardianBackend();
      
      // Start file watching
      if (this.guardianConfig.real_time_validation) {
        await this.startFileWatching();
      }
      
      // Start periodic validation
      this.startPeriodicValidation();
      
      // Initial project validation
      await this.validateProject();
      
      console.log(chalk.green('✅ Guardian Continuous Validation started successfully'));
      this.emit('validation_started');
      
    } catch (error) {
      console.error(chalk.red('❌ Failed to start Guardian Continuous Validation:'), error);
      this.emit('validation_error', error);
      throw error;
    }
  }

  /**
   * Stop continuous validation
   */
  async stopContinuousValidation(): Promise<void> {
    console.log(chalk.yellow('⏹️  Stopping Guardian Continuous Validation...'));
    
    // Stop file watcher
    if (this.fileWatcher) {
      await this.fileWatcher.close();
      this.fileWatcher = null;
    }
    
    // Clear validation timer
    if (this.validationTimer) {
      clearInterval(this.validationTimer);
      this.validationTimer = null;
    }
    
    console.log(chalk.green('✅ Guardian Continuous Validation stopped'));
    this.emit('validation_stopped');
  }

  /**
   * Validate a single file
   */
  async validateFile(filePath: string): Promise<ValidationIssue[]> {
    if (!this.shouldValidateFile(filePath)) {
      return [];
    }

    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/validate-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          real_time: true
        })
      });

      if (!response.ok) {
        throw new Error(`Guardian API error: ${response.statusText}`);
      }

      const result = await response.json();
      const issues: ValidationIssue[] = result.issues || [];
      
      // Update stats
      this.updateValidationStats(Date.now() - startTime, issues.length);
      
      // Handle auto-fixes
      if (this.guardianConfig.auto_fix_enabled) {
        await this.handleAutoFixes(filePath, issues);
      }
      
      // Emit events
      if (issues.length > 0) {
        this.emit('issues_found', { file: filePath, issues });
        this.handleIssueNotifications(issues);
      }
      
      return issues;
      
    } catch (error) {
      console.error(chalk.red(`❌ Error validating ${filePath}:`), error);
      this.emit('validation_error', { file: filePath, error });
      return [];
    }
  }

  /**
   * Validate entire project
   */
  async validateProject(): Promise<ValidationReport> {
    const startTime = Date.now();
    
    console.log(chalk.blue('🔍 Running full project validation...'));
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/validate-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_path: this.projectPath,
          config: this.guardianConfig
        })
      });

      if (!response.ok) {
        throw new Error(`Guardian API error: ${response.statusText}`);
      }

      const report: ValidationReport = await response.json();
      
      // Update stats
      this.updateProjectValidationStats(report);
      
      // Store recent issues
      this.recentIssues = report.issues_found.slice(-50); // Keep last 50 issues
      
      // Display summary
      this.displayValidationSummary(report);
      
      // Check for blocking issues
      this.checkBlockingIssues(report.issues_found);
      
      this.emit('project_validated', report);
      
      return report;
      
    } catch (error) {
      console.error(chalk.red('❌ Project validation failed:'), error);
      this.emit('validation_error', error);
      throw error;
    }
  }

  /**
   * Get validation status
   */
  getValidationStatus(): {
    active: boolean;
    stats: ValidationStats;
    recent_issues: ValidationIssue[];
    config: GuardianConfig;
  } {
    return {
      active: this.fileWatcher !== null,
      stats: this.stats,
      recent_issues: this.recentIssues,
      config: this.guardianConfig
    };
  }

  /**
   * Update Guardian configuration
   */
  updateConfig(newConfig: Partial<GuardianConfig>): void {
    this.guardianConfig = { ...this.guardianConfig, ...newConfig };
    console.log(chalk.blue('⚙️  Guardian configuration updated'));
    this.emit('config_updated', this.guardianConfig);
  }

  /**
   * Validate before commit
   */
  async validateBeforeCommit(changedFiles: string[]): Promise<{
    validation_passed: boolean;
    issues_found: number;
    issues: ValidationIssue[];
    blocking_reason?: string;
  }> {
    console.log(chalk.blue('🔍 Running pre-commit validation...'));
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/validate-before-commit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          changed_files: changedFiles
        })
      });

      if (!response.ok) {
        throw new Error(`Guardian API error: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.validation_passed) {
        console.log(chalk.red('❌ Pre-commit validation failed'));
        console.log(chalk.yellow(`Reason: ${result.blocking_reason}`));
      } else {
        console.log(chalk.green('✅ Pre-commit validation passed'));
      }
      
      return result;
      
    } catch (error) {
      console.error(chalk.red('❌ Pre-commit validation error:'), error);
      return {
        validation_passed: false,
        issues_found: 0,
        issues: [],
        blocking_reason: `Validation service error: ${error}`
      };
    }
  }

  /**
   * Validate before deployment
   */
  async validateBeforeDeployment(deploymentTarget: string = 'production'): Promise<{
    deployment_approved: boolean;
    validation_report: ValidationReport;
    blocking_reason?: string;
  }> {
    console.log(chalk.blue(`🚀 Running pre-deployment validation for ${deploymentTarget}...`));
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/validate-before-deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deployment_target: deploymentTarget
        })
      });

      if (!response.ok) {
        throw new Error(`Guardian API error: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.deployment_approved) {
        console.log(chalk.red('❌ Deployment validation failed'));
        console.log(chalk.yellow(`Reason: ${result.blocking_reason}`));
      } else {
        console.log(chalk.green('✅ Deployment validation passed'));
      }
      
      return result;
      
    } catch (error) {
      console.error(chalk.red('❌ Deployment validation error:'), error);
      throw error;
    }
  }

  /**
   * Initialize Guardian backend
   */
  private async initializeGuardianBackend(): Promise<void> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/status`);
      
      if (!response.ok) {
        throw new Error('Guardian backend not available');
      }
      
      const status = await response.json();
      console.log(chalk.green(`✅ Guardian backend connected: ${status.active_rules} rules active`));
      
    } catch (error) {
      console.log(chalk.yellow('⚠️  Guardian backend not available, using fallback mode'));
      // Continue with limited functionality
    }
  }

  /**
   * Start file watching
   */
  private async startFileWatching(): Promise<void> {
    const watchPatterns = this.guardianConfig.include_patterns.map(pattern => 
      path.join(this.projectPath, '**', pattern)
    );
    
    this.fileWatcher = chokidar.watch(watchPatterns, {
      ignored: this.guardianConfig.exclude_patterns.map(pattern => 
        path.join(this.projectPath, pattern)
      ),
      persistent: true,
      ignoreInitial: true
    });
    
    this.fileWatcher.on('change', (filePath) => {
      this.queueFileForValidation(filePath);
    });
    
    this.fileWatcher.on('add', (filePath) => {
      this.queueFileForValidation(filePath);
    });
    
    this.fileWatcher.on('ready', () => {
      const watchedPaths = this.fileWatcher?.getWatched();
      const fileCount = Object.values(watchedPaths || {}).reduce((acc, files) => acc + files.length, 0);
      this.stats.files_monitored = fileCount;
      
      console.log(chalk.green(`👀 Watching ${fileCount} files for changes`));
      this.emit('file_watching_started', { files_monitored: fileCount });
    });
    
    this.fileWatcher.on('error', (error) => {
      console.error(chalk.red('❌ File watcher error:'), error);
      this.emit('file_watcher_error', error);
    });
  }

  /**
   * Start periodic validation
   */
  private startPeriodicValidation(): void {
    this.validationTimer = setInterval(async () => {
      if (this.validationQueue.size > 0 && !this.isValidating) {
        await this.processValidationQueue();
      }
    }, this.guardianConfig.validation_interval);
  }

  /**
   * Queue file for validation
   */
  private queueFileForValidation(filePath: string): void {
    if (this.shouldValidateFile(filePath)) {
      this.validationQueue.add(filePath);
      this.emit('file_queued', { file: filePath, queue_size: this.validationQueue.size });
    }
  }

  /**
   * Process validation queue
   */
  private async processValidationQueue(): Promise<void> {
    if (this.isValidating || this.validationQueue.size === 0) {
      return;
    }
    
    this.isValidating = true;
    const filesToValidate = Array.from(this.validationQueue).slice(0, this.guardianConfig.batch_size);
    this.validationQueue.clear();
    
    console.log(chalk.blue(`🔍 Validating ${filesToValidate.length} changed files...`));
    
    try {
      const validationPromises = filesToValidate.map(file => this.validateFile(file));
      const results = await Promise.allSettled(validationPromises);
      
      let totalIssues = 0;
      for (const result of results) {
        if (result.status === 'fulfilled') {
          totalIssues += result.value.length;
        }
      }
      
      if (totalIssues > 0) {
        console.log(chalk.yellow(`⚠️  Found ${totalIssues} issues in ${filesToValidate.length} files`));
      } else {
        console.log(chalk.green(`✅ No issues found in ${filesToValidate.length} files`));
      }
      
    } catch (error) {
      console.error(chalk.red('❌ Batch validation error:'), error);
    } finally {
      this.isValidating = false;
    }
  }

  /**
   * Should validate file
   */
  private shouldValidateFile(filePath: string): boolean {
    // Check if file matches include patterns
    const matchesInclude = this.guardianConfig.include_patterns.some(pattern => 
      filePath.endsWith(pattern.replace('*', ''))
    );
    
    // Check if file matches exclude patterns
    const matchesExclude = this.guardianConfig.exclude_patterns.some(pattern => 
      filePath.includes(pattern.replace('/', ''))
    );
    
    return matchesInclude && !matchesExclude;
  }

  /**
   * Handle auto-fixes
   */
  private async handleAutoFixes(filePath: string, issues: ValidationIssue[]): Promise<void> {
    const autoFixableIssues = issues.filter(issue => issue.auto_fixable);
    
    if (autoFixableIssues.length === 0) {
      return;
    }
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/guardian/auto-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          issues: autoFixableIssues.map(issue => issue.id)
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        const fixedCount = result.fixes_applied || 0;
        
        if (fixedCount > 0) {
          console.log(chalk.green(`🔧 Auto-fixed ${fixedCount} issues in ${filePath}`));
          this.stats.issues_auto_fixed += fixedCount;
          this.emit('auto_fixes_applied', { file: filePath, fixes: fixedCount });
        }
      }
    } catch (error) {
      console.error(chalk.red('❌ Auto-fix error:'), error);
    }
  }

  /**
   * Handle issue notifications
   */
  private handleIssueNotifications(issues: ValidationIssue[]): void {
    if (!this.guardianConfig.notification_enabled) {
      return;
    }
    
    const criticalIssues = issues.filter(issue => issue.severity === ValidationSeverity.CRITICAL);
    const errorIssues = issues.filter(issue => issue.severity === ValidationSeverity.ERROR);
    
    if (criticalIssues.length > 0) {
      console.log(chalk.red.bold(`🚨 CRITICAL: ${criticalIssues.length} critical security/quality issues found!`));
      criticalIssues.forEach(issue => {
        console.log(chalk.red(`   ${issue.title} in ${issue.file_path}:${issue.line_number}`));
      });
    }
    
    if (errorIssues.length > 0) {
      console.log(chalk.yellow(`⚠️  ERROR: ${errorIssues.length} error-level issues found`));
    }
  }

  /**
   * Display validation summary
   */
  private displayValidationSummary(report: ValidationReport): void {
    console.log(chalk.blue('\n📊 Validation Summary:'));
    console.log(chalk.gray(`   Session: ${report.session_id}`));
    console.log(chalk.gray(`   Duration: ${report.duration_seconds.toFixed(2)}s`));
    console.log(chalk.gray(`   Files checked: ${report.files_checked}`));
    console.log(chalk.gray(`   Rules executed: ${report.rules_executed}`));
    console.log(chalk.gray(`   Total issues: ${report.issues_found.length}`));
    
    if (Object.keys(report.summary).length > 0) {
      console.log(chalk.blue('\n📈 Issues by severity:'));
      for (const [severity, count] of Object.entries(report.summary)) {
        const color = this.getSeverityColor(severity as ValidationSeverity);
        console.log(color(`   ${severity.toUpperCase()}: ${count}`));
      }
    }
  }

  /**
   * Check for blocking issues
   */
  private checkBlockingIssues(issues: ValidationIssue[]): void {
    const issuesBySeverity: Record<ValidationSeverity, number> = {
      [ValidationSeverity.CRITICAL]: 0,
      [ValidationSeverity.ERROR]: 0,
      [ValidationSeverity.WARNING]: 0,
      [ValidationSeverity.INFO]: 0
    };
    
    issues.forEach(issue => {
      issuesBySeverity[issue.severity]++;
    });
    
    const blockingIssues: string[] = [];
    
    for (const [severity, count] of Object.entries(issuesBySeverity)) {
      const threshold = this.guardianConfig.severity_thresholds[severity as ValidationSeverity];
      if (count > threshold) {
        blockingIssues.push(`${count} ${severity} issues (threshold: ${threshold})`);
      }
    }
    
    if (blockingIssues.length > 0) {
      console.log(chalk.red.bold('\n🚫 BLOCKING ISSUES DETECTED:'));
      blockingIssues.forEach(issue => {
        console.log(chalk.red(`   ${issue}`));
      });
      
      this.emit('blocking_issues', blockingIssues);
    }
  }

  /**
   * Update validation stats
   */
  private updateValidationStats(duration: number, issuesCount: number): void {
    this.stats.validations_run++;
    this.stats.issues_found += issuesCount;
    this.stats.last_validation = new Date();
    
    // Update average validation time
    const totalTime = this.stats.avg_validation_time * (this.stats.validations_run - 1) + duration;
    this.stats.avg_validation_time = totalTime / this.stats.validations_run;
  }

  /**
   * Update project validation stats
   */
  private updateProjectValidationStats(report: ValidationReport): void {
    this.stats.validations_run++;
    this.stats.issues_found += report.issues_found.length;
    this.stats.last_validation = new Date();
    this.stats.avg_validation_time = report.duration_seconds * 1000; // Convert to ms
  }

  /**
   * Get severity color
   */
  private getSeverityColor(severity: ValidationSeverity): (text: string) => string {
    switch (severity) {
      case ValidationSeverity.CRITICAL:
        return chalk.red.bold;
      case ValidationSeverity.ERROR:
        return chalk.red;
      case ValidationSeverity.WARNING:
        return chalk.yellow;
      case ValidationSeverity.INFO:
        return chalk.blue;
      default:
        return chalk.gray;
    }
  }

  /**
   * Setup event handlers
   */
  private setupEventHandlers(): void {
    // Handle process termination
    process.on('SIGINT', async () => {
      await this.stopContinuousValidation();
      process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
      await this.stopContinuousValidation();
      process.exit(0);
    });
  }
}

export default GuardianContinuousValidation;