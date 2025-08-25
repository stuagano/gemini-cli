import * as vscode from 'vscode';
import { DocumentationProvider } from './providers/DocumentationProvider';
import { EpicsStoriesProvider } from './providers/EpicsStoriesProvider';
import { RAGDatastoreProvider } from './providers/RAGDatastoreProvider';
import { DocumentationService } from './services/DocumentationService';
import { RAGService } from './services/RAGService';
import { registerCommands } from './commands';

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 GEMINI EXTENSION: Starting activation...');
    vscode.window.showInformationMessage('🚀 Gemini Documentation Manager: Activating...');
    
    // Check if workspace is available
    if (!vscode.workspace.workspaceFolders) {
        const errorMsg = 'Gemini Extension: No workspace folder open. Please open a folder first.';
        console.log('❌ GEMINI EXTENSION:', errorMsg);
        vscode.window.showErrorMessage(errorMsg);
        return;
    }
    
    const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
    console.log('✅ GEMINI EXTENSION: Workspace root:', workspaceRoot);

    // Initialize services
    const docService = new DocumentationService();
    const ragService = new RAGService();

    // Create providers
    console.log('🔧 GEMINI EXTENSION: Creating providers...');
    const docProvider = new DocumentationProvider(docService);
    const epicsProvider = new EpicsStoriesProvider();
    const ragProvider = new RAGDatastoreProvider(ragService);
    console.log('✅ GEMINI EXTENSION: Providers created');

    // Register tree data providers
    console.log('🔧 GEMINI EXTENSION: Registering tree views...');
    const docTreeView = vscode.window.createTreeView('documentation-status', {
        treeDataProvider: docProvider,
        showCollapseAll: true
    });
    console.log('✅ GEMINI EXTENSION: Documentation tree view registered');

    const epicsTreeView = vscode.window.createTreeView('epics-stories', {
        treeDataProvider: epicsProvider,
        showCollapseAll: true
    });
    console.log('✅ GEMINI EXTENSION: Epics tree view registered');

    const ragTreeView = vscode.window.createTreeView('rag-datastore', {
        treeDataProvider: ragProvider,
        showCollapseAll: true
    });
    console.log('✅ GEMINI EXTENSION: RAG tree view registered');

    // Register a simple test command first
    console.log('🔧 GEMINI EXTENSION: Registering test command...');
    const testCommand = vscode.commands.registerCommand('gemini.test', () => {
        vscode.window.showInformationMessage('Test command works!');
    });
    context.subscriptions.push(testCommand);
    console.log('✅ GEMINI EXTENSION: Test command registered');

    // Register commands
    console.log('🔧 GEMINI EXTENSION: Registering commands...');
    registerCommands(context, docProvider, epicsProvider, ragProvider, docService, ragService);
    console.log('✅ GEMINI EXTENSION: Commands registered');

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
    // Test if commands are actually registered
    setTimeout(() => {
        vscode.commands.getCommands(true).then(commands => {
            const geminiCommands = commands.filter(cmd => cmd.startsWith('gemini.'));
            console.log('🔍 GEMINI EXTENSION: Registered commands:', geminiCommands);
            if (geminiCommands.length === 0) {
                console.log('❌ GEMINI EXTENSION: No gemini commands found!');
            }
        });
    }, 1000);

    console.log('🎉 GEMINI EXTENSION: Activation completed successfully!');
    vscode.window.showInformationMessage('🎉 Gemini Documentation Manager activated successfully!');
}

export function deactivate() {
    console.log('Gemini Documentation Manager deactivated');
}