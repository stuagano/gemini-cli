import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { RAGService, RAGDocument } from '../services/RAGService';

export class RAGDatastoreProvider implements vscode.TreeDataProvider<RAGItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<RAGItem | undefined | null | void> = new vscode.EventEmitter<RAGItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<RAGItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private documents: RAGDocument[] = [];
    private uploadQueue: string[] = [];

    constructor(private ragService: RAGService) {
        this.loadDocuments();
    }

    refresh(): void {
        this.loadDocuments();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: RAGItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: RAGItem): Promise<RAGItem[]> {
        if (!element) {
            // Root level - show categories
            return this.getRAGCategories();
        } else if (element.contextValue === 'rag-category') {
            // Show documents in category
            return this.getDocumentsInCategory(element.label as string);
        }
        return [];
    }

    private async loadDocuments(): Promise<void> {
        try {
            console.log('RAGDatastoreProvider: Loading documents from server...');
            this.documents = await this.ragService.getDocuments();
            console.log(`RAGDatastoreProvider: Loaded ${this.documents.length} documents`);
        } catch (error: any) {
            console.error('Failed to load RAG documents:', error);
            this.documents = [];
            // Don't show error message, just silently use empty data
            // The service will return mock data if server is unavailable
        }
    }

    private getRAGCategories(): RAGItem[] {
        // Check if we have any documents
        if (this.documents.length === 0 && this.uploadQueue.length === 0) {
            // Show welcome/empty state
            return this.getEmptyState();
        }

        const categories = [
            { name: 'Uploaded Documents', icon: '📚', count: this.documents.length },
            { name: 'Upload Queue', icon: '⏳', count: this.uploadQueue.length },
            { name: 'Search Index', icon: '🔍', count: this.getIndexedCount() }
        ];

        return categories.map(cat => {
            return new RAGItem(
                `${cat.icon} ${cat.name} (${cat.count})`,
                cat.count > 0 ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None,
                'rag-category',
                cat.name
            );
        });
    }

    private getEmptyState(): RAGItem[] {
        const items: RAGItem[] = [];
        
        // Welcome message
        const welcome = new RAGItem(
            '👋 Welcome to RAG Datastore',
            vscode.TreeItemCollapsibleState.None,
            'rag-welcome',
            'welcome'
        );
        welcome.description = 'Get started by uploading documents';
        items.push(welcome);

        // Action items
        const uploadFile = new RAGItem(
            '📄 Click to upload a file',
            vscode.TreeItemCollapsibleState.None,
            'rag-action-upload-file',
            'upload-file'
        );
        uploadFile.command = {
            command: 'gemini.uploadFileToRAG',
            title: 'Upload File to RAG'
        };
        uploadFile.tooltip = 'Upload a single file to the RAG datastore';
        items.push(uploadFile);

        const uploadFolder = new RAGItem(
            '📁 Click to upload a folder',
            vscode.TreeItemCollapsibleState.None,
            'rag-action-upload-folder',
            'upload-folder'
        );
        uploadFolder.command = {
            command: 'gemini.uploadFolderToRAG',
            title: 'Upload Folder to RAG'
        };
        uploadFolder.tooltip = 'Upload all markdown files from a folder';
        items.push(uploadFolder);

        const uploadUrl = new RAGItem(
            '🔗 Click to add from URL',
            vscode.TreeItemCollapsibleState.None,
            'rag-action-upload-url',
            'upload-url'
        );
        uploadUrl.command = {
            command: 'gemini.uploadUrlToRAG',
            title: 'Add Document from URL'
        };
        uploadUrl.tooltip = 'Fetch and index content from a URL';
        items.push(uploadUrl);

        const checkServer = new RAGItem(
            '🔄 Check server connection',
            vscode.TreeItemCollapsibleState.None,
            'rag-action-check-server',
            'check-server'
        );
        checkServer.command = {
            command: 'gemini.checkRAGServer',
            title: 'Check RAG Server'
        };
        checkServer.tooltip = 'Verify connection to the RAG server';
        items.push(checkServer);

        return items;
    }

    private getDocumentsInCategory(category: string): RAGItem[] {
        if (category.includes('Uploaded Documents')) {
            return this.documents.map(doc => {
                const icon = this.getDocumentIcon(doc.type);
                return new RAGItem(
                    `${icon} ${doc.name}`,
                    vscode.TreeItemCollapsibleState.None,
                    'rag-document',
                    doc.name,
                    doc
                );
            });
        } else if (category.includes('Upload Queue')) {
            return this.uploadQueue.map(file => {
                return new RAGItem(
                    `⏳ ${path.basename(file)}`,
                    vscode.TreeItemCollapsibleState.None,
                    'rag-queued',
                    file
                );
            });
        } else if (category.includes('Search Index')) {
            return this.getIndexStats();
        }
        return [];
    }

    private getIndexedCount(): number {
        return this.documents.filter(d => d.indexed).length;
    }

    private getIndexStats(): RAGItem[] {
        const stats = [
            { label: 'Total Documents', value: this.documents.length },
            { label: 'Indexed', value: this.getIndexedCount() },
            { label: 'Total Chunks', value: this.documents.reduce((sum, d) => sum + (d.chunks || 0), 0) },
            { label: 'Average Chunk Size', value: Math.round(this.documents.reduce((sum, d) => sum + (d.avgChunkSize || 0), 0) / this.documents.length) || 0 }
        ];

        return stats.map(stat => {
            return new RAGItem(
                `${stat.label}: ${stat.value}`,
                vscode.TreeItemCollapsibleState.None,
                'rag-stat',
                stat.label
            );
        });
    }

    private getDocumentIcon(type?: string): string {
        switch (type) {
            case 'markdown': return '📝';
            case 'code': return '💻';
            case 'documentation': return '📖';
            case 'api': return '🔌';
            default: return '📄';
        }
    }

    async uploadDocument(filePath: string): Promise<void> {
        this.uploadQueue.push(filePath);
        this.refresh();

        try {
            await this.ragService.uploadDocument(filePath);
            this.uploadQueue = this.uploadQueue.filter(f => f !== filePath);
            vscode.window.showInformationMessage(`Document uploaded successfully: ${path.basename(filePath)}`);
        } catch (error: any) {
            this.uploadQueue = this.uploadQueue.filter(f => f !== filePath);
            vscode.window.showErrorMessage(`Failed to upload document: ${error.message}`);
        }

        this.refresh();
    }

    async uploadFolder(folderPath: string): Promise<void> {
        const files = this.getAllMarkdownFiles(folderPath);
        
        if (files.length === 0) {
            vscode.window.showWarningMessage('No markdown files found in folder');
            return;
        }

        const result = await vscode.window.showInformationMessage(
            `Upload ${files.length} markdown files to RAG datastore?`,
            'Yes',
            'No'
        );

        if (result !== 'Yes') {
            return;
        }

        for (const file of files) {
            await this.uploadDocument(file);
        }
    }

    private getAllMarkdownFiles(dir: string): string[] {
        let results: string[] = [];
        const list = fs.readdirSync(dir);
        
        list.forEach(file => {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat && stat.isDirectory()) {
                results = results.concat(this.getAllMarkdownFiles(filePath));
            } else if (file.endsWith('.md')) {
                results.push(filePath);
            }
        });
        
        return results;
    }
}

export class RAGItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly id: string,
        public readonly document?: RAGDocument
    ) {
        super(label, collapsibleState);
        
        this.tooltip = this.getTooltip();
        this.description = this.getDescription();
        
        if (contextValue === 'rag-document' && document) {
            this.command = {
                command: 'gemini.viewRAGDocument',
                title: 'View Document',
                arguments: [document]
            };
        }
    }

    private getTooltip(): string {
        if (this.document) {
            return `Document: ${this.document.name}
Type: ${this.document.type}
Size: ${this.document.size} bytes
Chunks: ${this.document.chunks}
Indexed: ${this.document.indexed ? 'Yes' : 'No'}
Uploaded: ${new Date(this.document.uploadedAt).toLocaleString()}`;
        }
        return this.label;
    }

    private getDescription(): string {
        if (this.document) {
            const size = Math.round(this.document.size / 1024);
            return `${size}KB • ${this.document.chunks} chunks`;
        }
        return '';
    }
}