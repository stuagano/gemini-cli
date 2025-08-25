import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { DocumentationService, DocumentStatus } from '../services/DocumentationService';

export class DocumentationProvider implements vscode.TreeDataProvider<DocumentItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<DocumentItem | undefined | null | void> = new vscode.EventEmitter<DocumentItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<DocumentItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private docService: DocumentationService) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: DocumentItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: DocumentItem): Thenable<DocumentItem[]> {
        console.log('📁 DOC PROVIDER: getChildren called', element ? element.label : 'root');
        if (!vscode.workspace.workspaceFolders) {
            console.log('❌ DOC PROVIDER: No workspace folder open');
            vscode.window.showInformationMessage('No workspace folder open');
            return Promise.resolve([]);
        }

        const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;

        if (!element) {
            // Root level - show categories
            return Promise.resolve(this.getDocumentCategories(workspaceRoot));
        } else if (element.contextValue === 'category') {
            // Show documents in category
            return Promise.resolve(this.getDocumentsInCategory(workspaceRoot, element.label as string));
        } else {
            return Promise.resolve([]);
        }
    }

    private getDocumentCategories(workspaceRoot: string): DocumentItem[] {
        const config = vscode.workspace.getConfiguration('gemini');
        const structure = config.get<string>('documentationStructure', 'gcar');
        const docPath = config.get<string>('documentationPath', 'docs');
        
        let categories: Array<{name: string, path: string, icon: string}> = [];
        
        if (structure === 'gcar') {
            categories = [
                { name: 'Business Case', path: `${docPath}/0_business_case`, icon: '💼' },
                { name: 'Product', path: `${docPath}/1_product`, icon: '📦' },
                { name: 'Architecture', path: `${docPath}/2_architecture`, icon: '🏗️' },
                { name: 'Manuals', path: `${docPath}/3_manuals`, icon: '📚' },
                { name: 'Quality', path: `${docPath}/4_quality`, icon: '✅' },
                { name: 'Project Management', path: `${docPath}/5_project_management`, icon: '📊' }
            ];
        } else if (structure === 'flat') {
            categories = [
                { name: 'Documentation', path: docPath, icon: '📝' }
            ];
        } else if (structure === 'custom') {
            const customCategories = config.get<Array<{name: string, path: string, icon: string}>>('customCategories', []);
            categories = customCategories.length > 0 ? customCategories : [
                { name: 'Documentation', path: docPath, icon: '📝' }
            ];
        }

        return categories.map(cat => {
            const categoryPath = path.join(workspaceRoot, cat.path);
            const status = this.docService.getCategoryStatus(categoryPath);
            const completionPercentage = this.calculateCompletionPercentage(categoryPath);
            
            return new DocumentItem(
                `${cat.icon} ${cat.name} (${completionPercentage}%)`,
                status.complete ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.Expanded,
                'category',
                categoryPath,
                status
            );
        });
    }

    private getDocumentsInCategory(workspaceRoot: string, categoryLabel: string): DocumentItem[] {
        const config = vscode.workspace.getConfiguration('gemini');
        const structure = config.get<string>('documentationStructure', 'gcar');
        const docPath = config.get<string>('documentationPath', 'docs');
        
        // Extract category name from label (remove icon and percentage)
        const categoryName = categoryLabel.split(' ')[1];
        
        let categoryPath: string;
        
        if (structure === 'gcar') {
            const categoryMap: { [key: string]: string } = {
                'Business': `${docPath}/0_business_case`,
                'Product': `${docPath}/1_product`,
                'Architecture': `${docPath}/2_architecture`,
                'Manuals': `${docPath}/3_manuals`,
                'Quality': `${docPath}/4_quality`,
                'Project': `${docPath}/5_project_management`
            };
            categoryPath = path.join(workspaceRoot, categoryMap[categoryName] || docPath);
        } else if (structure === 'flat') {
            categoryPath = path.join(workspaceRoot, docPath);
        } else {
            // Custom structure - find matching category
            const customCategories = config.get<Array<{name: string, path: string, icon: string}>>('customCategories', []);
            const category = customCategories.find(cat => cat.name === categoryName);
            categoryPath = path.join(workspaceRoot, category?.path || docPath);
        }
        
        if (!fs.existsSync(categoryPath)) {
            return [];
        }

        const files = fs.readdirSync(categoryPath)
            .filter(file => file.endsWith('.md'))
            .map(file => {
                const filePath = path.join(categoryPath, file);
                const status = this.docService.getDocumentStatus(filePath);
                const icon = this.getStatusIcon(status);
                
                return new DocumentItem(
                    `${icon} ${file}`,
                    vscode.TreeItemCollapsibleState.None,
                    'document',
                    filePath,
                    status
                );
            });

        return files;
    }

    private calculateCompletionPercentage(categoryPath: string): number {
        if (!fs.existsSync(categoryPath)) {
            return 0;
        }

        const files = fs.readdirSync(categoryPath).filter(f => f.endsWith('.md'));
        if (files.length === 0) return 0;

        let completeCount = 0;
        files.forEach(file => {
            const status = this.docService.getDocumentStatus(path.join(categoryPath, file));
            if (status.complete) completeCount++;
        });

        return Math.round((completeCount / files.length) * 100);
    }

    private getStatusIcon(status: DocumentStatus): string {
        if (status.complete) return '✅';
        if (status.inProgress) return '🔄';
        if (status.hasContent) return '📝';
        return '⚠️';
    }
}

export class DocumentItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly resourcePath: string,
        public readonly status: DocumentStatus
    ) {
        super(label, collapsibleState);
        
        this.tooltip = this.getTooltip();
        this.description = this.getDescription();
        
        if (contextValue === 'document') {
            this.command = {
                command: 'gemini.openDocument',
                title: 'Open Document',
                arguments: [this.resourcePath]
            };
        }
    }

    private getTooltip(): string {
        if (this.contextValue === 'category') {
            return `Category: ${this.label}\nStatus: ${this.status.complete ? 'Complete' : 'In Progress'}`;
        } else {
            const sections = this.status.sections || [];
            return `Document: ${this.label}\nSections: ${sections.length}\nComplete: ${this.status.complete ? 'Yes' : 'No'}`;
        }
    }

    private getDescription(): string {
        if (this.contextValue === 'category') {
            return this.status.complete ? 'Complete' : 'In Progress';
        } else {
            const wordCount = this.status.wordCount || 0;
            return `${wordCount} words`;
        }
    }
}