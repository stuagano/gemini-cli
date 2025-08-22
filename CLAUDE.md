# CLAUDE.md - Project Memory and Instructions

## Documentation Practices - BMAD Method

When working with documentation in this project, follow these critical guidelines:

### Update, Don't Create
- **ALWAYS** check for existing documentation before creating new files
- **PREFER** updating existing documentation files over creating new ones
- **FOLLOW** the BMAD (Business Model Agent Development) method structure
- **NEVER** create new documentation files unless explicitly requested by the user

### Documentation Structure
- All documentation should be maintained under the appropriate folder structure:
  - `.bmad-core/` - Core BMAD method files and agent definitions
  - `.gemini/bmad-method/` - Gemini-specific BMAD configurations
  - `.claude/` - Claude-specific configurations
  - `docs/` - General project documentation
  - Architecture docs: `docs/architecture/`
  - API docs: `src/api/README.md`
  - Knowledge base: `src/knowledge/README.md`
  - BMAD docs: `docs/bmad-*.md`

### Before Creating Documentation
1. Search for existing related documentation files
2. Check if the content fits within an existing document
3. Consider if the documentation belongs in an existing category
4. Only create new files when absolutely necessary and no existing file is appropriate

### When Updating Documentation
1. Maintain consistency with existing formatting and structure
2. Preserve the original document's purpose and scope
3. Add new sections rather than rewriting existing content unless explicitly requested
4. Keep documentation organized by topic and maintainable

## Progress Tracking and Reporting

### BMAD Progress Updates
When working on BMAD-related tasks, always update the following files:
- `docs/implementation-status.md` - Overall implementation progress
- `docs/bmad-operations-guide.md` - Operational procedures and guidelines
- `docs/bmad-success-metrics.md` - Success metrics and KPIs
- `docs/bmad-value-streams.md` - Value stream mappings
- `docs/business-case.md` - ROI justification and investment analysis
- `docs/cloud-usage-estimates.md` - Cloud resource usage estimates with gamification
- `docs/pricing-validation-report.md` - Real-time Google Cloud pricing validation

### Progress Report Structure
When providing progress updates:
1. **Current Status**: What was completed in this session
2. **Changes Made**: Specific files modified or created
3. **Next Steps**: What needs to be done next
4. **Blockers**: Any issues encountered
5. **Metrics**: Relevant metrics or performance indicators

### Task Tracking
- Use the TodoWrite tool for all multi-step tasks
- Update task status in real-time (pending → in_progress → completed)
- Break complex tasks into smaller, manageable steps
- Document completed tasks in the appropriate BMAD tracking files

## Building and Running

### Validation Commands
Before submitting any changes, run the full preflight check:
```bash
npm run preflight
```

This command will:
- Build the repository
- Run all tests
- Check for type errors
- Lint the code

### Individual Commands
- Build: `npm run build`
- Test: `npm test`
- Type check: `npm run typecheck`
- Lint: `npm run lint`

## Testing Framework

This project uses **Vitest** as its primary testing framework. Follow these conventions:

### Test Structure
- Framework: Vitest (`describe`, `it`, `expect`, `vi`)
- File naming: `*.test.ts` for logic, `*.test.tsx` for React components
- Location: Co-located with source files
- Configuration: `vitest.config.ts` files

### Mocking Best Practices
- Mock ES modules with `vi.mock('module-name', async (importOriginal) => { ... })`
- Place critical mocks at the top of test files
- Use `vi.hoisted()` for mock functions needed before definition
- Restore spies with `mockRestore()` in `afterEach`

## Code Style Guidelines

### JavaScript/TypeScript
- **Prefer plain objects** over classes with TypeScript interfaces
- **Use ES modules** for encapsulation (import/export)
- **Avoid `any` types** - use `unknown` when type is uncertain
- **Minimize type assertions** (`as Type`) - use only when necessary
- **Embrace array operators** (.map(), .filter(), .reduce())
- **Use functional programming** patterns for immutability

### React Development
- Use functional components with Hooks
- Keep components pure and side-effect-free
- Respect one-way data flow
- Never mutate state directly
- Use useEffect sparingly and correctly
- Follow the Rules of Hooks
- Optimize for React Compiler

## Git Workflow

### Main Branch
- Main branch: `main`
- Always create feature branches from `main`
- Submit PRs to `main`

### Commit Messages
- Be concise and descriptive
- Focus on the "why" not just the "what"
- Follow repository commit style conventions

### Upstream Sync Management

This fork maintains sync with the upstream `google-gemini/gemini-cli` repository while preserving all custom enterprise features.

#### Quick Sync
```bash
# Run the sync manager
./scripts/sync-upstream.sh

# Or use the alias if configured
sync

# Check sync status
git rev-list --count HEAD...upstream/main
```

#### Protected Features
The following directories and files are protected during upstream merges:
- `.bmad-*` directories - BMAD methodology files
- `.claude/`, `.crush/`, `.scout/` - Custom tool configurations
- `src/agents/`, `src/api/`, `src/knowledge/`, `src/monitoring/` - Enterprise features
- `github-app/`, `slack-bot/` - Integrations
- `terraform/`, `k8s/`, `docker/` - Infrastructure
- `CLAUDE.md`, `SOURCE_TREE.md` - Project documentation

#### What to Pull from Upstream
**Always Pull:**
- Core CLI bug fixes and improvements
- Tool updates (grep, file system, web tools)
- Test infrastructure improvements
- Security patches

**Review Carefully:**
- Configuration changes
- Package dependency updates
- UI/UX changes that might conflict

**Never Pull (Keep Your Version):**
- Custom features and integrations
- BMAD methodology files
- Enterprise documentation
- Cloud deployment configurations

#### Sync Strategies
1. **Full Merge** (Recommended for regular syncs): `./scripts/sync-upstream.sh` → Option 1
2. **Cherry-pick** (For selective updates): `./scripts/sync-upstream.sh` → Option 2
3. **Analyze Only** (See what changed): `./scripts/sync-upstream.sh` → Option 3

#### Post-Sync Checklist
- [ ] Run `npm install` to update dependencies
- [ ] Run `npm run build` to verify build
- [ ] Test BMAD features still work
- [ ] Verify agent server: `./start_server.sh`
- [ ] Review changes: `git log --oneline upstream/main ^HEAD`

See `SYNC_GUIDE.md` for detailed sync instructions.

## File Naming Conventions
- Use hyphens instead of underscores (e.g., `my-file.ts` not `my_file.ts`)
- Test files: `*.test.ts` or `*.test.tsx`
- Configuration files: `*.config.ts`

## Project-Specific Context

### Key Directories
- `packages/cli/` - Main CLI package
- `src/agents/` - Agent implementations
- `src/api/` - API server and endpoints
- `src/knowledge/` - RAG and knowledge base system
- `github-app/` - GitHub integration
- `slack-bot/` - Slack integration
- `monitoring/` - Monitoring and observability
- `terraform/` - Infrastructure as code
- `k8s/` - Kubernetes configurations
- `vscode-extension/` - VS Code extension with BMAD validation and cloud pricing

### VS Code Extension Features
- **BMAD Status Provider** - Mandatory documentation validation (red/green status)
- **Cloud Pricing Service** - Google Cloud Billing API integration for real-time pricing
- **Business Value Tracker** - ROI calculation and investment justification
- **Cost Gamification** - Learning system for junior developers on cloud costs
- **AI Personas** - Including Business Value Analyst and DORA Agent
- **Swarm Orchestration** - Multi-agent collaboration system
- **Roadmap Provider** - Forward-looking project planning with milestone tracking (replaces Issues view)
- **Progress Tracking** - Business value-based progress monitoring with percentage completion

### Integration Points
- Vertex AI integration for Gemini models
- GitHub Actions for CI/CD
- Docker for containerization
- Kubernetes for orchestration
- PostgreSQL for data persistence
- Qdrant for vector storage
- Redis for caching
- Google Cloud Billing API for real-time pricing
- VS Code Extension API for BMAD validation

## BMAD Methodology Implementation

### Mandatory Documentation Requirements
BMAD enforces these critical requirements before any development work can proceed:

1. **Business Case** (`docs/business-case.md`) - CRITICAL
   - Executive summary with 3-year ROI projections
   - Quantified problem statement with opportunity costs
   - Detailed investment breakdown and expected benefits
   - Risk assessment and mitigation strategies
   - Implementation timeline with milestones
   - Success metrics with baselines and targets

2. **Cloud Usage Estimates** (`docs/cloud-usage-estimates.md`) - CRITICAL
   - Specific resource quantities (not "lots" or "some")
   - Growth projections with realistic assumptions
   - Seasonality factors and usage patterns
   - Cost optimization strategies identified
   - Gamification elements for junior developer learning

3. **Real-time Pricing Validation** (`docs/pricing-validation-report.md`) - CRITICAL
   - Live Google Cloud Billing API data
   - 3-year cost forecast with optimization opportunities
   - Budget thresholds and alerting strategy
   - Cost gamification dashboard for team learning
   - Junior developer cost education materials

4. **Traditional BMAD Requirements**
   - PRD (Product Requirements Document) - CRITICAL
   - Epics and Stories with acceptance criteria - MAJOR
   - Source Tree Documentation - CRITICAL
   - Architecture Documentation - MAJOR

### Cost Gamification Features
The system includes comprehensive gamification to help junior developers understand the financial impact of architectural decisions:

#### Learning Elements
- **Achievement Badges**: Cost Detective, Optimizer, Budget Guardian, Efficiency Expert
- **Team Leaderboard**: Most cost-efficient developers
- **Weekly Challenges**: Structured learning path for cost optimization
- **Real Stories**: "The $1000 Query", "The Forgotten Instance", "The Big Transfer"

#### Educational Components
- **Cost Impact Scenarios**: Database choice implications, caching effects, API efficiency
- **Architecture Decision Games**: Monolith vs Microservices cost analysis
- **Optimization Challenges**: "Can you reduce costs by 40% using lifecycle policies?"
- **Budget Guardrails**: Alert thresholds and automatic cost monitoring

### Development Blocking System
The BMAD validator blocks ALL development work until documentation is complete:
- Code analysis commands show warning dialogs
- Swarm sessions require complete documentation
- Real-time pricing validation must be current (updated within 24 hours)
- Business case must include quantified ROI metrics

### AI Personas for Business Value
- **Business Value Analyst**: ROI analysis, business case development, investment justification
- **DORA Agent**: DevOps metrics, performance analytics, delivery optimization
- **The Architect**: Enterprise architecture with cost implications
- **Scout**: Duplicate detection with optimization opportunities
- **Guardian**: Security and compliance validation

## Google Cloud Pricing API Configuration

### Required Setup
To enable real-time cloud pricing validation:

1. **API Key Configuration**
   ```bash
   # Set environment variable
   export GOOGLE_CLOUD_API_KEY="your-api-key-here"
   
   # Or configure in VS Code settings
   "gemini.googleCloudApiKey": "your-api-key-here"
   ```

2. **API Permissions Required**
   - Cloud Billing API access
   - Service usage API access
   - Read access to pricing information

3. **Fallback Pricing**
   - System provides fallback pricing when API is unavailable
   - Warning displayed when using estimated vs. live pricing
   - Validation fails if pricing data is older than 24 hours

### Cost Gamification Configuration
- Team leaderboards require user identification
- Achievement badges stored in workspace `.gemini/achievements.json`
- Cost thresholds configurable per environment
- Learning scenarios customizable for company context

## Important Reminders

1. **Always prefer updating existing files** over creating new ones
2. **Check for existing documentation** before creating any new docs
3. **Update BMAD tracking files** when working on BMAD tasks
4. **Use TodoWrite tool** for task management
5. **Run preflight checks** before committing
6. **Follow existing code patterns** and conventions
7. **Write tests** for new functionality
8. **Document in existing files** when possible
9. **Ensure cloud pricing validation is current** before development work
10. **Include cost gamification elements** in all architecture decisions
11. **Use Roadmap view for forward progress** - Focus on planned work, milestones, and business value rather than historical issues
12. **Compile and test VS Code extension** after changes using `npm run compile && npm run package`

## Common Fixes and Troubleshooting

### Python F-string Syntax Errors
When encountering f-string errors like:
```
SyntaxError: f-string: valid expression required before '}'
```

**Problem**: Double curly braces `{{}}` in f-strings or invalid expressions
**Solution**: 
- Use single curly braces for variables: `{'key': value}`
- For empty dict fallback, use `or []` instead of `or {}`
- Example fix: `tags={{'filter_count': len(filters or {})}}` → `tags={'filter_count': len(filters or [])}`

### BMAD Agent Server Startup Issues
If `./start_server.sh` fails:
1. Check Python virtual environment activation
2. Verify all dependencies installed: `pip install fastapi uvicorn websockets python-multipart pydantic psutil coverage pytest pytest-cov aiofiles redis python-json-logger beautifulsoup4 requests`
3. Ensure `PYTHONPATH` includes `src/` directory
4. Check for syntax errors in Python files
5. Fix relative import errors: Use `from agents.enhanced.scout import CodeAnalyzer` instead of `from ..agents.enhanced.scout import CodeAnalyzer`
6. If port 2000 is in use: `lsof -ti:2000 | xargs kill -9`

### VS Code Extension Compilation Errors

#### TypeScript Compilation Issues
**Error Pattern**: `Cannot find name 'variableName'` or `Parameter 'X' of constructor has or is using private name 'Y'`

**Common Causes & Fixes**:
1. **Variable Scope Issues**
   - **Problem**: Variable declared inside try block, used outside
   - **Fix**: Declare variable at function scope with proper typing
   ```typescript
   // Before (broken)
   try {
     const myProvider = new MyProvider();
   } catch {}
   // Later...
   myProvider.refresh(); // Error: Cannot find name

   // After (fixed)
   let myProvider: MyProvider | undefined;
   try {
     myProvider = new MyProvider();
   } catch {}
   // Later...
   if (myProvider) {
     myProvider.refresh();
   }
   ```

2. **Interface/Type Mismatches**
   - **Problem**: Changed interface name but old references remain
   - **Fix**: Use global find/replace to update all references consistently
   - **Example**: `DocumentationItem` renamed to `ProjectItem` - update ALL files

3. **Missing Import Dependencies**
   - **Problem**: Imported old file that was renamed/moved
   - **Fix**: Update import paths or remove unused imports
   ```typescript
   // Fix import paths
   import { ProjectExplorerProvider } from './providers/ProjectExplorerProvider';
   // Remove old imports
   // import { DocumentationProvider } from './providers/DocumentationProvider';
   ```

#### Extension Registration Errors
**Error Pattern**: `Cannot find name 'registrationVariable'`

**Problem**: Provider registration variables not properly handled
**Fix**: Ensure consistent naming and proper subscription handling
```typescript
// Correct pattern
const myRegistration = vscode.window.registerTreeDataProvider('view-id', provider);
context.subscriptions.push(myRegistration);
```

#### EventEmitter Type Errors
**Error Pattern**: `Expected 1 arguments, but got 0` on `.fire()`

**Problem**: VS Code EventEmitter requires explicit argument
**Fix**: Always pass argument to fire(), use `undefined` if no specific data
```typescript
// Before (broken)
this._onDidChangeTreeData.fire();

// After (fixed)
this._onDidChangeTreeData.fire(undefined);
```

### Extension Development Best Practices

#### File Renaming/Replacement Process
When replacing providers (like Documentation → ProjectExplorer, Issues → Roadmap):
1. Create new file with complete implementation
2. Update all import statements in extension.ts
3. Update variable names consistently throughout
4. Update package.json view configurations and command registrations
5. Update interface definitions in client.ts if needed
6. Remove or rename old files (add .old extension)
7. Compile and fix any remaining type errors
8. Test thoroughly before packaging

#### VS Code Extension Roadmap Migration (Completed 2025-08-20)
**Migration from Issues to Roadmap Provider:**
- Replaced `IssuesProvider` with `RoadmapProvider` for forward-looking project planning
- Updated view from "Issues" to "🗺️ Roadmap" in package.json
- Added business value tracking (1-10 scale) and progress percentages
- Implemented milestone-based organization with multiple view modes
- Added rich WebView interface for detailed roadmap item display
- Updated all command registrations (refresh, clear, changeView, openItem)
- Modified client interfaces to support RoadmapItem instead of ValidationIssue focus

#### AI Personas Integration (Completed 2025-08-20)
**Enhanced Conversation Management:**
- Implemented `ConversationContextManager` for persistent conversation tracking
- Added context-aware chat with file awareness, project detection, and topic tracking
- Enhanced WebView interface with context badges and conversation statistics
- Added fallback responses for offline operation with persona-specific content
- Integrated conversation history storage with automatic cleanup
- Added conversation analytics and persona usage tracking
- Enhanced chat interface with typing indicators and improved UX
- Conversation sessions persist across VS Code restarts

#### Compilation Workflow
```bash
# Always clean compile when major changes
rm -rf out
npm run compile

# Package and test
npm run package
code --install-extension ./extension-name.vsix --force

# Test in new VS Code window
code --new-window
```

### Project Organization Issues

#### Tasks Directory Cleanup
**Problem**: Mixed content types in `/tasks` directory
**Solution**: Organize by content type:
- Keep: `epic-*.md`, `story-*.md`, `README.md`
- Move to `docs/architecture/`: Implementation roadmaps
- Move to `docs/project-management/`: JSON task files
- Archive: Completed stories in `archived/` subfolder

#### Story Status Management
**Best Practice**: Always update story status to reflect actual implementation
- Mark completed tasks as `[x]`
- Update story status at bottom
- Add implementation notes for clarity
- Keep stories as living documents, not static plans

#### Story Status Icon Issues
**Problem**: Completed stories showing blue circles instead of green checkmarks
**Root Cause**: EpicsProvider parsing logic doesn't match story file format
**Solution**: Update parsing logic to match actual story status format

```typescript
// Story files contain: *Story Status*: **Completed**
// But parser was looking for: Status:** Done

// Fix in EpicsProvider.ts parseStory method:
if (content.includes('Status:** Done') || 
    content.includes('*Story Status*: **Completed**') || // Add this line
    content.includes('✅')) {
    status = 'done';
}
```

**Status Mapping**: 
- `'done'` status → Green checkmark icon (`check-all`) 
- `'in-progress'` status → Blue loading icon
- `'todo'` status → Gray circle outline

## Reference Files
- Source tree structure: `sourcetree.md`
- Gemini instructions: `GEMINI.md`
- Architecture documentation: `docs/architecture/`
- BMAD method details: `.bmad-core/` and `.gemini/bmad-method/`

## BMAD Directory Structure

The project's documentation is organized under the `/docs` directory with the following structure:

-   `/docs/0_business_case/`
-   `/docs/1_product/`
-   `/docs/2_architecture/`
-   `/docs/3_manuals/`
-   `/docs/4_quality/`
-   `/docs/5_project_management/`
-   `/docs/tasks/` (contains epics and stories)