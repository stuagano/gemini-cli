import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import axios from 'axios';

export interface RAGDocument {
    id: string;
    name: string;
    path: string;
    type: string;
    size: number;
    chunks: number;
    avgChunkSize: number;
    indexed: boolean;
    uploadedAt: string;
    metadata?: any;
}

export interface SearchResult {
    documentId: string;
    documentName: string;
    chunk: string;
    score: number;
    metadata?: any;
}

export class RAGService {
    private serverUrl: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('gemini');
        this.serverUrl = config.get<string>('ragServerUrl') || 'http://localhost:2000';
    }

    async getDocuments(): Promise<RAGDocument[]> {
        try {
            const response = await axios.get(`${this.serverUrl}/api/rag/documents`);
            return response.data.documents || [];
        } catch (error) {
            console.error('Failed to fetch documents:', error);
            // Return mock data if server is not available
            return this.getMockDocuments();
        }
    }

    async uploadDocument(filePath: string): Promise<void> {
        const content = fs.readFileSync(filePath, 'utf8');
        const fileName = path.basename(filePath);
        const fileType = this.detectFileType(fileName);

        try {
            const response = await axios.post(`${this.serverUrl}/api/rag/upload`, {
                name: fileName,
                content: content,
                type: fileType,
                path: filePath,
                metadata: {
                    uploadedBy: 'vscode-extension',
                    timestamp: new Date().toISOString()
                }
            });

            if (response.status !== 200 && response.status !== 201) {
                throw new Error(`Upload failed with status ${response.status}`);
            }
        } catch (error: any) {
            // If server is not available, store locally
            console.error('Failed to upload to server, storing locally:', error);
            await this.storeLocally(filePath, content, fileType);
        }
    }

    async searchDocuments(query: string, limit: number = 10): Promise<SearchResult[]> {
        try {
            const response = await axios.post(`${this.serverUrl}/api/rag/search`, {
                query,
                limit
            });
            return response.data.results || [];
        } catch (error) {
            console.error('Search failed:', error);
            return [];
        }
    }

    async deleteDocument(documentId: string): Promise<void> {
        try {
            await axios.delete(`${this.serverUrl}/api/rag/documents/${documentId}`);
        } catch (error) {
            console.error('Failed to delete document:', error);
            throw error;
        }
    }

    async getDocumentContent(documentId: string): Promise<string> {
        try {
            const response = await axios.get(`${this.serverUrl}/api/rag/documents/${documentId}/content`);
            return response.data.content;
        } catch (error) {
            console.error('Failed to fetch document content:', error);
            return '';
        }
    }

    async reindexDocuments(): Promise<void> {
        try {
            await axios.post(`${this.serverUrl}/api/rag/reindex`);
        } catch (error) {
            console.error('Failed to reindex documents:', error);
            throw error;
        }
    }

    private detectFileType(fileName: string): string {
        const ext = path.extname(fileName).toLowerCase();
        const name = fileName.toLowerCase();

        if (name.includes('api')) return 'api';
        if (name.includes('architecture') || name.includes('design')) return 'architecture';
        if (name.includes('test') || name.includes('spec')) return 'test';
        if (name.includes('readme') || name.includes('guide') || name.includes('manual')) return 'documentation';
        
        switch (ext) {
            case '.md': return 'markdown';
            case '.ts':
            case '.js':
            case '.py':
            case '.java':
            case '.go': return 'code';
            case '.json':
            case '.yaml':
            case '.yml': return 'config';
            default: return 'text';
        }
    }

    private async storeLocally(filePath: string, content: string, type: string): Promise<void> {
        // Store in workspace storage for later sync
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceRoot) return;

        const ragStorePath = path.join(workspaceRoot, '.vscode', 'rag-store');
        if (!fs.existsSync(ragStorePath)) {
            fs.mkdirSync(ragStorePath, { recursive: true });
        }

        const metadata = {
            originalPath: filePath,
            type,
            uploadedAt: new Date().toISOString(),
            synced: false
        };

        const fileName = path.basename(filePath);
        const storePath = path.join(ragStorePath, `${Date.now()}-${fileName}`);
        const metaPath = storePath + '.meta.json';

        fs.writeFileSync(storePath, content);
        fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2));
    }

    private getMockDocuments(): RAGDocument[] {
        // Return mock data for development/testing
        return [
            {
                id: '1',
                name: 'architecture.md',
                path: '/docs/architecture.md',
                type: 'architecture',
                size: 5432,
                chunks: 12,
                avgChunkSize: 453,
                indexed: true,
                uploadedAt: new Date().toISOString()
            },
            {
                id: '2',
                name: 'api-specification.md',
                path: '/docs/api-specification.md',
                type: 'api',
                size: 8765,
                chunks: 18,
                avgChunkSize: 487,
                indexed: true,
                uploadedAt: new Date().toISOString()
            }
        ];
    }

    async checkServerStatus(): Promise<boolean> {
        try {
            const response = await axios.get(`${this.serverUrl}/health`, { timeout: 5000 });
            return response.status === 200;
        } catch {
            return false;
        }
    }

    async syncLocalDocuments(): Promise<number> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceRoot) return 0;

        const ragStorePath = path.join(workspaceRoot, '.vscode', 'rag-store');
        if (!fs.existsSync(ragStorePath)) return 0;

        const files = fs.readdirSync(ragStorePath).filter(f => !f.endsWith('.meta.json'));
        let synced = 0;

        for (const file of files) {
            const filePath = path.join(ragStorePath, file);
            const metaPath = filePath + '.meta.json';
            
            if (fs.existsSync(metaPath)) {
                const metadata = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
                
                if (!metadata.synced) {
                    try {
                        const content = fs.readFileSync(filePath, 'utf8');
                        await this.uploadDocument(metadata.originalPath);
                        
                        // Mark as synced
                        metadata.synced = true;
                        fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2));
                        synced++;
                    } catch (error) {
                        console.error(`Failed to sync ${file}:`, error);
                    }
                }
            }
        }

        return synced;
    }
}