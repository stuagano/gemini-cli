/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CommandKind, SlashCommand, CommandContext } from './types.js';

/**
 * Utility function to handle enterprise agent requests
 * This is a simplified version that will submit the request as a regular prompt
 * with agent context for now, until the full agent system is integrated
 */
async function handleAgentRequest(
  context: CommandContext,
  agentType: string,
  args: string,
  description: string
) {
  if (!args.trim()) {
    return {
      type: 'message' as const,
      messageType: 'error' as const,
      content: `Please provide a request for the ${agentType} agent. Example: /${agentType} ${description}`
    };
  }

  // For now, we'll format the request as a special prompt that the backend can recognize
  const agentPrompt = `[ENTERPRISE_AGENT:${agentType.toUpperCase()}] ${args.trim()}

This request should be handled by the ${agentType} agent with specialized business context and expertise.`;

  return {
    type: 'submit_prompt' as const,
    content: agentPrompt
  };
}

// Business Analysis Agent
export const analystCommand: SlashCommand = {
  name: 'analyst',
  description: 'Business analysis, technical debt assessment, and metrics',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'analyst',
      args,
      'analyze technical debt in this codebase'
    );
  }
};

// Product Manager Agent
export const pmCommand: SlashCommand = {
  name: 'pm',
  description: 'Project management, roadmaps, and sprint planning',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'pm',
      args,
      'create a project roadmap for this feature'
    );
  }
};

// Principal Architect Agent
export const architectCommand: SlashCommand = {
  name: 'architect',
  altNames: ['arch'],
  description: 'System design, architecture guidance, and technical strategy',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'architect',
      args,
      'design a microservices architecture'
    );
  }
};

// Developer Agent
export const developerCommand: SlashCommand = {
  name: 'developer',
  altNames: ['dev'],
  description: 'Code implementation, best practices, and development guidance',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'developer',
      args,
      'implement this feature with best practices'
    );
  }
};

// QA Agent
export const qaCommand: SlashCommand = {
  name: 'qa',
  altNames: ['test'],
  description: 'Testing strategies, quality assurance, and test automation',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'qa',
      args,
      'create comprehensive tests for this code'
    );
  }
};

// Scout Agent (Duplicate Detection)
export const scoutCommand: SlashCommand = {
  name: 'scout',
  description: 'Duplicate detection, code analysis, and DRY enforcement',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'scout',
      args,
      'check for duplicates before implementing this'
    );
  }
};

// Product Owner Agent
export const poCommand: SlashCommand = {
  name: 'po',
  altNames: ['product'],
  description: 'Product optimization, value analysis, and user experience',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'po',
      args,
      'optimize this feature for business value'
    );
  }
};

// Guardian Security Validation
export const guardianCommand: SlashCommand = {
  name: 'guardian',
  altNames: ['security'],
  description: 'Security validation, compliance checks, and code standards',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'guardian',
      args,
      'validate this code meets security standards'
    );
  }
};

// Killer Demo (Performance Analysis)
export const killerDemoCommand: SlashCommand = {
  name: 'killer-demo',
  altNames: ['performance', 'scaling'],
  description: 'Performance analysis, scaling issues, and optimization detection',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'killer-demo',
      args,
      'find scaling issues and performance bottlenecks'
    );
  }
};

// Knowledge Base Search
export const knowledgeCommand: SlashCommand = {
  name: 'knowledge',
  altNames: ['docs', 'search'],
  description: 'Search documentation, best practices, and knowledge base',
  kind: CommandKind.BUILT_IN,
  action: async (context, args) => {
    return await handleAgentRequest(
      context,
      'knowledge',
      args,
      'search our documentation for best practices'
    );
  }
};

// Agent Status Command
export const agentStatusCommand: SlashCommand = {
  name: 'agents',
  description: 'Check enterprise agent status and available commands',
  kind: CommandKind.BUILT_IN,
  action: async (context, _args) => {
    const statusMessage = `🤖 **Enterprise Agents Available**

**Business & Strategy:**
• \`/analyst\` - Business analysis, technical debt assessment, and metrics
• \`/pm\` - Project management, roadmaps, and sprint planning  
• \`/po\` - Product optimization, value analysis, and user experience

**Technical & Architecture:**
• \`/architect\` - System design, architecture guidance, and technical strategy
• \`/developer\` - Code implementation, best practices, and development guidance
• \`/qa\` - Testing strategies, quality assurance, and test automation

**Code Quality & Security:**
• \`/scout\` - Duplicate detection, code analysis, and DRY enforcement
• \`/guardian\` - Security validation, compliance checks, and code standards
• \`/killer-demo\` - Performance analysis, scaling issues, and optimization detection

**Knowledge & Documentation:**
• \`/knowledge\` - Search documentation, best practices, and knowledge base

**Usage Examples:**
\`\`\`
/architect design a microservices API for user authentication
/scout check for duplicate authentication code
/analyst assess technical debt in our React components
/qa create comprehensive tests for this payment service
\`\`\`

**Backend Status:** 
To enable full enterprise features, ensure your agent server is running:
\`python src/api/agent_server.py\`

Your environment is configured and ready! 🎯`;

    return {
      type: 'message' as const,
      messageType: 'info' as const,
      content: statusMessage
    };
  }
};

// Export all enterprise commands
export const enterpriseCommands: SlashCommand[] = [
  analystCommand,
  pmCommand,
  architectCommand,
  developerCommand,
  qaCommand,
  scoutCommand,
  poCommand,
  guardianCommand,
  killerDemoCommand,
  knowledgeCommand,
  agentStatusCommand
];