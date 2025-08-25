import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';

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
        let rawUrl = config.get<string>('ragServerUrl') || 'http://localhost:2000';
        
        // Clean and validate URL
        rawUrl = rawUrl.trim().replace(/[.\s]+$/, '');
        
        try {
            new URL(rawUrl); // Validate URL format
            this.serverUrl = rawUrl;
        } catch (error) {
            console.warn(`Invalid RAG server URL: ${rawUrl}, using default`);
            this.serverUrl = 'http://localhost:2000';
        }
    }

    private getCleanServerUrl(): string {
        return this.serverUrl.replace(/[.\s]+$/, '');
    }

    private async httpRequest(url: string, options: {
        method?: string;
        headers?: Record<string, string>;
        body?: string;
        timeout?: number;
    } = {}): Promise<{ status: number; data: any; headers: Record<string, string> }> {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            const isHttps = urlObj.protocol === 'https:';
            const lib = isHttps ? https : http;
            
            const requestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port || (isHttps ? 443 : 80),
                path: urlObj.pathname + urlObj.search,
                method: options.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'VS Code Extension',
                    ...options.headers
                },
                timeout: options.timeout || 5000
            };

            const req = lib.request(requestOptions, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const parsedData = data ? JSON.parse(data) : null;
                        resolve({
                            status: res.statusCode || 0,
                            data: parsedData,
                            headers: res.headers as Record<string, string>
                        });
                    } catch (error) {
                        resolve({
                            status: res.statusCode || 0,
                            data: data, // Return raw data if JSON parsing fails
                            headers: res.headers as Record<string, string>
                        });
                    }
                });
            });

            req.on('error', reject);
            req.on('timeout', () => reject(new Error('Request timeout')));

            if (options.body) {
                req.write(options.body);
            }

            req.end();
        });
    }

    async getDocuments(): Promise<RAGDocument[]> {
        try {
            const cleanUrl = this.getCleanServerUrl();
            console.log(`RAGService: Fetching documents from ${cleanUrl}/api/rag/documents`);
            const response = await this.httpRequest(`${cleanUrl}/api/rag/documents`, {
                timeout: 5000
            });
            console.log('RAGService: Response received:', response.data);
            if (response.status === 200 && response.data && response.data.documents) {
                return response.data.documents;
            }
            // Return empty array if no valid response
            console.log('RAGService: No documents found');
            return [];
        } catch (error: any) {
            console.log('RAGService: Server not available');
            // Return empty array - let the UI handle the empty state
            return [];
        }
    }

    async uploadDocument(filePath: string): Promise<void> {
        const content = fs.readFileSync(filePath, 'utf8');
        const fileName = path.basename(filePath);
        const fileType = this.detectFileType(fileName);

        try {
            const cleanUrl = this.getCleanServerUrl();
            const body = JSON.stringify({
                name: fileName,
                content: content,
                type: fileType,
                path: filePath,
                metadata: {
                    uploadedBy: 'vscode-extension',
                    timestamp: new Date().toISOString()
                }
            });
            
            const response = await this.httpRequest(`${cleanUrl}/api/rag/upload`, {
                method: 'POST',
                body: body,
                headers: {
                    'Content-Type': 'application/json'
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

    async uploadFromUrl(url: string): Promise<void> {
        try {
            // First fetch the content from the URL
            const response = await this.httpRequest(url, {
                timeout: 30000,  // 30 second timeout for external URLs
                headers: {
                    'User-Agent': 'Mozilla/5.0 (compatible; Gemini RAG Uploader)'
                }
            });

            if (response.status !== 200) {
                throw new Error(`Failed to fetch URL: ${response.status}`);
            }

            const content = response.data;
            const urlObj = new URL(url);
            const fileName = urlObj.pathname.split('/').pop() || 'webpage.html';
            const fileType = this.detectFileType(fileName);

            // Now upload to RAG server
            const cleanUrl = this.getCleanServerUrl();
            const uploadBody = JSON.stringify({
                name: fileName,
                content: content,
                type: fileType,
                path: url,  // Use URL as the path
                metadata: {
                    uploadedBy: 'vscode-extension',
                    timestamp: new Date().toISOString(),
                    sourceUrl: url,
                    contentType: response.headers['content-type']
                }
            });
            
            const uploadResponse = await this.httpRequest(`${cleanUrl}/api/rag/upload`, {
                method: 'POST',
                body: uploadBody,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (uploadResponse.status !== 200 && uploadResponse.status !== 201) {
                throw new Error(`Upload failed with status ${uploadResponse.status}`);
            }
        } catch (error: any) {
            if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
                throw new Error(`Cannot reach URL: ${url}`);
            } else if (error.response?.status === 404) {
                throw new Error(`URL not found: ${url}`);
            } else {
                throw new Error(`Failed to upload from URL: ${error.message || error}`);
            }
        }
    }

    async searchDocuments(query: string, limit: number = 10): Promise<SearchResult[]> {
        try {
            const cleanUrl = this.getCleanServerUrl();
            const body = JSON.stringify({ query, limit });
            const response = await this.httpRequest(`${cleanUrl}/api/rag/search`, {
                method: 'POST',
                body: body,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            return response.data.results || [];
        } catch (error) {
            console.error('Search failed:', error);
            return [];
        }
    }

    async deleteDocument(documentId: string): Promise<void> {
        try {
            const cleanUrl = this.getCleanServerUrl();
            await this.httpRequest(`${cleanUrl}/api/rag/documents/${documentId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Failed to delete document:', error);
            throw error;
        }
    }

    async getDocumentContent(documentId: string): Promise<string> {
        try {
            const cleanUrl = this.getCleanServerUrl();
            const response = await this.httpRequest(`${cleanUrl}/api/rag/documents/${documentId}/content`);
            return response.data.content || '';
        } catch (error) {
            console.error('Failed to fetch document content:', error);
            return '';
        }
    }

    async reindexDocuments(): Promise<void> {
        try {
            const cleanUrl = this.getCleanServerUrl();
            await this.httpRequest(`${cleanUrl}/api/rag/reindex`, {
                method: 'POST'
            });
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
            const cleanUrl = this.getCleanServerUrl();
            const response = await this.httpRequest(`${cleanUrl}/health`, { timeout: 5000 });
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