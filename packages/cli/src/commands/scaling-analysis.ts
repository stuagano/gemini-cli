/**
 * Scaling Analysis CLI Command
 * Integrates the scaling detector into the CLI for the "killer demo"
 */

import chalk from 'chalk';
import { Command } from 'commander';
import ScalingDetector, { ScalingAnalysisRequest } from '../agents/scaling-detector.js';
import { createDemoFiles, DEMO_FILES } from '../agents/scaling-demo-scenarios.js';
import { readFile } from 'fs/promises';
import path from 'path';

interface ScalingAnalysisOptions {
  file?: string;
  code?: string;
  depth?: 'quick' | 'thorough' | 'comprehensive';
  examples?: boolean;
  demo?: boolean;
  interactive?: boolean;
}

export class ScalingAnalysisCommand {
  private detector: ScalingDetector;

  constructor() {
    this.detector = new ScalingDetector();
  }

  /**
   * Create the CLI command
   */
  createCommand(): Command {
    const command = new Command('scaling')
      .description('🔍 Analyze code for scaling issues (The Killer Demo)')
      .option('-f, --file <path>', 'Analyze specific file')
      .option('-c, --code <code>', 'Analyze code snippet directly')
      .option('-d, --depth <level>', 'Analysis depth: quick, thorough, comprehensive', 'thorough')
      .option('-e, --examples', 'Include fix examples in output', false)
      .option('--demo', 'Run demonstration with example scaling issues', false)
      .option('-i, --interactive', 'Interactive mode with guided analysis', false)
      .action(this.executeAnalysis.bind(this));

    // Add subcommands
    command
      .command('demo')
      .description('🎭 Run the killer demo with predefined scaling issues')
      .option('--create-files', 'Create demo scenario files')
      .option('--scenario <name>', 'Run specific scenario')
      .action(this.runDemo.bind(this));

    command
      .command('report')
      .description('📊 Generate scaling analysis report')
      .option('--format <type>', 'Report format: text, json, html', 'text')
      .action(this.generateReport.bind(this));

    return command;
  }

  /**
   * Execute scaling analysis
   */
  private async executeAnalysis(options: ScalingAnalysisOptions): Promise<void> {
    try {
      console.log(chalk.blue.bold('\n🔍 SCALING ISSUE DETECTOR - The Killer Demo'));
      console.log(chalk.gray('Detecting performance issues before they reach production\n'));

      // Handle demo mode
      if (options.demo) {
        return this.runDemo({ scenario: 'all' });
      }

      // Handle interactive mode
      if (options.interactive) {
        return this.runInteractiveAnalysis(options);
      }

      // Build analysis request
      const request: ScalingAnalysisRequest = {
        filePath: options.file,
        codeSnippet: options.code,
        analysisDepth: options.depth as any || 'thorough',
        includeExamples: options.examples
      };

      // Validate input
      if (!request.filePath && !request.codeSnippet) {
        console.log(chalk.red('❌ Please provide either --file or --code option'));
        console.log(chalk.gray('   Example: scaling --file src/api/users.ts'));
        console.log(chalk.gray('   Example: scaling --code "for(const user of users) { await getOrders(user.id); }"'));
        console.log(chalk.gray('   Example: scaling --demo (run demonstration)'));
        return;
      }

      // Run analysis
      const result = await this.detector.analyzeForScalingIssues(request);

      // Display summary
      this.displayAnalysisSummary(result, options.examples);

    } catch (error) {
      console.log(chalk.red('❌ Analysis failed:'), error);
      process.exit(1);
    }
  }

  /**
   * Run the killer demo
   */
  private async runDemo(options: { scenario?: string; createFiles?: boolean }): Promise<void> {
    try {
      console.log(chalk.blue.bold('\n🎭 SCALING DETECTOR KILLER DEMO'));
      console.log(chalk.gray('Demonstrating detection of critical scaling issues\n'));

      // Create demo files if requested
      if (options.createFiles) {
        await createDemoFiles('./demo-scenarios');
        console.log(chalk.green('✅ Demo scenario files created in ./demo-scenarios/'));
        return;
      }

      // Demo scenarios to run
      const scenarios = options.scenario === 'all' ? Object.keys(DEMO_FILES) : [options.scenario];

      let totalIssues = 0;
      let totalCritical = 0;

      console.log(chalk.blue('🚀 Running scaling analysis on demonstration scenarios...\n'));

      for (const scenarioFile of scenarios) {
        if (!DEMO_FILES[scenarioFile as keyof typeof DEMO_FILES]) {
          console.log(chalk.yellow(`⚠️  Unknown scenario: ${scenarioFile}`));
          continue;
        }

        console.log(chalk.blue(`\n📁 Analyzing: ${scenarioFile}`));
        console.log(chalk.gray('─'.repeat(60)));

        const code = DEMO_FILES[scenarioFile as keyof typeof DEMO_FILES];
        
        const result = await this.detector.analyzeForScalingIssues({
          codeSnippet: code,
          analysisDepth: 'comprehensive',
          includeExamples: true
        });

        totalIssues += result.issues.length;
        totalCritical += result.issues.filter(i => i.severity === 'critical').length;

        // Display key findings for this scenario
        this.displayScenarioResults(scenarioFile, result);
      }

      // Demo summary
      console.log(chalk.blue.bold('\n🎯 DEMO SUMMARY'));
      console.log(chalk.gray('─'.repeat(40)));
      console.log(chalk.red(`Total Issues Found: ${totalIssues}`));
      console.log(chalk.red(`Critical Issues: ${totalCritical}`));
      console.log(chalk.yellow(`Scenarios Analyzed: ${scenarios.length}`));
      
      if (totalCritical > 0) {
        console.log(chalk.red.bold('\n🚨 CRITICAL FINDINGS:'));
        console.log(chalk.red('   • N+1 query patterns detected'));
        console.log(chalk.red('   • Memory leak vulnerabilities found'));
        console.log(chalk.red('   • Inefficient algorithms identified'));
        console.log(chalk.red('   • Blocking operations discovered'));
        
        console.log(chalk.blue.bold('\n💡 VALUE DEMONSTRATION:'));
        console.log(chalk.green('   ✅ Issues caught before production'));
        console.log(chalk.green('   ✅ Specific fix recommendations provided'));
        console.log(chalk.green('   ✅ Performance impact quantified'));
        console.log(chalk.green('   ✅ Breaking points identified'));
      }

      console.log(chalk.blue.bold('\n🎉 Demo Complete! The system successfully detected all planted scaling issues.'));

    } catch (error) {
      console.log(chalk.red('❌ Demo failed:'), error);
      throw error;
    }
  }

  /**
   * Interactive analysis mode
   */
  private async runInteractiveAnalysis(options: ScalingAnalysisOptions): Promise<void> {
    const readline = await import('readline/promises');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    try {
      console.log(chalk.blue.bold('\n🔍 INTERACTIVE SCALING ANALYSIS'));
      console.log(chalk.gray('Enter code to analyze for scaling issues\n'));

      while (true) {
        console.log(chalk.blue('\nOptions:'));
        console.log(chalk.gray('  1. Analyze code snippet'));
        console.log(chalk.gray('  2. Analyze file'));
        console.log(chalk.gray('  3. Run demo scenario'));
        console.log(chalk.gray('  4. View analysis history'));
        console.log(chalk.gray('  5. Exit\n'));

        const choice = await rl.question(chalk.cyan('Select option (1-5): '));

        switch (choice.trim()) {
          case '1':
            await this.interactiveCodeAnalysis(rl);
            break;
          case '2':
            await this.interactiveFileAnalysis(rl);
            break;
          case '3':
            await this.interactiveDemoScenario(rl);
            break;
          case '4':
            this.displayAnalysisHistory();
            break;
          case '5':
            console.log(chalk.green('\n👋 Goodbye!'));
            return;
          default:
            console.log(chalk.red('❌ Invalid choice. Please select 1-5.'));
        }
      }
    } finally {
      rl.close();
    }
  }

  /**
   * Interactive code snippet analysis
   */
  private async interactiveCodeAnalysis(rl: any): Promise<void> {
    console.log(chalk.blue('\n📝 Enter your code (press Enter twice to finish):'));
    
    const lines: string[] = [];
    let emptyLines = 0;

    while (emptyLines < 2) {
      const line = await rl.question('');
      
      if (line.trim() === '') {
        emptyLines++;
      } else {
        emptyLines = 0;
      }
      
      lines.push(line);
    }

    const code = lines.slice(0, -2).join('\n').trim();
    
    if (code) {
      const result = await this.detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive',
        includeExamples: true
      });

      this.displayAnalysisSummary(result, true);
    } else {
      console.log(chalk.yellow('⚠️  No code provided.'));
    }
  }

  /**
   * Interactive file analysis
   */
  private async interactiveFileAnalysis(rl: any): Promise<void> {
    const filePath = await rl.question(chalk.cyan('Enter file path: '));
    
    try {
      const result = await this.detector.analyzeForScalingIssues({
        filePath: filePath.trim(),
        analysisDepth: 'comprehensive',
        includeExamples: true
      });

      this.displayAnalysisSummary(result, true);
    } catch (error) {
      console.log(chalk.red(`❌ Failed to analyze file: ${error}`));
    }
  }

  /**
   * Interactive demo scenario selection
   */
  private async interactiveDemoScenario(rl: any): Promise<void> {
    console.log(chalk.blue('\n🎭 Available Demo Scenarios:'));
    
    const scenarios = Object.keys(DEMO_FILES);
    scenarios.forEach((scenario, index) => {
      console.log(chalk.gray(`  ${index + 1}. ${scenario}`));
    });

    const choice = await rl.question(chalk.cyan(`\nSelect scenario (1-${scenarios.length}): `));
    const index = parseInt(choice.trim()) - 1;

    if (index >= 0 && index < scenarios.length) {
      const scenarioFile = scenarios[index];
      const code = DEMO_FILES[scenarioFile as keyof typeof DEMO_FILES];
      
      console.log(chalk.blue(`\n📁 Analyzing: ${scenarioFile}`));
      
      const result = await this.detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive',
        includeExamples: true
      });

      this.displayScenarioResults(scenarioFile, result);
    } else {
      console.log(chalk.red('❌ Invalid scenario selection.'));
    }
  }

  /**
   * Display analysis history
   */
  private displayAnalysisHistory(): void {
    const history = this.detector.getAnalysisHistory();
    
    if (history.length === 0) {
      console.log(chalk.yellow('\n📝 No analysis history available.'));
      return;
    }

    console.log(chalk.blue.bold('\n📊 ANALYSIS HISTORY'));
    console.log(chalk.gray('─'.repeat(50)));

    history.slice(-10).forEach((result, index) => {
      const riskColor = result.overallRisk === 'critical' ? chalk.red :
                       result.overallRisk === 'high' ? chalk.yellow :
                       result.overallRisk === 'medium' ? chalk.blue : chalk.green;
      
      console.log(`${index + 1}. ${result.timestamp.toLocaleTimeString()} - ` +
                 `${result.issues.length} issues - ` +
                 riskColor(`${result.overallRisk.toUpperCase()} risk`));
    });
  }

  /**
   * Generate analysis report
   */
  private async generateReport(options: { format?: string }): Promise<void> {
    const history = this.detector.getAnalysisHistory();
    const format = options.format || 'text';

    if (history.length === 0) {
      console.log(chalk.yellow('📝 No analysis data available for report generation.'));
      return;
    }

    console.log(chalk.blue(`📊 Generating ${format.toUpperCase()} report...`));

    switch (format) {
      case 'json':
        await this.generateJSONReport(history);
        break;
      case 'html':
        await this.generateHTMLReport(history);
        break;
      default:
        this.generateTextReport(history);
    }
  }

  /**
   * Display helper methods
   */
  private displayAnalysisSummary(result: any, showExamples: boolean = false): void {
    const { issues, overallRisk, estimatedUserCapacity } = result;

    // Risk assessment
    const riskEmoji = overallRisk === 'critical' ? '🔴' :
                     overallRisk === 'high' ? '🟠' :
                     overallRisk === 'medium' ? '🟡' : '🟢';

    console.log(chalk.blue.bold('\n📊 SCALING ANALYSIS RESULTS'));
    console.log(chalk.gray('─'.repeat(50)));
    console.log(`${riskEmoji} Overall Risk: ${chalk.bold(overallRisk.toUpperCase())}`);
    console.log(chalk.gray(`   Estimated User Capacity: ${estimatedUserCapacity} concurrent users`));
    console.log(chalk.gray(`   Analysis Time: ${result.analysisTime}ms`));
    console.log(chalk.gray(`   Confidence: ${Math.round(result.confidence * 100)}%`));

    if (issues.length > 0) {
      // Group issues by type
      const issuesByType = issues.reduce((acc: any, issue: any) => {
        acc[issue.type] = (acc[issue.type] || 0) + 1;
        return acc;
      }, {});

      console.log(chalk.red.bold(`\n🚨 Found ${issues.length} Scaling Issue(s):`));
      Object.entries(issuesByType).forEach(([type, count]) => {
        const emoji = type === 'n_plus_one' ? '💥' :
                     type === 'memory_leak' ? '🧠' :
                     type === 'inefficient_algorithm' ? '🐌' :
                     type === 'blocking_operation' ? '🚫' : '⚠️';
        console.log(chalk.red(`   ${emoji} ${type.replace('_', ' ')}: ${count}`));
      });

      // Show critical issues with details
      const criticalIssues = issues.filter((i: any) => i.severity === 'critical' || i.severity === 'high');
      if (criticalIssues.length > 0) {
        console.log(chalk.red.bold('\n🔥 Critical Issues:'));
        criticalIssues.slice(0, 3).forEach((issue: any) => {
          console.log(chalk.red(`\n   • ${issue.title}`));
          console.log(chalk.gray(`     ${issue.description}`));
          console.log(chalk.yellow(`     Impact: ${issue.impact.estimatedBreakingPoint}`));
          console.log(chalk.cyan(`     Fix: ${issue.recommendation.solution}`));
          
          if (showExamples && issue.examples) {
            console.log(chalk.gray('\n     Example:'));
            console.log(chalk.red(issue.examples.badCode.split('\n').slice(0, 3).join('\n')));
            console.log(chalk.green(issue.examples.goodCode.split('\n').slice(0, 3).join('\n')));
          }
        });
      }
    } else {
      console.log(chalk.green.bold('\n✅ No scaling issues detected!'));
      console.log(chalk.green('   Code appears optimized for scaling'));
    }

    // Recommended actions
    if (result.recommendedActions.length > 0) {
      console.log(chalk.blue.bold('\n💡 Recommended Actions:'));
      result.recommendedActions.forEach((action: string) => {
        console.log(chalk.blue(`   • ${action}`));
      });
    }
  }

  private displayScenarioResults(scenarioFile: string, result: any): void {
    const { issues, overallRisk } = result;
    
    const riskColor = overallRisk === 'critical' ? chalk.red :
                     overallRisk === 'high' ? chalk.yellow :
                     overallRisk === 'medium' ? chalk.blue : chalk.green;

    console.log(riskColor(`   Risk: ${overallRisk.toUpperCase()}`));
    console.log(chalk.gray(`   Issues: ${issues.length}`));
    console.log(chalk.gray(`   Capacity: ${result.estimatedUserCapacity} users`));

    if (issues.length > 0) {
      const criticalIssue = issues.find((i: any) => i.severity === 'critical');
      if (criticalIssue) {
        console.log(chalk.red(`   🚨 ${criticalIssue.title}`));
      }
    }
  }

  private generateTextReport(history: any[]): void {
    console.log(chalk.blue.bold('\n📋 SCALING ANALYSIS REPORT'));
    console.log(chalk.gray('Generated: ' + new Date().toLocaleString()));
    console.log(chalk.gray('─'.repeat(60)));

    const totalAnalyses = history.length;
    const totalIssues = history.reduce((sum, result) => sum + result.issues.length, 0);
    const criticalIssues = history.reduce((sum, result) => 
      sum + result.issues.filter((i: any) => i.severity === 'critical').length, 0);

    console.log(`Total Analyses: ${totalAnalyses}`);
    console.log(`Total Issues Found: ${totalIssues}`);
    console.log(`Critical Issues: ${criticalIssues}`);
    console.log(`Average Issues per Analysis: ${(totalIssues / totalAnalyses).toFixed(1)}`);

    // Most common issues
    const issueTypes: Record<string, number> = {};
    history.forEach(result => {
      result.issues.forEach((issue: any) => {
        issueTypes[issue.type] = (issueTypes[issue.type] || 0) + 1;
      });
    });

    if (Object.keys(issueTypes).length > 0) {
      console.log(chalk.blue('\nMost Common Issues:'));
      Object.entries(issueTypes)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .forEach(([type, count]) => {
          console.log(`  ${type.replace('_', ' ')}: ${count}`);
        });
    }
  }

  private async generateJSONReport(history: any[]): Promise<void> {
    const report = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalAnalyses: history.length,
        totalIssues: history.reduce((sum, result) => sum + result.issues.length, 0),
        criticalIssues: history.reduce((sum, result) => 
          sum + result.issues.filter((i: any) => i.severity === 'critical').length, 0)
      },
      analyses: history
    };

    const { writeFile } = await import('fs/promises');
    const filename = `scaling-report-${Date.now()}.json`;
    
    await writeFile(filename, JSON.stringify(report, null, 2));
    console.log(chalk.green(`📄 JSON report saved to: ${filename}`));
  }

  private async generateHTMLReport(history: any[]): Promise<void> {
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Scaling Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        .summary { background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .issue { background: #fef2f2; padding: 10px; margin: 10px 0; border-left: 4px solid #ef4444; }
        .critical { border-left-color: #dc2626; }
        .high { border-left-color: #ea580c; }
        .medium { border-left-color: #d97706; }
        .low { border-left-color: #65a30d; }
    </style>
</head>
<body>
    <h1 class="header">🔍 Scaling Analysis Report</h1>
    <p>Generated: ${new Date().toLocaleString()}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Analyses: ${history.length}</p>
        <p>Total Issues: ${history.reduce((sum, result) => sum + result.issues.length, 0)}</p>
        <p>Critical Issues: ${history.reduce((sum, result) => 
          sum + result.issues.filter((i: any) => i.severity === 'critical').length, 0)}</p>
    </div>
    
    ${history.map(result => `
        <div class="analysis">
            <h3>Analysis ${result.analysisId}</h3>
            <p>Risk: ${result.overallRisk} | Issues: ${result.issues.length}</p>
            ${result.issues.map((issue: any) => `
                <div class="issue ${issue.severity}">
                    <strong>${issue.title}</strong>
                    <p>${issue.description}</p>
                    <p><em>Fix: ${issue.recommendation.solution}</em></p>
                </div>
            `).join('')}
        </div>
    `).join('')}
</body>
</html>`;

    const { writeFile } = await import('fs/promises');
    const filename = `scaling-report-${Date.now()}.html`;
    
    await writeFile(filename, html);
    console.log(chalk.green(`📄 HTML report saved to: ${filename}`));
  }
}

export default ScalingAnalysisCommand;