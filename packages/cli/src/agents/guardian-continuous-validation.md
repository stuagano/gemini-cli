# Guardian Continuous Validation (CLI-004)

## Overview

Guardian Continuous Validation provides real-time validation during development to catch issues before they reach production. It integrates with the Python Guardian backend to deliver comprehensive code quality monitoring, security scanning, and performance analysis with auto-fixing capabilities.

## Architecture

### System Components

```mermaid
graph TD
    A[CLI TypeScript Interface] --> B[Python Guardian Backend]
    A --> C[File Watcher (chokidar)]
    A --> D[Validation Queue]
    B --> E[Validation Rules Engine]
    B --> F[Auto-Fix Engine]
    E --> G[Security Scanner]
    E --> H[Performance Analyzer]
    E --> I[Quality Checker]
    E --> J[Architecture Validator]
    E --> K[Test Coverage Monitor]
```

### Integration Points

1. **TypeScript CLI Layer** (`guardian-continuous-validation.ts`)
   - Real-time file watching with chokidar
   - Validation queue management
   - Event-driven notifications
   - CLI command interface

2. **Python Guardian Backend** (`guardian_continuous_validation.py`)
   - Comprehensive validation rules engine
   - Auto-fixing capabilities
   - Security and performance analysis
   - Detailed reporting

3. **CLI Commands** (`guardianCommand.ts`)
   - User-friendly command interface
   - Pre-commit and pre-deployment hooks
   - Configuration management
   - Status reporting

## Features

### 🛡️ Real-time Validation

- **File Watching**: Monitors source files for changes using chokidar
- **Instant Feedback**: Validates files immediately upon modification
- **Batch Processing**: Processes multiple files efficiently
- **Smart Filtering**: Only validates relevant file types

### 🔍 Comprehensive Rule Engine

#### Security Rules
- **Hardcoded Secrets Detection** (Critical)
  - Detects passwords, API keys, tokens
  - Excludes obvious placeholders
  - Suggests environment variables

- **SQL Injection Risk** (Error)
  - Identifies string concatenation in SQL queries
  - Recommends parameterized queries
  - Prevents injection vulnerabilities

#### Performance Rules
- **N+1 Query Detection** (Warning)
  - Finds database queries inside loops
  - Suggests batch loading strategies
  - Identifies performance bottlenecks

- **Memory Leak Detection** (Error)
  - Detects unclosed resources
  - Finds missing event listener cleanup
  - Prevents memory leaks

#### Quality Rules
- **Code Complexity** (Warning)
  - Calculates cyclomatic complexity
  - Suggests function decomposition
  - Maintains code readability

- **Dead Code Detection** (Info)
  - Finds unused functions and variables
  - Supports auto-removal
  - Keeps codebase clean

#### Architecture Rules
- **Dependency Cycle Detection** (Error)
- **Layer Violation Detection** (Warning)

#### Testing Rules
- **Test Coverage Monitoring** (Warning)
- **Missing Test Detection** (Info)

### 🔧 Auto-fixing Capabilities

- **Automatic Issue Resolution**: Fixes common issues automatically
- **Safe Transformations**: Only applies proven, safe fixes
- **User Confirmation**: Optional confirmation for destructive changes
- **Rollback Support**: Maintains backup of original code

### 📊 Breaking Change Detection

- **API Compatibility**: Checks for breaking API changes
- **Contract Validation**: Ensures interface compatibility
- **Dependency Impact**: Analyzes dependency version conflicts
- **Migration Guidance**: Provides upgrade paths

### 📈 Performance Regression Alerts

- **Baseline Tracking**: Maintains performance baselines
- **Threshold Monitoring**: Alerts on performance degradation
- **Trend Analysis**: Identifies performance trends
- **Resource Usage**: Monitors memory and CPU usage

### 🔔 Notification System

- **Severity-based Alerts**: Different notifications for different severities
- **Real-time Updates**: Immediate feedback on validation results
- **Integration Ready**: Supports Slack, Teams, email notifications
- **Customizable Thresholds**: Configurable alert levels

## Usage

### Starting Guardian

#### Basic Usage
```bash
# Start continuous validation in current directory
gemini guardian start

# Start with specific options
gemini guardian start --watch --auto-fix --interval 10

# Start in specific project
gemini guardian start /path/to/project
```

#### Advanced Configuration
```bash
# Enable all features
gemini guardian start \
  --watch \
  --auto-fix \
  --interval 5 \
  --enable-notifications \
  --breaking-change-detection \
  --performance-monitoring
```

### Validation Commands

#### File Validation
```bash
# Validate single file
gemini guardian validate src/auth.ts

# Validate with filtering
gemini guardian validate src/auth.ts --severity error --category security
```

#### Project Validation
```bash
# Validate entire project
gemini guardian validate project

# JSON output
gemini guardian validate project --json

# Verbose output
gemini guardian validate project --verbose
```

### Pre-commit Integration

#### Git Hook Setup
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
gemini guardian pre-commit
exit $?
```

#### Manual Pre-commit Check
```bash
# Check all changed files
gemini guardian pre-commit

# Check specific files
gemini guardian pre-commit src/auth.ts src/payment.ts

# JSON output for CI/CD
gemini guardian pre-commit --json
```

### Pre-deployment Validation

```bash
# Validate for production deployment
gemini guardian pre-deploy production

# Validate for staging
gemini guardian pre-deploy staging

# JSON output for CI/CD pipelines
gemini guardian pre-deploy production --json
```

### Status and Configuration

#### Status Check
```bash
# Current status
gemini guardian status

# Detailed status with recent issues
gemini guardian status --verbose

# JSON format
gemini guardian status --json
```

#### Configuration Management
```bash
# Show current configuration
gemini guardian config --show

# Update configuration
gemini guardian config --set auto_fix_enabled=true
gemini guardian config --set validation_interval=10
gemini guardian config --set severity_thresholds.error=10

# JSON configuration
gemini guardian config --show --json
```

## Configuration

### Default Configuration

```typescript
{
  real_time_validation: true,
  auto_fix_enabled: true,
  validation_interval: 5000, // 5 seconds
  batch_size: 10,
  exclude_patterns: ['.git/', 'node_modules/', '__pycache__/', '*.pyc', 'dist/', 'build/'],
  include_patterns: ['*.ts', '*.js', '*.tsx', '*.jsx', '*.py', '*.java', '*.go'],
  severity_thresholds: {
    critical: 0,  // Block on any critical issue
    error: 5,     // Block on more than 5 errors
    warning: 20,  // Block on more than 20 warnings
    info: 50      // Block on more than 50 info issues
  },
  notification_enabled: true,
  breaking_change_detection: true,
  test_coverage_monitoring: true,
  performance_regression_alerts: true
}
```

### Environment Variables

```bash
# Guardian backend URL
export AGENT_SERVER_URL=http://localhost:2000

# Enable debug logging
export DEBUG=guardian:*

# Notification settings
export GUARDIAN_SLACK_WEBHOOK=https://hooks.slack.com/...
export GUARDIAN_TEAMS_WEBHOOK=https://outlook.office.com/...
```

## Integration

### CI/CD Pipeline Integration

#### GitHub Actions
```yaml
name: Guardian Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm install
      
      - name: Start Guardian backend
        run: ./start_server.sh &
        
      - name: Pre-commit validation
        run: gemini guardian pre-commit --json
        
      - name: Pre-deployment validation
        if: github.ref == 'refs/heads/main'
        run: gemini guardian pre-deploy production --json
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Guardian Validation') {
            steps {
                sh 'gemini guardian validate project --json > validation-report.json'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'validation-report.json',
                    reportName: 'Guardian Validation Report'
                ])
            }
        }
        stage('Pre-deployment Check') {
            when { branch 'main' }
            steps {
                sh 'gemini guardian pre-deploy production'
            }
        }
    }
}
```

### IDE Integration

Guardian can be integrated with IDEs for real-time feedback:

#### VS Code Extension Integration
```typescript
// Extension integration point
import GuardianContinuousValidation from '@google/gemini-cli/guardian';

const guardian = new GuardianContinuousValidation(config);
await guardian.startContinuousValidation(workspace.rootPath);

guardian.on('issues_found', (data) => {
  // Display issues in VS Code problems panel
  updateProblemsPanel(data.issues);
});
```

### Slack/Teams Integration

#### Webhook Configuration
```bash
# Configure Slack notifications
gemini guardian config --set notification_webhook="https://hooks.slack.com/..."
gemini guardian config --set notification_channel="#dev-alerts"

# Configure Teams notifications
gemini guardian config --set teams_webhook="https://outlook.office.com/..."
```

#### Custom Notification Templates
```json
{
  "slack_template": {
    "critical": "🚨 *CRITICAL* Guardian Alert: {issue_count} critical issues found in {file_path}",
    "error": "⚠️ *ERROR* Guardian Alert: {issue_count} error-level issues detected",
    "warning": "💡 Guardian Notice: {issue_count} warnings in latest validation"
  }
}
```

## API Reference

### GuardianContinuousValidation Class

#### Constructor
```typescript
constructor(config: Config)
```

#### Main Methods

##### Start/Stop Validation
```typescript
async startContinuousValidation(projectPath?: string): Promise<void>
async stopContinuousValidation(): Promise<void>
```

##### File and Project Validation
```typescript
async validateFile(filePath: string): Promise<ValidationIssue[]>
async validateProject(): Promise<ValidationReport>
```

##### Pre-commit and Deployment
```typescript
async validateBeforeCommit(changedFiles: string[]): Promise<ValidationResult>
async validateBeforeDeployment(target: string): Promise<DeploymentResult>
```

##### Configuration and Status
```typescript
getValidationStatus(): ValidationStatus
updateConfig(newConfig: Partial<GuardianConfig>): void
```

### Data Types

#### ValidationIssue
```typescript
interface ValidationIssue {
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
```

#### ValidationReport
```typescript
interface ValidationReport {
  session_id: string;
  timestamp: Date;
  duration_seconds: number;
  files_checked: number;
  rules_executed: number;
  issues_found: ValidationIssue[];
  performance_metrics: Record<string, any>;
  summary: Record<ValidationSeverity, number>;
}
```

#### GuardianConfig
```typescript
interface GuardianConfig {
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
```

## Events

Guardian emits various events for integration and monitoring:

### Validation Events
- `validation_started`: Guardian has started
- `validation_stopped`: Guardian has stopped
- `file_queued`: File added to validation queue
- `issues_found`: Issues detected in file
- `project_validated`: Project validation completed

### Auto-fix Events
- `auto_fixes_applied`: Auto-fixes have been applied
- `auto_fix_failed`: Auto-fix attempt failed

### Alert Events
- `blocking_issues`: Issues that block commit/deployment
- `config_updated`: Configuration has been updated
- `validation_error`: Validation process error

### Monitoring Events
- `performance_regression`: Performance degradation detected
- `breaking_change`: Breaking change detected
- `coverage_threshold`: Test coverage below threshold

## Performance

### Benchmarks

- **File Validation**: < 100ms for typical source files
- **Project Validation**: < 30s for projects with 1000+ files
- **Memory Usage**: < 100MB during continuous monitoring
- **CPU Impact**: < 5% during background monitoring

### Optimization Features

- **Incremental Validation**: Only validates changed files
- **Parallel Processing**: Concurrent validation of multiple files
- **Smart Caching**: Caches validation results for unchanged files
- **Batched Operations**: Groups file changes for efficient processing
- **Resource Throttling**: Configurable resource limits

## Troubleshooting

### Common Issues

#### Guardian Backend Not Available
```bash
# Check backend status
curl http://localhost:2000/api/v1/guardian/status

# Start backend manually
./start_server.sh

# Check logs
tail -f guardian.log
```

#### File Watching Issues
```bash
# Check file system limits (Linux)
cat /proc/sys/fs/inotify/max_user_watches

# Increase limits if needed
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### High False Positive Rate
```bash
# Adjust sensitivity thresholds
gemini guardian config --set severity_thresholds.warning=50

# Disable specific rule categories
gemini guardian config --set enable_quality_rules=false

# Customize exclude patterns
gemini guardian config --set exclude_patterns="test/**,*.test.ts"
```

#### Performance Issues
```bash
# Reduce validation frequency
gemini guardian config --set validation_interval=10000

# Reduce batch size
gemini guardian config --set batch_size=5

# Disable auto-fixing
gemini guardian config --set auto_fix_enabled=false
```

### Debug Mode

Enable detailed logging:

```bash
# Enable debug logging
export DEBUG=guardian:*
gemini guardian start --verbose

# View validation statistics
gemini guardian status --verbose

# Check configuration
gemini guardian config --show --json
```

### Health Checks

#### System Health
```bash
# Check Guardian status
gemini guardian status

# Validate backend connectivity
curl -f http://localhost:2000/api/v1/health || echo "Backend unavailable"

# Test file validation
gemini guardian validate package.json
```

#### Performance Monitoring
```bash
# Monitor validation performance
gemini guardian status --json | jq '.stats.avg_validation_time'

# Check memory usage
ps aux | grep guardian

# Monitor file watching
lsof | grep guardian | wc -l
```

## Best Practices

### Development Workflow

1. **Start Guardian Early**: Begin validation from project start
2. **Configure Appropriately**: Set thresholds matching team standards
3. **Review Issues Regularly**: Address validation issues promptly
4. **Use Pre-commit Hooks**: Prevent issues from entering repository
5. **Monitor Performance**: Track validation metrics over time

### Team Integration

1. **Establish Standards**: Define team-wide validation rules
2. **Train Developers**: Ensure team understands Guardian capabilities
3. **Customize Rules**: Adapt rules to project requirements
4. **Share Configuration**: Use consistent Guardian config across team
5. **Review Reports**: Regular team review of validation reports

### CI/CD Integration

1. **Fail Fast**: Block builds on critical issues
2. **Generate Reports**: Produce validation artifacts
3. **Track Metrics**: Monitor validation trends over time
4. **Automate Fixes**: Use auto-fixing in appropriate environments
5. **Environment-specific Rules**: Stricter rules for production

## Migration Guide

### From Manual Code Review

1. **Start with Warnings**: Begin with non-blocking validation
2. **Gradually Increase Strictness**: Progressively lower thresholds
3. **Focus on Critical Issues**: Prioritize security and performance
4. **Train Team**: Educate on Guardian capabilities
5. **Measure Improvement**: Track code quality metrics

### From Other Tools

#### ESLint/TSLint Migration
```bash
# Import existing ESLint rules
gemini guardian import-eslint .eslintrc.json

# Map severity levels
gemini guardian config --set eslint_error_mapping="guardian_error"
```

#### SonarQube Integration
```bash
# Export Guardian results to SonarQube format
gemini guardian validate project --format sonarqube > sonar-results.xml
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: AI-powered rule suggestions
2. **Custom Rule Creation**: User-defined validation rules
3. **Advanced Analytics**: Detailed trend analysis and reporting
4. **Multi-language Support**: Broader language coverage
5. **Cloud Integration**: Distributed validation processing

### Extensibility

Guardian is designed for extensibility:

- **Plugin Architecture**: Custom validation plugins
- **Rule Engine API**: Create custom validation rules
- **Notification Adapters**: Custom notification channels
- **Report Generators**: Custom report formats
- **Integration Hooks**: Custom workflow integrations

## Support and Resources

### Documentation
- [Guardian API Reference](./guardian-api.md)
- [Rule Development Guide](./guardian-rules.md)
- [Integration Examples](./guardian-examples.md)

### Community
- GitHub Issues: Report bugs and request features
- Discord: Community support and discussions
- Stack Overflow: Tagged questions for help

### Professional Support
- Enterprise support available
- Custom rule development services
- Training and consulting services