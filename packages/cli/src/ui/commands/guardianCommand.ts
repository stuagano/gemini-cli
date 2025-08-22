/**
 * Guardian Command
 * CLI commands for Guardian continuous validation
 */

import { Command } from 'commander';
import chalk from 'chalk';
import GuardianContinuousValidation, { ValidationSeverity, ValidationCategory } from '../../agents/guardian-continuous-validation.js';
import { Config } from '@google/gemini-cli-core';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

interface GuardianCommandOptions {
  start?: boolean;
  stop?: boolean;
  status?: boolean;
  validate?: string;
  project?: boolean;
  preCommit?: string;
  preDeploy?: string;
  config?: boolean;
  watch?: boolean;
  autoFix?: boolean;
  severity?: string;
  category?: string;
  json?: boolean;
  verbose?: boolean;
}

export function createGuardianCommand(config: Config): Command {
  const guardian = new GuardianContinuousValidation(config);
  
  const command = new Command('guardian')
    .description('Guardian continuous validation for real-time code quality monitoring')
    .option('-s, --start', 'Start continuous validation')
    .option('-S, --stop', 'Stop continuous validation')
    .option('--status', 'Show validation status')
    .option('-v, --validate <file>', 'Validate specific file')
    .option('-p, --project', 'Validate entire project')
    .option('--pre-commit <files>', 'Run pre-commit validation on files (comma-separated)')
    .option('--pre-deploy [target]', 'Run pre-deployment validation (default: production)')
    .option('-c, --config', 'Show current configuration')
    .option('-w, --watch', 'Enable file watching (used with --start)')
    .option('--auto-fix', 'Enable auto-fixing of issues')
    .option('--severity <level>', 'Filter by severity (critical|error|warning|info)')
    .option('--category <cat>', 'Filter by category (security|performance|quality|architecture|testing|deployment)')
    .option('--json', 'Output in JSON format')
    .option('--verbose', 'Verbose output')
    .action(async (options: GuardianCommandOptions) => {
      try {
        await executeGuardianCommand(guardian, options);
      } catch (error) {
        console.error(chalk.red('❌ Guardian command failed:'), error);
        process.exit(1);
      }
    });

  // Add subcommands
  command
    .command('start [path]')
    .description('Start Guardian continuous validation')
    .option('-w, --watch', 'Enable real-time file watching')
    .option('--auto-fix', 'Enable automatic issue fixing')
    .option('--interval <seconds>', 'Validation interval in seconds', '5')
    .action(async (projectPath: string = process.cwd(), options) => {
      try {
        // Update configuration
        if (options.autoFix) {
          guardian.updateConfig({ auto_fix_enabled: true });
        }
        if (options.watch) {
          guardian.updateConfig({ real_time_validation: true });
        }
        if (options.interval) {
          guardian.updateConfig({ validation_interval: parseInt(options.interval) * 1000 });
        }

        await guardian.startContinuousValidation(projectPath);
        
        // Keep process alive
        process.stdin.resume();
        console.log(chalk.gray('\nPress Ctrl+C to stop Guardian validation\n'));
        
      } catch (error) {
        console.error(chalk.red('❌ Failed to start Guardian:'), error);
        process.exit(1);
      }
    });

  command
    .command('validate <target>')
    .description('Validate file or project')
    .option('--severity <level>', 'Filter by severity level')
    .option('--category <cat>', 'Filter by category')
    .option('--json', 'Output in JSON format')
    .action(async (target: string, options) => {
      try {
        if (target === 'project' || target === '.') {
          const report = await guardian.validateProject();
          displayValidationReport(report, options);
        } else {
          const issues = await guardian.validateFile(target);
          displayFileValidation(target, issues, options);
        }
      } catch (error) {
        console.error(chalk.red('❌ Validation failed:'), error);
        process.exit(1);
      }
    });

  command
    .command('pre-commit')
    .description('Run pre-commit validation')
    .argument('[files...]', 'Files to validate')
    .option('--json', 'Output in JSON format')
    .action(async (files: string[], options) => {
      try {
        if (files.length === 0) {
          // Get changed files from git
          files = await getChangedFiles();
        }
        
        const result = await guardian.validateBeforeCommit(files);
        displayPreCommitResult(result, options);
        
        if (!result.validation_passed) {
          process.exit(1);
        }
      } catch (error) {
        console.error(chalk.red('❌ Pre-commit validation failed:'), error);
        process.exit(1);
      }
    });

  command
    .command('pre-deploy [target]')
    .description('Run pre-deployment validation')
    .option('--json', 'Output in JSON format')
    .action(async (target: string = 'production', options) => {
      try {
        const result = await guardian.validateBeforeDeployment(target);
        displayPreDeployResult(result, options);
        
        if (!result.deployment_approved) {
          process.exit(1);
        }
      } catch (error) {
        console.error(chalk.red('❌ Pre-deployment validation failed:'), error);
        process.exit(1);
      }
    });

  command
    .command('status')
    .description('Show Guardian validation status')
    .option('--json', 'Output in JSON format')
    .action(async (options) => {
      try {
        const status = guardian.getValidationStatus();
        displayStatus(status, options);
      } catch (error) {
        console.error(chalk.red('❌ Failed to get status:'), error);
        process.exit(1);
      }
    });

  command
    .command('config')
    .description('Manage Guardian configuration')
    .option('--show', 'Show current configuration')
    .option('--set <key=value>', 'Set configuration value')
    .option('--json', 'Output in JSON format')
    .action(async (options) => {
      try {
        if (options.set) {
          const [key, value] = options.set.split('=');
          const config: any = {};
          
          // Parse value
          if (value === 'true') config[key] = true;
          else if (value === 'false') config[key] = false;
          else if (!isNaN(Number(value))) config[key] = Number(value);
          else config[key] = value;
          
          guardian.updateConfig(config);
          console.log(chalk.green(`✅ Configuration updated: ${key} = ${value}`));
        } else {
          const status = guardian.getValidationStatus();
          displayConfiguration(status.config, options);
        }
      } catch (error) {
        console.error(chalk.red('❌ Configuration error:'), error);
        process.exit(1);
      }
    });

  return command;
}

/**
 * Execute main Guardian command
 */
async function executeGuardianCommand(
  guardian: GuardianContinuousValidation,
  options: GuardianCommandOptions
): Promise<void> {
  // Handle legacy options
  if (options.start) {
    await guardian.startContinuousValidation();
    process.stdin.resume();
    console.log(chalk.gray('\nPress Ctrl+C to stop Guardian validation\n'));
    return;
  }

  if (options.status) {
    const status = guardian.getValidationStatus();
    displayStatus(status, options);
    return;
  }

  if (options.validate) {
    const issues = await guardian.validateFile(options.validate);
    displayFileValidation(options.validate, issues, options);
    return;
  }

  if (options.project) {
    const report = await guardian.validateProject();
    displayValidationReport(report, options);
    return;
  }

  if (options.preCommit) {
    const files = options.preCommit.split(',').map(f => f.trim());
    const result = await guardian.validateBeforeCommit(files);
    displayPreCommitResult(result, options);
    
    if (!result.validation_passed) {
      process.exit(1);
    }
    return;
  }

  if (options.preDeploy) {
    const target = typeof options.preDeploy === 'string' ? options.preDeploy : 'production';
    const result = await guardian.validateBeforeDeployment(target);
    displayPreDeployResult(result, options);
    
    if (!result.deployment_approved) {
      process.exit(1);
    }
    return;
  }

  if (options.config) {
    const status = guardian.getValidationStatus();
    displayConfiguration(status.config, options);
    return;
  }

  // No specific action, show help
  console.log(chalk.yellow('No action specified. Use --help for available options.'));
}

/**
 * Display validation report
 */
function displayValidationReport(report: any, options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  console.log(chalk.blue('\n📊 Project Validation Report'));
  console.log(chalk.gray(`Session: ${report.session_id}`));
  console.log(chalk.gray(`Duration: ${report.duration_seconds.toFixed(2)}s`));
  console.log(chalk.gray(`Files checked: ${report.files_checked}`));
  console.log(chalk.gray(`Issues found: ${report.issues_found.length}`));

  if (report.issues_found.length > 0) {
    console.log(chalk.blue('\n🔍 Issues by severity:'));
    
    const filteredIssues = filterIssues(report.issues_found, options);
    const groupedBySeverity = groupBySeverity(filteredIssues);
    
    for (const [severity, issues] of Object.entries(groupedBySeverity)) {
      const color = getSeverityColor(severity as ValidationSeverity);
      console.log(color(`\n${severity.toUpperCase()} (${issues.length} issues):`));
      
      issues.slice(0, 5).forEach((issue: any) => {
        console.log(color(`  • ${issue.title}`));
        console.log(chalk.gray(`    ${issue.file_path}:${issue.line_number || '?'}`));
        if (options.verbose && issue.suggestion) {
          console.log(chalk.gray(`    💡 ${issue.suggestion}`));
        }
      });
      
      if (issues.length > 5) {
        console.log(chalk.gray(`    ... and ${issues.length - 5} more`));
      }
    }
  } else {
    console.log(chalk.green('\n✅ No issues found!'));
  }
}

/**
 * Display file validation results
 */
function displayFileValidation(filePath: string, issues: any[], options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify({ file: filePath, issues }, null, 2));
    return;
  }

  console.log(chalk.blue(`\n📁 Validation: ${filePath}`));
  
  if (issues.length === 0) {
    console.log(chalk.green('✅ No issues found'));
    return;
  }

  const filteredIssues = filterIssues(issues, options);
  
  console.log(chalk.yellow(`⚠️  Found ${filteredIssues.length} issues:`));
  
  filteredIssues.forEach(issue => {
    const color = getSeverityColor(issue.severity);
    console.log(color(`\n${issue.severity.toUpperCase()}: ${issue.title}`));
    console.log(chalk.gray(`  Line ${issue.line_number || '?'}: ${issue.description}`));
    if (issue.code_snippet) {
      console.log(chalk.gray(`  Code: ${issue.code_snippet}`));
    }
    if (issue.suggestion) {
      console.log(chalk.blue(`  💡 ${issue.suggestion}`));
    }
  });
}

/**
 * Display pre-commit validation result
 */
function displayPreCommitResult(result: any, options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  if (result.validation_passed) {
    console.log(chalk.green('✅ Pre-commit validation passed'));
  } else {
    console.log(chalk.red('❌ Pre-commit validation failed'));
    if (result.blocking_reason) {
      console.log(chalk.yellow(`Reason: ${result.blocking_reason}`));
    }
  }
  
  if (result.issues_found > 0) {
    console.log(chalk.yellow(`Found ${result.issues_found} issues`));
    
    result.issues.slice(0, 10).forEach((issue: any) => {
      const color = getSeverityColor(issue.severity as ValidationSeverity);
      console.log(color(`  • ${issue.title} (${issue.file}:${issue.line || '?'})`));
    });
    
    if (result.issues.length > 10) {
      console.log(chalk.gray(`  ... and ${result.issues.length - 10} more issues`));
    }
  }
}

/**
 * Display pre-deployment validation result
 */
function displayPreDeployResult(result: any, options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  if (result.deployment_approved) {
    console.log(chalk.green('✅ Deployment validation passed'));
  } else {
    console.log(chalk.red('❌ Deployment validation failed'));
    if (result.blocking_reason) {
      console.log(chalk.yellow(`Reason: ${result.blocking_reason}`));
    }
  }
  
  const report = result.validation_report;
  if (report && report.issues_found.length > 0) {
    console.log(chalk.yellow(`\nFound ${report.issues_found.length} total issues`));
    displayValidationReport(report, { ...options, verbose: false });
  }
}

/**
 * Display Guardian status
 */
function displayStatus(status: any, options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify(status, null, 2));
    return;
  }

  console.log(chalk.blue('🛡️  Guardian Continuous Validation Status\n'));
  
  const activeIcon = status.active ? chalk.green('✅ Active') : chalk.red('❌ Inactive');
  console.log(`Status: ${activeIcon}`);
  
  if (status.stats) {
    console.log(chalk.blue('\n📊 Statistics:'));
    console.log(`  Validations run: ${status.stats.validations_run}`);
    console.log(`  Issues found: ${status.stats.issues_found}`);
    console.log(`  Issues auto-fixed: ${status.stats.issues_auto_fixed}`);
    console.log(`  Files monitored: ${status.stats.files_monitored}`);
    console.log(`  Avg validation time: ${status.stats.avg_validation_time.toFixed(2)}ms`);
    
    if (status.stats.last_validation) {
      const lastValidation = new Date(status.stats.last_validation);
      console.log(`  Last validation: ${lastValidation.toLocaleString()}`);
    }
  }
  
  if (status.recent_issues && status.recent_issues.length > 0) {
    console.log(chalk.blue('\n🔍 Recent Issues:'));
    status.recent_issues.slice(0, 5).forEach((issue: any) => {
      const color = getSeverityColor(issue.severity);
      console.log(color(`  • ${issue.title} (${issue.file_path})`));
    });
    
    if (status.recent_issues.length > 5) {
      console.log(chalk.gray(`  ... and ${status.recent_issues.length - 5} more`));
    }
  }
}

/**
 * Display configuration
 */
function displayConfiguration(config: any, options: GuardianCommandOptions): void {
  if (options.json) {
    console.log(JSON.stringify(config, null, 2));
    return;
  }

  console.log(chalk.blue('⚙️  Guardian Configuration\n'));
  
  console.log(`Real-time validation: ${config.real_time_validation ? chalk.green('Enabled') : chalk.red('Disabled')}`);
  console.log(`Auto-fix: ${config.auto_fix_enabled ? chalk.green('Enabled') : chalk.red('Disabled')}`);
  console.log(`Validation interval: ${config.validation_interval / 1000}s`);
  console.log(`Batch size: ${config.batch_size}`);
  console.log(`Notifications: ${config.notification_enabled ? chalk.green('Enabled') : chalk.red('Disabled')}`);
  
  console.log(chalk.blue('\n📁 File Patterns:'));
  console.log(`  Include: ${config.include_patterns.join(', ')}`);
  console.log(`  Exclude: ${config.exclude_patterns.join(', ')}`);
  
  console.log(chalk.blue('\n⚠️  Severity Thresholds:'));
  Object.entries(config.severity_thresholds).forEach(([severity, threshold]) => {
    const color = getSeverityColor(severity as ValidationSeverity);
    console.log(color(`  ${severity.toUpperCase()}: ${threshold}`));
  });
}

/**
 * Filter issues by severity and category
 */
function filterIssues(issues: any[], options: GuardianCommandOptions): any[] {
  let filtered = issues;
  
  if (options.severity) {
    filtered = filtered.filter(issue => 
      issue.severity.toLowerCase() === options.severity!.toLowerCase()
    );
  }
  
  if (options.category) {
    filtered = filtered.filter(issue => 
      issue.category.toLowerCase() === options.category!.toLowerCase()
    );
  }
  
  return filtered;
}

/**
 * Group issues by severity
 */
function groupBySeverity(issues: any[]): Record<string, any[]> {
  return issues.reduce((groups, issue) => {
    const severity = issue.severity;
    if (!groups[severity]) {
      groups[severity] = [];
    }
    groups[severity].push(issue);
    return groups;
  }, {});
}

/**
 * Get color for severity level
 */
function getSeverityColor(severity: ValidationSeverity): (text: string) => string {
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
 * Get changed files from git
 */
async function getChangedFiles(): Promise<string[]> {
  try {
    const { execSync } = require('child_process');
    const stdout = execSync('git diff --name-only HEAD', { encoding: 'utf8' });
    return stdout.trim().split('\n').filter(file => file.length > 0);
  } catch (error) {
    console.log(chalk.yellow('⚠️  Could not get changed files from git, please specify files manually'));
    return [];
  }
}

export default createGuardianCommand;