# 📜 Scripts Guide - Which Script to Use?

> **New to Agents?** Read [What Are Agents?](docs/WHAT_ARE_AGENTS.md) first to understand what agents are and how they work.

## 🚀 Quick Start for New Team Members

### Primary Scripts (Use These!)

1. **`./start_agent_server.sh`** - Start the BMAD agent server
   - ✅ This is what you need to run the agents
   - Starts on port 2000
   - All 7 agents (analyst, pm, architect, developer, qa, scout, po)
   - Automatically restarts on code changes (hot reload)
   - Shows real-time logs from all agents

2. **`./setup-enterprise.sh`** - Initial setup (NO GCP REQUIRED!)
   - Run this ONCE when you first clone the repo
   - **What it does:**
     - ✅ Checks prerequisites (Node.js, Python 3)
     - ✅ Creates Python virtual environment
     - ✅ Installs all Python dependencies
     - ✅ Installs Node.js dependencies
     - ✅ Creates .env file from template
     - ✅ Tests agent server can start
     - ✅ Tests Vertex AI (if configured, otherwise skips)
     - ✅ Creates CLI integration files
   - **Only requires:**
     - Node.js v20+
     - Python 3.9+
   - **GCP is OPTIONAL** - agents work fine without it!

### Secondary Scripts (Special Cases)

3. **`scripts/sync-upstream.sh`** - Sync with upstream Gemini CLI
   - Only use if you need to pull updates from google-gemini/gemini-cli
   - Preserves all enterprise customizations

4. **`monitoring/deployment/quick-deploy.sh`** - Deploy monitoring stack
   - Only if you need Grafana/Prometheus monitoring
   - Optional for local development

## ⚠️ Scripts to Avoid (Confusing/Legacy)

### Don't Use These:
- ❌ `install-gemini.sh` - Legacy installer, use `setup-enterprise.sh` instead
- ❌ `scripts/deploy-cloud.sh` - For cloud deployment only
- ❌ `scripts/create_alias.sh` - Not needed
- ❌ `docker/scripts/dev-*.sh` - Only if using Docker setup
- ❌ `packages/vscode-extension/*.sh` - Internal build scripts

## 📁 Script Directory Structure

```
gemini-cli/
├── start_agent_server.sh    ✅ Main script to run agents
├── setup-enterprise.sh      ✅ Initial setup script (no GCP required)
├── scripts/
│   ├── sync-upstream.sh    ⚙️ Sync with upstream
│   └── [other scripts]      ❌ Internal/build scripts
├── docker/scripts/          🐳 Docker-only scripts
└── monitoring/deployment/   📊 Monitoring setup (optional)
```

## 🎯 Typical Workflow

### First Time Setup:
```bash
# 1. Clone the repository
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli

# 2. Run setup (creates .env, installs dependencies)
./setup-enterprise.sh    

# 3. Start the agent server
./start_agent_server.sh

# 4. (OPTIONAL) Add Google Cloud later if needed:
# Edit .env and add:
# - GOOGLE_CLOUD_PROJECT=your-project-id
# - GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json        
```

### Daily Development:
```bash
./start_agent_server.sh  # That's it!
```

## 🌐 OPTIONAL: Vertex AI & Enhanced RAG Setup

### Basic Mode (No GCP Required):
- ✅ All 7 agents work perfectly
- ✅ Local document storage and search
- ✅ Code analysis and duplication detection
- ✅ Full API functionality

### Enhanced Mode (With GCP - Optional):
If you have Google Cloud access, you can enable:

1. **Embedding Models** (via Vertex AI):
   - `text-embedding-004` for document embeddings
   - `gemini-1.5-pro` for chat/completion

2. **Vector Storage** (Local):
   - FAISS index stored in `src/knowledge/data/`
   - Automatic indexing of project documentation
   - Scout agent indexes codebase for duplicate detection

3. **RAG System Components**:
   - Document ingestion pipeline
   - Vector similarity search
   - Knowledge base querying
   - Real-time document updates

### Vertex AI Configuration:
The `scripts/setup-vertex-ai.py` script (called by setup-enterprise.sh) handles:
- Validating Google Cloud credentials
- Testing Vertex AI API access
- Configuring embedding endpoints
- Setting up model deployments

### Environment Variables (OPTIONAL for GCP):
```bash
# Google Cloud / Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_LOCATION=us-central1

# Optional: Override default models
EMBEDDING_MODEL=text-embedding-004
CHAT_MODEL=gemini-1.5-pro
```

### RAG Datastore Endpoints:
Once running, the RAG system provides:
- `POST /api/v1/knowledge/query` - Query the knowledge base
- `POST /api/v1/knowledge/documents` - Add new documents
- `GET /api/v1/knowledge/search` - Search documents
- `POST /api/v1/knowledge/reindex` - Rebuild the index
- `GET /api/v1/knowledge/stats` - Get datastore statistics

### API Endpoints:
- Health Check: http://localhost:2000/api/v1/health
- API Docs: http://localhost:2000/docs
- WebSocket: ws://localhost:2000/ws

## 🔧 Troubleshooting

### If `start_agent_server.sh` fails:
1. Check Python virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 2000: `lsof -i :2000`

### If agents aren't responding:
1. Check health: `curl http://localhost:2000/api/v1/health`
2. Check logs in terminal where you ran `start_server.sh`
3. Restart the server: `Ctrl+C` then `./start_agent_server.sh`

## 📝 Notes

- The main Gemini CLI (`gemini` command) works independently of the agent server
- Agent server provides specialized AI agents for enterprise features
- VS Code extension connects to the agent server automatically
- Docker setup is optional and not required for local development