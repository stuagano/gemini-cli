import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { DocumentationProvider } from '../providers/DocumentationProvider';
import { EpicsStoriesProvider } from '../providers/EpicsStoriesProvider';
import { RAGDatastoreProvider } from '../providers/RAGDatastoreProvider';
import { DocumentationService } from '../services/DocumentationService';
import { RAGService } from '../services/RAGService';
import { DashboardPanel } from '../webviews/DashboardPanel';

export function registerCommands(
    context: vscode.ExtensionContext,
    docProvider: DocumentationProvider,
    epicsProvider: EpicsStoriesProvider,
    ragProvider: RAGDatastoreProvider,
    docService: DocumentationService,
    ragService: RAGService
) {
    // Documentation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.refreshDocStatus', () => {
            docProvider.refresh();
            vscode.window.showInformationMessage('Documentation status refreshed');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.openDocument', (resourcePath: string) => {
            if (resourcePath) {
                vscode.workspace.openTextDocument(resourcePath).then(doc => {
                    vscode.window.showTextDocument(doc);
                });
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.editDocument', async (resourcePath: string) => {
            if (!resourcePath) {
                // Prompt for document type
                const docType = await vscode.window.showQuickPick([
                    'business-case',
                    'architecture',
                    'api',
                    'prd',
                    'testing-strategy'
                ], {
                    placeHolder: 'Select document type to create'
                });

                if (!docType) return;

                // Get file name
                const fileName = await vscode.window.showInputBox({
                    prompt: 'Enter document file name',
                    value: `${docType}.md`
                });

                if (!fileName) return;

                // Generate template
                const template = await docService.generateTemplate(docType);
                
                // Create and open document
                const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
                if (workspaceRoot) {
                    const filePath = path.join(workspaceRoot, 'docs', fileName);
                    fs.writeFileSync(filePath, template);
                    vscode.workspace.openTextDocument(filePath).then(doc => {
                        vscode.window.showTextDocument(doc);
                    });
                }
            } else {
                vscode.workspace.openTextDocument(resourcePath).then(doc => {
                    vscode.window.showTextDocument(doc);
                });
            }
        })
    );

    // Epic and Story commands
    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.refreshEpics', () => {
            epicsProvider.refresh();
            vscode.window.showInformationMessage('Epics and stories refreshed');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.createEpic', async () => {
            const epicName = await vscode.window.showInputBox({
                prompt: 'Enter epic name',
                placeHolder: 'e.g., User Authentication System'
            });

            if (!epicName) return;

            const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
            if (workspaceRoot) {
                const fileName = `epic-${epicName.toLowerCase().replace(/\s+/g, '-')}.md`;
                const filePath = path.join(workspaceRoot, 'docs', 'tasks', fileName);
                
                const template = `# Epic: ${epicName}

## Overview
[Describe the epic overview]

## Goals
### Primary Goals
- 

### Secondary Goals
- 

## User Stories
- As a [user type], I want [feature] so that [benefit]
- 

## Acceptance Criteria
### Must Have (MVP)
- [ ] 
- [ ] 

### Should Have
- [ ] 
- [ ] 

### Could Have
- [ ] 

## Definition of Done
- [ ] All unit tests pass
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Performance targets met

## Priority
**High** / Medium / Low

## Estimation
**Story Points**: [number]

## Dependencies
- 

## Progress Summary
### Overall Completion: **0%**

**Phase Status:**
- **Phase 1**: Not Started
- **Phase 2**: Not Started
- **Phase 3**: Not Started

---
*Epic Status*: **Not Started**
*Last Updated*: ${new Date().toISOString().split('T')[0]}
`;

                fs.writeFileSync(filePath, template);
                vscode.workspace.openTextDocument(filePath).then(doc => {
                    vscode.window.showTextDocument(doc);
                });
                
                epicsProvider.refresh();
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.createStory', async () => {
            const storyTitle = await vscode.window.showInputBox({
                prompt: 'Enter story title',
                placeHolder: 'e.g., Implement login functionality'
            });

            if (!storyTitle) return;

            const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
            if (workspaceRoot) {
                const storyNumber = Date.now().toString().slice(-3);
                const fileName = `story-${storyNumber}-${storyTitle.toLowerCase().replace(/\s+/g, '-')}.md`;
                const filePath = path.join(workspaceRoot, 'docs', 'tasks', fileName);
                
                const template = `# Story ${storyNumber}: ${storyTitle}

## Story
As a [user type], I want [feature] so that [benefit]

## Acceptance Criteria
- [ ] Given [context], when [action], then [outcome]
- [ ] 
- [ ] 

## Technical Details
### Implementation Notes
- 

### API Changes
- 

### Database Changes
- 

## Tasks
- [ ] Design implementation
- [ ] Write unit tests
- [ ] Implement feature
- [ ] Update documentation
- [ ] Code review
- [ ] Integration testing

## Estimation
**Story Points**: [number]

## Dependencies
- 

## Testing Notes
- 

---
*Story Status*: **To Do**
*Assigned To*: [developer]
*Sprint*: [sprint number]
*Created*: ${new Date().toISOString().split('T')[0]}
`;

                fs.writeFileSync(filePath, template);
                vscode.workspace.openTextDocument(filePath).then(doc => {
                    vscode.window.showTextDocument(doc);
                });
                
                epicsProvider.refresh();
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.markStoryComplete', async (item) => {
            if (item && item.story) {
                const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
                if (workspaceRoot) {
                    const filePath = path.join(workspaceRoot, 'docs', 'tasks', item.story.file);
                    let content = fs.readFileSync(filePath, 'utf8');
                    
                    // Update story status
                    content = content.replace(/\*Story Status\*: \*\*.*\*\*/, '*Story Status*: **Completed**');
                    content = content.replace(/\*\*To Do\*\*/, '**Completed**');
                    content = content.replace(/\*\*In Progress\*\*/, '**Completed**');
                    
                    // Add completion date if not present
                    if (!content.includes('*Completed*:')) {
                        content += `\n*Completed*: ${new Date().toISOString().split('T')[0]}`;
                    }
                    
                    fs.writeFileSync(filePath, content);
                    epicsProvider.refresh();
                    vscode.window.showInformationMessage(`Story marked as complete: ${item.story.title}`);
                }
            }
        })
    );

    // RAG commands
    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.uploadToRAG', async (resourceUri?: vscode.Uri) => {
            let filePath: string | undefined;
            
            if (resourceUri) {
                filePath = resourceUri.fsPath;
            } else {
                const result = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    filters: {
                        'Markdown': ['md'],
                        'All Files': ['*']
                    }
                });
                
                if (result && result[0]) {
                    filePath = result[0].fsPath;
                }
            }
            
            if (filePath) {
                await ragProvider.uploadDocument(filePath);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.uploadFolderToRAG', async (resourceUri?: vscode.Uri) => {
            let folderPath: string | undefined;
            
            if (resourceUri) {
                folderPath = resourceUri.fsPath;
            } else {
                const result = await vscode.window.showOpenDialog({
                    canSelectFiles: false,
                    canSelectFolders: true,
                    canSelectMany: false
                });
                
                if (result && result[0]) {
                    folderPath = result[0].fsPath;
                }
            }
            
            if (folderPath) {
                await ragProvider.uploadFolder(folderPath);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.viewRAGStatus', async () => {
            const serverStatus = await ragService.checkServerStatus();
            const documents = await ragService.getDocuments();
            
            const message = `RAG Datastore Status:
Server: ${serverStatus ? '🟢 Online' : '🔴 Offline'}
Documents: ${documents.length}
Indexed: ${documents.filter(d => d.indexed).length}
Total Size: ${Math.round(documents.reduce((sum, d) => sum + d.size, 0) / 1024)}KB`;
            
            vscode.window.showInformationMessage(message);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.searchRAG', async () => {
            const query = await vscode.window.showInputBox({
                prompt: 'Enter search query',
                placeHolder: 'e.g., authentication flow'
            });
            
            if (!query) return;
            
            const results = await ragService.searchDocuments(query);
            
            if (results.length === 0) {
                vscode.window.showInformationMessage('No results found');
                return;
            }
            
            const items = results.map(r => ({
                label: r.documentName,
                description: `Score: ${r.score.toFixed(2)}`,
                detail: r.chunk.substring(0, 100) + '...'
            }));
            
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a result to view'
            });
            
            if (selected) {
                const result = results.find(r => r.documentName === selected.label);
                if (result) {
                    // Show result in new document
                    const doc = await vscode.workspace.openTextDocument({
                        content: `# Search Result\n\n**Document**: ${result.documentName}\n**Score**: ${result.score}\n\n## Content\n\n${result.chunk}`,
                        language: 'markdown'
                    });
                    vscode.window.showTextDocument(doc);
                }
            }
        })
    );

    // Dashboard command
    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.showDashboard', () => {
            DashboardPanel.createOrShow(context.extensionUri, docService, ragService);
        })
    );

    // Sync command
    context.subscriptions.push(
        vscode.commands.registerCommand('gemini.syncRAG', async () => {
            const synced = await ragService.syncLocalDocuments();
            vscode.window.showInformationMessage(`Synced ${synced} documents to RAG datastore`);
            ragProvider.refresh();
        })
    );
}