import * as vscode from 'vscode';
import { DocumentationService } from '../services/DocumentationService';
import { RAGService } from '../services/RAGService';

export class DashboardPanel {
    public static currentPanel: DashboardPanel | undefined;
    public static readonly viewType = 'geminiDashboard';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(
        extensionUri: vscode.Uri,
        docService: DocumentationService,
        ragService: RAGService
    ) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (DashboardPanel.currentPanel) {
            DashboardPanel.currentPanel._panel.reveal(column);
            DashboardPanel.currentPanel._update(docService, ragService);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            DashboardPanel.viewType,
            'Gemini Documentation Dashboard',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [extensionUri]
            }
        );

        DashboardPanel.currentPanel = new DashboardPanel(panel, extensionUri, docService, ragService);
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        docService: DocumentationService,
        ragService: RAGService
    ) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        // Set the webview's initial html content
        this._update(docService, ragService);

        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Update the content based on view changes
        this._panel.onDidChangeViewState(
            e => {
                if (this._panel.visible) {
                    this._update(docService, ragService);
                }
            },
            null,
            this._disposables
        );

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'refresh':
                        this._update(docService, ragService);
                        return;
                    case 'openDocument':
                        vscode.commands.executeCommand('gemini.openDocument', message.path);
                        return;
                    case 'uploadToRAG':
                        vscode.commands.executeCommand('gemini.uploadToRAG', vscode.Uri.file(message.path));
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    public dispose() {
        DashboardPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private async _update(docService: DocumentationService, ragService: RAGService) {
        const webview = this._panel.webview;
        this._panel.webview.html = await this._getHtmlForWebview(webview, docService, ragService);
    }

    private async _getHtmlForWebview(
        webview: vscode.Webview,
        docService: DocumentationService,
        ragService: RAGService
    ): Promise<string> {
        // Get documentation statistics
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath || '';
        const categories = [
            { name: 'Business Case', path: 'docs/0_business_case' },
            { name: 'Product', path: 'docs/1_product' },
            { name: 'Architecture', path: 'docs/2_architecture' },
            { name: 'Manuals', path: 'docs/3_manuals' },
            { name: 'Quality', path: 'docs/4_quality' },
            { name: 'Project Management', path: 'docs/5_project_management' }
        ];

        let categoryStats = [];
        let totalDocs = 0;
        let completeDocs = 0;
        let totalWords = 0;

        for (const cat of categories) {
            const status = docService.getCategoryStatus(`${workspaceRoot}/${cat.path}`);
            const docsCount = status.sections.length;
            totalDocs += docsCount;
            if (status.complete) completeDocs += docsCount;
            totalWords += status.wordCount;
            
            categoryStats.push({
                name: cat.name,
                complete: status.complete,
                wordCount: status.wordCount,
                progress: status.complete ? 100 : (status.inProgress ? 50 : 0)
            });
        }

        // Get RAG statistics
        const ragDocs = await ragService.getDocuments();
        const ragStats = {
            total: ragDocs.length,
            indexed: ragDocs.filter(d => d.indexed).length,
            totalSize: Math.round(ragDocs.reduce((sum, d) => sum + d.size, 0) / 1024)
        };

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Documentation Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            padding: 20px;
            margin: 0;
        }
        
        h1 {
            color: var(--vscode-editor-foreground);
            border-bottom: 2px solid var(--vscode-panel-border);
            padding-bottom: 10px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .card {
            background: var(--vscode-editorWidget-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .card h2 {
            margin-top: 0;
            color: var(--vscode-foreground);
            font-size: 1.2em;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px;
            background: var(--vscode-editor-background);
            border-radius: 4px;
        }
        
        .stat-label {
            font-weight: 500;
        }
        
        .stat-value {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: var(--vscode-input-background);
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--vscode-progressBar-background);
            transition: width 0.3s ease;
        }
        
        .category-item {
            padding: 10px;
            margin: 5px 0;
            background: var(--vscode-editor-background);
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .category-item:hover {
            background: var(--vscode-list-hoverBackground);
        }
        
        .complete {
            color: var(--vscode-terminal-ansiGreen);
        }
        
        .in-progress {
            color: var(--vscode-terminal-ansiYellow);
        }
        
        .not-started {
            color: var(--vscode-terminal-ansiRed);
        }
        
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .overview-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .overview-stat {
            text-align: center;
            padding: 15px;
            background: var(--vscode-editorWidget-background);
            border-radius: 8px;
            border: 1px solid var(--vscode-panel-border);
        }
        
        .overview-stat .value {
            font-size: 2em;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        
        .overview-stat .label {
            margin-top: 5px;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <h1>📊 Gemini Documentation Dashboard</h1>
    
    <div class="overview-stats">
        <div class="overview-stat">
            <div class="value">${totalDocs}</div>
            <div class="label">Total Documents</div>
        </div>
        <div class="overview-stat">
            <div class="value">${completeDocs}</div>
            <div class="label">Completed</div>
        </div>
        <div class="overview-stat">
            <div class="value">${Math.round((completeDocs / totalDocs) * 100)}%</div>
            <div class="label">Progress</div>
        </div>
        <div class="overview-stat">
            <div class="value">${Math.round(totalWords / 1000)}k</div>
            <div class="label">Total Words</div>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h2>📚 Documentation Status</h2>
            ${categoryStats.map(cat => `
                <div class="category-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="${cat.complete ? 'complete' : (cat.progress > 0 ? 'in-progress' : 'not-started')}">
                            ${cat.complete ? '✅' : (cat.progress > 0 ? '🔄' : '⚠️')} ${cat.name}
                        </span>
                        <span>${cat.wordCount} words</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${cat.progress}%"></div>
                    </div>
                </div>
            `).join('')}
            <button onclick="refreshDashboard()">Refresh</button>
        </div>
        
        <div class="card">
            <h2>🗄️ RAG Datastore</h2>
            <div class="stat">
                <span class="stat-label">Total Documents:</span>
                <span class="stat-value">${ragStats.total}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Indexed:</span>
                <span class="stat-value">${ragStats.indexed}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Total Size:</span>
                <span class="stat-value">${ragStats.totalSize} KB</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${ragStats.total > 0 ? (ragStats.indexed / ragStats.total) * 100 : 0}%"></div>
            </div>
            <button onclick="uploadToRAG()">Upload Documents</button>
            <button onclick="searchRAG()">Search</button>
        </div>
        
        <div class="card">
            <h2>🎯 Quick Actions</h2>
            <button onclick="createDocument()">Create Document</button>
            <button onclick="createEpic()">Create Epic</button>
            <button onclick="createStory()">Create Story</button>
            <button onclick="validateDocs()">Validate All</button>
            <button onclick="syncRAG()">Sync RAG</button>
        </div>
        
        <div class="card">
            <h2>📈 Metrics</h2>
            <div class="stat">
                <span class="stat-label">Documentation Coverage:</span>
                <span class="stat-value">${Math.round((completeDocs / totalDocs) * 100)}%</span>
            </div>
            <div class="stat">
                <span class="stat-label">Average Doc Size:</span>
                <span class="stat-value">${Math.round(totalWords / totalDocs)} words</span>
            </div>
            <div class="stat">
                <span class="stat-label">RAG Coverage:</span>
                <span class="stat-value">${Math.round((ragStats.indexed / totalDocs) * 100)}%</span>
            </div>
        </div>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        
        function refreshDashboard() {
            vscode.postMessage({ command: 'refresh' });
        }
        
        function createDocument() {
            vscode.postMessage({ command: 'createDocument' });
        }
        
        function createEpic() {
            vscode.postMessage({ command: 'createEpic' });
        }
        
        function createStory() {
            vscode.postMessage({ command: 'createStory' });
        }
        
        function uploadToRAG() {
            vscode.postMessage({ command: 'uploadToRAG' });
        }
        
        function searchRAG() {
            vscode.postMessage({ command: 'searchRAG' });
        }
        
        function validateDocs() {
            vscode.postMessage({ command: 'validateDocs' });
        }
        
        function syncRAG() {
            vscode.postMessage({ command: 'syncRAG' });
        }
    </script>
</body>
</html>`;
    }
}