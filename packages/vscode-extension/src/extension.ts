import * as vscode from 'vscode';
import { DocumentationProvider } from './providers/DocumentationProvider';
import { EpicsStoriesProvider } from './providers/EpicsStoriesProvider';
import { RAGDatastoreProvider } from './providers/RAGDatastoreProvider';
import { DocumentationService } from './services/DocumentationService';
import { RAGService } from './services/RAGService';
import { DashboardPanel } from './webviews/DashboardPanel';
import { registerCommands } from './commands';

export function activate(context: vscode.ExtensionContext) {
    console.log('Gemini Documentation Manager is now active!');

    // Initialize services
    const docService = new DocumentationService();
    const ragService = new RAGService();

    // Create providers
    const docProvider = new DocumentationProvider(docService);
    const epicsProvider = new EpicsStoriesProvider();
    const ragProvider = new RAGDatastoreProvider(ragService);

    // Register tree data providers
    vscode.window.createTreeView('documentation-status', {
        treeDataProvider: docProvider,
        showCollapseAll: true
    });

    vscode.window.createTreeView('epics-stories', {
        treeDataProvider: epicsProvider,
        showCollapseAll: true
    });

    vscode.window.createTreeView('rag-datastore', {
        treeDataProvider: ragProvider,
        showCollapseAll: true
    });

    // Register commands
    registerCommands(context, docProvider, epicsProvider, ragProvider, docService, ragService);

    // Set up auto-refresh if enabled
    const config = vscode.workspace.getConfiguration('gemini');
    if (config.get<boolean>('autoRefresh')) {
        const interval = config.get<number>('refreshInterval') || 30000;
        setInterval(() => {
            docProvider.refresh();
            epicsProvider.refresh();
            ragProvider.refresh();
        }, interval);
    }

    // Watch for file changes
    const watcher = vscode.workspace.createFileSystemWatcher('**/*.md');
    watcher.onDidCreate(() => {
        docProvider.refresh();
        ragProvider.refresh();
    });
    watcher.onDidChange(() => {
        docProvider.refresh();
    });
    watcher.onDidDelete(() => {
        docProvider.refresh();
        ragProvider.refresh();
    });

    context.subscriptions.push(watcher);

    // Show welcome message
    vscode.window.showInformationMessage('Gemini Documentation Manager activated successfully!');
}

export function deactivate() {
    console.log('Gemini Documentation Manager deactivated');
}