# Deployment Guide: Extension Independence & Server Integration

## 🔍 Architecture Overview

The Gemini Documentation Manager VS Code extension is designed with **graceful degradation** - it provides maximum value even without any server components.

### ✅ **Works Completely Standalone** (No Server Needed)
- **📊 Documentation Status Tracking** - Analyzes local markdown files
- **📋 Epic & Story Management** - Reads/creates local epic/story files  
- **📁 File Organization** - Tree views of local documentation
- **✏️ Document Templates** - Creates new epics/stories with templates
- **🔄 Progress Calculation** - Calculates completion percentages from file content
- **⚙️ Configuration** - All VS Code settings work independently

### ❓ **Partially Dependent** (Graceful Degradation)
- **🔍 RAG Datastore Panel** - Shows "getting started" UI when server unavailable
- **📤 Document Upload** - Falls back to local storage when server offline
- **🔍 Knowledge Base Search** - Shows "server offline" message gracefully

### 🖥️ **Requires Gemini CLI Server** (Optional Advanced Features)
- **RAG Document Management** - Full upload/search/indexing capabilities
- **Vertex AI Search Integration** - Advanced semantic search
- **Agent Integration** - Access to AI personas (Analyst, Architect, etc.)
- **Real-time Document Processing** - Advanced document analysis

## 🚀 Deployment Options

### **Option 1: Extension Only** (Recommended for Most Projects)
Perfect for teams that just want documentation management:

```bash
# Just install the extension
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli/packages/vscode-extension
./install.sh
```

**✅ You Get:**
- Documentation status tracking with completion percentages
- Epic/story management with visual indicators
- Progress visualization across documentation categories
- Document templates for consistent formatting
- File organization and quick navigation
- All configuration options for different project structures

**❌ You Don't Get:**
- RAG-powered search capabilities
- AI agent interactions
- Advanced document processing

**Perfect For:**
- Open source projects
- Small to medium teams
- Projects focused on documentation organization
- Teams wanting zero server dependencies

### **Option 2: Extension + RAG Server** (Knowledge Management)
For teams wanting AI-powered knowledge management:

```bash
# Install extension + start RAG server
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli/packages/vscode-extension
./install.sh

# Start the RAG server (runs on port 2000)
cd ../../
./start_server_with_cloud.sh
```

**✅ You Get (Everything from Option 1 Plus):**
- RAG document upload and indexing
- Semantic search across your knowledge base
- Document content analysis and categorization
- Batch document processing
- URL-based content ingestion
- Vertex AI Search integration (if configured)

**Perfect For:**
- Teams with large documentation sets
- Projects needing advanced search capabilities
- Organizations wanting knowledge management
- Teams comfortable running one server process

### **Option 3: Full Gemini CLI** (Enterprise Development Environment)
Complete AI-powered development environment:

```bash
# Full installation with all agents and services
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli
npm install
pip install -r requirements.txt
./start_server.sh

# Install extension separately
cd packages/vscode-extension
./install.sh
```

**✅ You Get (Everything from Options 1 & 2 Plus):**
- AI agents: Enhanced Analyst, PM, Architect, Developer, QA, Scout, PO
- Advanced GCAR methodology support
- WebSocket-based real-time agent communication
- Business analysis and architecture capabilities
- Enterprise documentation workflows
- Full integration with Gemini CLI ecosystem

**Perfect For:**
- Enterprise development teams
- Complex projects requiring AI assistance
- Organizations following GCAR methodology
- Teams wanting full automation capabilities

## 🔧 Server Architecture Details

### Gemini CLI Server Components

The server (`src/api/agent_server.py`) provides:

**Core Services:**
- **FastAPI REST API** - HTTP endpoints for all services
- **WebSocket Support** - Real-time communication with agents
- **CORS Configuration** - Cross-origin support for web interfaces

**AI Agents Available:**
- **Enhanced Analyst** - Business analysis and requirements
- **Enhanced PM** - Project management and planning
- **Enhanced Architect** - System architecture and design
- **Enhanced Developer** - Code analysis and development
- **Enhanced QA** - Quality assurance and testing
- **Enhanced Scout** - Code exploration and indexing
- **Enhanced PO** - Product ownership and strategy

**RAG Integration:**
- **Document Management** - Upload, index, and search documents
- **Vertex AI Search** - Advanced semantic search capabilities
- **Content Analysis** - Automatic categorization and tagging
- **Multi-format Support** - Markdown, code files, documentation

### RAG Server Endpoints

The extension connects to these server endpoints:

```
GET  /api/rag/documents        - List all documents
POST /api/rag/upload           - Upload new documents
POST /api/rag/search           - Search knowledge base
GET  /api/rag/documents/{id}   - Get specific document
DELETE /api/rag/documents/{id} - Delete document
POST /api/rag/reindex          - Rebuild search index
GET  /status                   - Server health check
```

## 🎯 Configuration for Different Deployments

### Standalone Configuration
For extension-only deployment:

```json
{
  "gemini.documentationStructure": "custom",
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true
}
```

### RAG-Enabled Configuration
For extension + RAG server:

```json
{
  "gemini.documentationStructure": "gcar",
  "gemini.documentationPath": "docs", 
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true,
  "gemini.refreshInterval": 30000
}
```

### Enterprise Configuration
For full Gemini CLI deployment:

```json
{
  "gemini.documentationStructure": "gcar",
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true,
  "gemini.refreshInterval": 10000,
  "gemini.customCategories": [
    {"name": "Business Case", "path": "docs/0_business_case", "icon": "💼"},
    {"name": "Architecture", "path": "docs/2_architecture", "icon": "🏗️"}
  ]
}
```

## 🛟 Troubleshooting by Deployment Type

### Extension Only Issues
- **No data in tree views**: Check folder structure and configuration
- **Commands not working**: Reload VS Code, verify installation
- **Settings ignored**: Check VS Code settings syntax

### RAG Server Issues  
- **Connection failed**: Verify server is running on configured port
- **Upload failing**: Check server logs, verify permissions
- **Search not working**: Ensure documents are indexed

### Full Gemini CLI Issues
- **Agents not responding**: Check WebSocket connections
- **Performance problems**: Review server resource usage
- **Integration failures**: Verify all services are running

## 📊 Resource Requirements

### Extension Only
- **CPU**: Negligible
- **Memory**: < 50MB
- **Storage**: < 5MB
- **Network**: None

### Extension + RAG Server
- **CPU**: 1-2 cores recommended
- **Memory**: 1-4GB depending on document volume
- **Storage**: 100MB-10GB for document index
- **Network**: Local network only

### Full Gemini CLI
- **CPU**: 4+ cores recommended
- **Memory**: 4-16GB depending on workload
- **Storage**: 1-50GB for all services and data
- **Network**: Internet access for Vertex AI integration

## 🔒 Security Considerations

### Extension Only
- **Risk Level**: Very Low
- **Data Flow**: Local files only
- **Network**: No network activity
- **Permissions**: File system read/write only

### Extension + RAG Server
- **Risk Level**: Low to Medium
- **Data Flow**: Local network communication
- **Network**: HTTP traffic to localhost:2000
- **Permissions**: File system + network access

### Full Gemini CLI
- **Risk Level**: Medium to High (depending on configuration)
- **Data Flow**: Potential cloud service integration
- **Network**: Internet access for AI services
- **Permissions**: Full system access for agents

## 🚀 Migration Paths

### Upgrading from Extension Only → RAG Enabled
1. Install Python dependencies
2. Start RAG server: `./start_server_with_cloud.sh`
3. Existing extension automatically detects server
4. Documents remain unchanged

### Upgrading from RAG Enabled → Full Gemini CLI
1. Install full dependencies: `npm install && pip install -r requirements.txt`
2. Start full server: `./start_server.sh`  
3. All existing data and configuration preserved
4. Additional agent capabilities become available

### Downgrading
- **Full → RAG Only**: Stop full server, start RAG server only
- **RAG → Extension Only**: Stop server, extension continues working
- **No data loss** in any downgrade scenario

This deployment flexibility ensures the extension provides value at every level while allowing teams to scale up their capabilities as needed.