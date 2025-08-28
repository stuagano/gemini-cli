# 📜 Scripts Guide - Which Script to Use?

## 🚀 Quick Start for New Team Members

### Primary Scripts (Use These!)

1. **`./start_server.sh`** - Start the BMAD agent server
   - ✅ This is what you need to run the agents
   - Starts on port 2000
   - All 7 agents (analyst, pm, architect, developer, qa, scout, po)
   - Automatically restarts on code changes (hot reload)
   - Shows real-time logs from all agents

2. **`./setup-enterprise.sh`** - Initial setup for enterprise features
   - Run this ONCE when you first clone the repo
   - **What it does:**
     - ✅ Checks prerequisites (Node.js, Python 3)
     - ✅ Creates Python virtual environment
     - ✅ Installs all Python dependencies (FastAPI, Vertex AI, etc.)
     - ✅ Installs Node.js dependencies
     - ✅ Verifies .env configuration exists
     - ✅ Tests agent server can start
     - ✅ Tests Vertex AI connection
     - ✅ Creates CLI integration files
   - **Prerequisites needed:**
     - `.env` file with Google Cloud credentials
     - Node.js v20+
     - Python 3.9+

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
├── start_server.sh          ✅ Main script to run agents
├── setup-enterprise.sh      ✅ Initial setup script
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

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your Google Cloud credentials:
# - GOOGLE_CLOUD_PROJECT=your-project-id
# - GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
# - VERTEX_AI_LOCATION=us-central1

# 3. Run setup (installs dependencies, tests connections)
./setup-enterprise.sh    

# 4. Start the agent server
./start_server.sh        
```

### Daily Development:
```bash
./start_server.sh        # That's it!
```

## 🌐 Vertex AI & RAG Datastore Setup

### What's Included:
The system uses **Vertex AI** for embedding models and **local FAISS** for vector storage:

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

### Environment Variables Required:
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

### If `start_server.sh` fails:
1. Check Python virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 2000: `lsof -i :2000`

### If agents aren't responding:
1. Check health: `curl http://localhost:2000/api/v1/health`
2. Check logs in terminal where you ran `start_server.sh`
3. Restart the server: `Ctrl+C` then `./start_server.sh`

## 📝 Notes

- The main Gemini CLI (`gemini` command) works independently of the agent server
- Agent server provides specialized AI agents for enterprise features
- VS Code extension connects to the agent server automatically
- Docker setup is optional and not required for local development