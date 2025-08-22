# Source Tree Documentation

## Project Structure Overview
This document describes the complete source code organization and the purpose of each directory and important file for the Gemini Enterprise Architect VS Code Extension project.

## Directory Structure
```
gemini-cli/
├── docs/                           # Project documentation
│   ├── architecture/               # Architecture documentation
│   │   ├── README.md              # High-level system design
│   │   ├── bmad-enterprise-architecture.md  # BMAD methodology architecture
│   │   ├── bmad-gemini-integration-specs.md # Integration specifications
│   │   ├── epics_and_stories.md   # Epics and stories breakdown
│   │   ├── gemini-enterprise-architect-technical.md # Technical architecture
│   │   ├── overview.md            # System overview
│   │   └── source-tree.md         # Source tree documentation
│   ├── briefs/                    # Project briefs and summaries
│   │   ├── bmad-overview.md       # BMAD methodology overview
│   │   ├── bmad-success-metrics.md # Success metrics and KPIs
│   │   ├── bmad-value-streams.md  # Value stream mapping
│   │   └── gemini-enterprise-architect.md # Project brief
│   ├── manuals/                   # User and developer guides
│   │   ├── api-documentation.md   # API documentation
│   │   ├── bmad-implementation-guide.md # BMAD implementation guide
│   │   ├── bmad-operations.md     # Operations guide
│   │   └── implementation-status.md # Implementation status
│   ├── stories/                   # User stories
│   │   └── 001-user-login.md      # User login story
│   ├── business-case.md           # Business case and ROI analysis
│   ├── cloud-usage-estimates.md   # Cloud resource usage estimates
│   └── pricing-validation-report.md # Real-time pricing validation
├── vscode-extension/              # VS Code Extension source code
│   ├── src/                       # Extension source code
│   │   ├── providers/             # Tree data providers and view providers
│   │   │   ├── BMADStatusProvider.ts     # BMAD documentation status
│   │   │   ├── EpicsProvider.ts          # Epics and stories tree view
│   │   │   ├── IssuesProvider.ts         # Issues and project management
│   │   │   ├── PersonasProvider.ts       # AI personas tree view
│   │   │   └── CloudPricingProvider.ts   # Cloud pricing insights
│   │   ├── services/              # Business logic and services
│   │   │   ├── BMADValidator.ts          # BMAD documentation validator
│   │   │   ├── GeminiClient.ts           # Gemini API client
│   │   │   └── CloudPricingService.ts    # Cloud pricing integration
│   │   ├── utils/                 # Utility functions and helpers
│   │   │   ├── logger.ts                 # Logging utilities
│   │   │   └── constants.ts              # Application constants
│   │   ├── webviews/              # WebView panels and content
│   │   │   ├── BMADStatusWebview.ts      # BMAD status detailed view
│   │   │   └── CloudPricingWebview.ts    # Cloud pricing dashboard
│   │   ├── extension.ts           # Main extension entry point
│   │   └── types.ts               # TypeScript type definitions
│   ├── package.json               # Extension manifest and dependencies
│   ├── tsconfig.json              # TypeScript configuration
│   └── README.md                  # Extension documentation
├── packages/cli/                  # Gemini CLI package source
│   ├── src/                       # CLI source code
│   │   ├── commands/              # CLI command implementations
│   │   │   ├── mcp.test.ts        # MCP command tests
│   │   │   └── mcp/               # MCP subcommands
│   │   ├── config/                # Configuration management
│   │   │   ├── config.ts          # Main configuration
│   │   │   ├── extension.test.ts  # Extension configuration tests
│   │   │   └── settings.test.ts   # Settings management tests
│   │   ├── services/              # CLI services
│   │   │   ├── BuiltinCommandLoader.ts  # Built-in command loader
│   │   │   └── FileCommandLoader.test.ts # File command loader tests
│   │   ├── ui/                    # User interface components
│   │   │   ├── App.tsx            # Main application component
│   │   │   ├── App.test.tsx       # Application tests
│   │   │   ├── commands/          # UI command implementations
│   │   │   ├── components/        # Reusable UI components
│   │   │   └── hooks/             # React hooks and utilities
│   │   ├── utils/                 # CLI utilities
│   │   │   ├── cleanup.test.ts    # Cleanup utilities tests
│   │   │   ├── handleAutoUpdate.test.ts # Auto-update handling tests
│   │   │   └── startupWarnings.test.ts  # Startup warnings tests
│   │   ├── gemini.tsx             # Gemini integration
│   │   └── nonInteractiveCli.test.ts # Non-interactive CLI tests
│   ├── package.json               # CLI package configuration
│   └── tsconfig.json              # TypeScript configuration for CLI
├── .github/                       # GitHub configuration
│   └── workflows/                 # GitHub Actions workflows
│       └── ci.yml                 # Continuous integration pipeline
├── epic_implementation_tasks.md   # Epic implementation tasks
├── PRD.md                         # Product Requirements Document
├── README.md                      # Project overview and setup
├── package.json                   # Root package configuration
└── package-lock.json             # Dependency lock file
```

## Key Directories and Files

### `/docs` - Documentation
**Purpose:** Contains all project documentation including architecture, API specs, business case, and guides.

- **`architecture/`** - System design documents and architectural decisions
- **`briefs/`** - Project briefs, BMAD methodology, and value propositions
- **`manuals/`** - Implementation guides, API documentation, and operations manuals
- **`stories/`** - User stories and acceptance criteria
- **`business-case.md`** - Complete business justification with ROI analysis
- **`cloud-usage-estimates.md`** - Detailed cloud resource planning and cost optimization
- **`pricing-validation-report.md`** - Real-time cloud pricing validation and forecasting

### `/vscode-extension` - VS Code Extension
**Purpose:** Complete VS Code extension implementation with AI-powered development tools.

- **`src/providers/`** - Tree data providers for BMAD status, personas, epics, and cloud pricing
- **`src/services/`** - Core business logic including BMAD validation and Gemini integration
- **`src/utils/`** - Utility functions for logging, constants, and helper methods
- **`src/webviews/`** - WebView panels for detailed status views and dashboards
- **`extension.ts`** - Main extension entry point and activation logic

### `/packages/cli` - Gemini CLI Package
**Purpose:** Core Gemini CLI functionality with command processing and UI components.

- **`src/commands/`** - CLI command implementations and tests
- **`src/config/`** - Configuration management and settings
- **`src/ui/`** - React-based user interface components
- **`src/utils/`** - CLI-specific utility functions and helpers

### Root Files
- **`epic_implementation_tasks.md`** - Epic-level task breakdown for implementation
- **`PRD.md`** - Product Requirements Document with goals and acceptance criteria
- **`README.md`** - Project overview, setup instructions, and developer guide

## File Naming Conventions

### Documentation Files
- Use kebab-case: `system-overview.md`
- Include version in filename if needed: `api-spec-v2.md`
- Use descriptive names: `user-authentication-flow.md`

### Source Code Files  
- Components: PascalCase `UserProfile.tsx`
- Services: camelCase `userService.ts`
- Utilities: camelCase `dateUtils.ts`
- Types: PascalCase `UserTypes.ts`

### Task Files
- Epics: `epic-user-management.md`
- Stories: `story-user-login.md`
- Use descriptive names that reflect the feature

## Code Organization Principles

### Separation of Concerns
- UI components only handle presentation
- Services handle business logic and data
- Utilities provide pure functions
- Types define clear interfaces

### Dependency Direction
- Components depend on services
- Services depend on utilities
- No circular dependencies allowed
- External dependencies isolated in service layer

### Testing Strategy
- Unit tests co-located with source files
- Integration tests in dedicated test directories
- End-to-end tests in separate test suite
- Mock external dependencies

## Navigation Guide

### For New Developers
1. Start with `README.md` for project overview
2. Review `docs/architecture/system-overview.md` for system understanding
3. Check `tasks/` directory for current development priorities
4. Explore `src/` directory for code organization

### For Project Managers
1. Review `tasks/` directory for epic and story status
2. Check `docs/` for current documentation status
3. Use `PRD.md` for requirements tracking

### For Architects
1. Focus on `docs/architecture/` directory
2. Review `src/` organization for implementation alignment
3. Check `config/` for system configuration

---
*Last Updated: 2025-08-20*  
*Maintained by: Development Team*
