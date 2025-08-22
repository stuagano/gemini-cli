# User Story: Implement Tree Data Providers

## Description
As a developer, I want to see BMAD status, AI personas, and project information in the VS Code sidebar so that I can access all Gemini features without leaving my editor.

## Acceptance Criteria
- [x] BMAD status provider shows documentation validation status with red/green indicators
- [x] Personas provider displays all available AI agents (Scout, Architect, Guardian, etc.)
- [x] Issues provider shows current code issues grouped by severity
- [x] Epics provider displays project epics and associated stories (renamed to "Current Epic Progress")
- [x] Tree views refresh automatically when data changes
- [x] Tree items are clickable and trigger appropriate actions
- [x] Empty states show helpful messages instead of errors
- [x] All providers work in offline/standalone mode
- [x] Project Explorer replaces Documentation view for file navigation
- [x] Launch Gemini CLI button added to toolbar

## Tasks
- [x] Create BMADStatusProvider class implementing TreeDataProvider interface
- [x] Create PersonasProvider with persona data management
- [x] Create IssuesProvider with issue grouping and filtering
- [x] Create EpicsProvider with story hierarchy display
- [x] Implement refresh logic with debouncing
- [x] Add click handlers for tree items
- [x] Create empty state messages
- [x] Add offline mode fallbacks
- [ ] Write unit tests for each provider
- [ ] Write integration tests for tree view display
- [x] Replace Documentation provider with ProjectExplorerProvider
- [x] Add Launch Gemini CLI command

## Definition of Done
- [x] All tree providers display data correctly
- [x] Click actions work as expected
- [x] Refresh functionality operates smoothly
- [ ] Unit test coverage > 90%
- [ ] Integration tests pass
- [x] Code review completed
- [x] Documentation updated
- [x] No memory leaks or performance issues

## Technical Notes
- Use VS Code TreeDataProvider API
- Implement disposable pattern for cleanup
- Cache data to reduce API calls
- Use async/await for data fetching

## Story Points
**5** - Medium complexity, well-defined requirements

## Dependencies
- VS Code Extension API
- TypeScript interfaces for data models
- Gemini backend API (optional for standalone mode)

---
*Story Status*: **Completed**
*Epic*: epic-vs-code-extension
*Sprint*: Sprint 1
*Assignee*: Development Team