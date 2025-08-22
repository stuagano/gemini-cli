import {
  CommandContext,
  CommandKind,
  MessageActionReturn,
  SlashCommand,
} from './types.js';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { marked } from 'marked';
import puppeteer from 'puppeteer';
import { SwarmDocumentationService, DocumentationRequirements } from '../../services/SwarmDocumentationService.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Helper function to parse requirements from user input or interactive prompts
 */
async function gatherRequirements(args: string, context: CommandContext): Promise<DocumentationRequirements> {
  // Parse command line arguments for requirements
  const argParts = args.trim().split(/\s+/);
  const projectName = argParts[0] || 'Enterprise Project';
  
  // Default requirements - in a real implementation, this could be interactive
  const requirements: DocumentationRequirements = {
    projectName,
    projectType: 'enterprise',
    businessDomain: 'Technology',
    technicalScope: 'full-stack',
    securityLevel: 'high',
    complianceRequirements: ['SOC 2', 'GDPR'],
    stakeholders: {
      business: ['Product Owner', 'Business Analyst'],
      technical: ['Solution Architect', 'Lead Developer'],
      external: ['Security Auditor', 'Compliance Officer']
    },
    timeline: {
      duration: '12 weeks',
      phases: [
        { name: 'Requirements Analysis', duration: '2 weeks' },
        { name: 'Architecture Design', duration: '3 weeks' },
        { name: 'Implementation', duration: '6 weeks' },
        { name: 'Testing & Deployment', duration: '1 week' }
      ]
    }
  };

  return requirements;
}

export const reviewBoardCommand: SlashCommand = {
  name: 'review-board',
  description: 'Generate and validate review board documentation using AI-powered swarm collaboration',
  kind: CommandKind.BUILT_IN,
  subCommands: [
    {
      name: 'generate',
      description: 'Generate review board documentation using basic template',
      kind: CommandKind.BUILT_IN,
      action: async (
        context: CommandContext,
        args: string
      ): Promise<MessageActionReturn | void> => {
        if (!context.services.config) {
          return {
            type: 'message',
            messageType: 'error',
            content: 'Configuration not available.',
          };
        }
        const templatePath = path.resolve(
          __dirname,
          '..',
          '..',
          'templates',
          'review-board-template.md'
        );
        const outputPath = path.join(
          process.cwd(),
          'review-board-documentation.md'
        );

        try {
          const templateContent = fs.readFileSync(templatePath, 'utf8');
          fs.writeFileSync(outputPath, templateContent, 'utf8');
          return {
            type: 'message',
            messageType: 'info',
            content: `Successfully generated review-board-documentation.md`,
          };
        } catch (error) {
          return {
            type: 'message',
            messageType: 'error',
            content: `Error generating review board documentation: ${error}`,
          };
        }
      },
    },
    {
      name: 'swarm-generate',
      description: 'Generate comprehensive review board documentation using AI swarm collaboration',
      kind: CommandKind.BUILT_IN,
      action: async (
        context: CommandContext,
        args: string
      ): Promise<MessageActionReturn | void> => {
        if (!context.services.config) {
          return {
            type: 'message',
            messageType: 'error',
            content: 'Configuration not available.',
          };
        }

        try {
          // Set pending message to show progress
          context.ui.setPendingItem({
            type: 'info',
            text: '🤖 Initializing AI swarm for documentation generation...'
          });

          // Gather requirements
          const requirements = await gatherRequirements(args, context);
          
          // Initialize swarm documentation service
          const swarmService = new SwarmDocumentationService(
            context.services.config,
            process.cwd()
          );

          // Update progress
          context.ui.setPendingItem({
            type: 'info',
            text: `🔄 Generating documentation for "${requirements.projectName}" using specialized AI agents...`
          });

          // Generate documentation using swarm
          const result = await swarmService.generateReviewBoardDocumentation(
            requirements,
            {
              useSwarm: true,
              validationLevel: 'comprehensive'
            }
          );

          // Clear pending message
          context.ui.setPendingItem(null);

          const agentsUsed = result.metadata.agentsUsed.join(', ');
          const generationTimeMs = result.metadata.generationTime;
          const sectionsCount = result.sections.length;
          const validationIssues = result.validationResults.reduce((sum, r) => sum + r.issues.length, 0);

          return {
            type: 'message',
            messageType: 'info',
            content: `✅ AI Swarm Documentation Generated Successfully!

📄 **Document:** ${result.documentPath}
🤖 **Agents Used:** ${agentsUsed}
📊 **Sections Generated:** ${sectionsCount}
⏱️ **Generation Time:** ${(generationTimeMs / 1000).toFixed(1)}s
${result.metadata.swarmSessionId ? `🔗 **Swarm Session:** ${result.metadata.swarmSessionId}` : ''}
${validationIssues > 0 ? `⚠️ **Validation Issues:** ${validationIssues} items need review` : '✅ **Validation:** All sections validated successfully'}

The comprehensive review board documentation has been generated using specialized AI agents for business analysis, architecture design, security assessment, and operational planning.`,
          };

        } catch (error) {
          context.ui.setPendingItem(null);
          return {
            type: 'message',
            messageType: 'error',
            content: `Error generating swarm documentation: ${error instanceof Error ? error.message : String(error)}`,
          };
        }
      },
    },
    {
      name: 'validate',
      description: 'Validate review board documentation using basic checks',
      kind: CommandKind.BUILT_IN,
      action: async (
        context: CommandContext
      ): Promise<MessageActionReturn | void> => {
        const outputPath = path.join(
          process.cwd(),
          'review-board-documentation.md'
        );

        try {
          const content = fs.readFileSync(outputPath, 'utf8');
          if (content.includes('...')) {
            return {
              type: 'message',
              messageType: 'error',
              content: `The documentation is not complete. Please fill out all sections.`,
            };
          }
          return {
            type: 'message',
            messageType: 'info',
            content: `The documentation is valid.`,
          };
        } catch (error) {
          return {
            type: 'message',
            messageType: 'error',
            content: `Error validating review board documentation: ${error}`,
          };
        }
      },
    },
    {
      name: 'ai-validate',
      description: 'Perform comprehensive AI-powered validation of review board documentation',
      kind: CommandKind.BUILT_IN,
      action: async (
        context: CommandContext,
        args: string
      ): Promise<MessageActionReturn | void> => {
        if (!context.services.config) {
          return {
            type: 'message',
            messageType: 'error',
            content: 'Configuration not available.',
          };
        }

        const outputPath = path.join(
          process.cwd(),
          'review-board-documentation.md'
        );

        try {
          if (!fs.existsSync(outputPath)) {
            return {
              type: 'message',
              messageType: 'error',
              content: `Review board documentation not found at ${outputPath}. Generate it first using /review-board swarm-generate.`,
            };
          }

          context.ui.setPendingItem({
            type: 'info',
            text: '🔍 Performing AI-powered validation analysis...'
          });

          const swarmService = new SwarmDocumentationService(
            context.services.config,
            process.cwd()
          );

          // Parse the existing document to extract sections
          const content = fs.readFileSync(outputPath, 'utf8');
          const sections = [
            {
              title: 'Full Document',
              content,
              agent: 'validator',
              confidence: 1.0,
              validationStatus: 'pending' as const,
              metadata: {
                generatedAt: new Date(),
                templateVersion: '2.0.0',
                agentVersion: '1.0.0'
              }
            }
          ];

          // Create mock requirements for validation
          const requirements = await gatherRequirements(args, context);
          
          // Run validation
          const validationTasks = [
            {
              agentPersona: 'guardian',
              taskType: 'content-validation',
              description: 'Comprehensive document validation',
              input: { sections, requirements },
              expectedOutput: 'Detailed validation report',
              dependencies: [],
              priority: 'high' as const,
              estimatedDuration: '2 minutes'
            }
          ];

          const validationResults = await swarmService['executeValidation'](validationTasks);
          
          context.ui.setPendingItem(null);

          // Format validation results
          let resultMessage = '🔍 **AI Validation Report**\n\n';
          
          let totalIssues = 0;
          let criticalIssues = 0;
          
          validationResults.forEach(result => {
            resultMessage += `**${result.section}**\n`;
            resultMessage += `- Status: ${result.isValid ? '✅ Valid' : '❌ Issues Found'}\n`;
            resultMessage += `- Confidence: ${(result.confidence * 100).toFixed(1)}%\n`;
            
            if (result.issues.length > 0) {
              resultMessage += `- Issues (${result.issues.length}):\n`;
              result.issues.forEach(issue => {
                totalIssues++;
                if (issue.severity === 'critical' || issue.severity === 'error') {
                  criticalIssues++;
                }
                resultMessage += `  • ${issue.message} (${issue.severity})\n`;
                if (issue.suggestions.length > 0) {
                  resultMessage += `    Suggestion: ${issue.suggestions[0]}\n`;
                }
              });
            }
            
            if (result.improvements.length > 0) {
              resultMessage += `- Improvements:\n`;
              result.improvements.forEach(improvement => {
                resultMessage += `  • ${improvement}\n`;
              });
            }
            
            resultMessage += '\n';
          });

          resultMessage += `**Summary:** ${totalIssues} total issues found`;
          if (criticalIssues > 0) {
            resultMessage += ` (${criticalIssues} critical)`;
          }

          return {
            type: 'message',
            messageType: criticalIssues > 0 ? 'error' : 'info',
            content: resultMessage,
          };

        } catch (error) {
          context.ui.setPendingItem(null);
          return {
            type: 'message',
            messageType: 'error',
            content: `Error during AI validation: ${error instanceof Error ? error.message : String(error)}`,
          };
        }
      },
    },
    {
      name: 'export',
      description: 'Export review board documentation to PDF',
      kind: CommandKind.BUILT_IN,
      action: async (
        context: CommandContext
      ): Promise<MessageActionReturn | void> => {
        const outputPath = path.join(
          process.cwd(),
          'review-board-documentation.md'
        );
        const pdfPath = path.join(
          process.cwd(),
          'review-board-documentation.pdf'
        );

        try {
          const markdown = fs.readFileSync(outputPath, 'utf8');
          const html = await marked(markdown);
          const browser = await puppeteer.launch();
          const page = await browser.newPage();
          await page.setContent(html);
          await page.pdf({ path: pdfPath, format: 'A4' });
          await browser.close();
          return {
            type: 'message',
            messageType: 'info',
            content: `Successfully exported to review-board-documentation.pdf`,
          };
        } catch (error) {
          return {
            type: 'message',
            messageType: 'error',
            content: `Error exporting review board documentation: ${error}`,
          };
        }
      },
    },
  ],
};
