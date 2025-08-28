# 📜 Scripts Guide - Which Script to Use?

## 🚀 Quick Start for New Team Members

### Primary Scripts (Use These!)

1. **`./start_server.sh`** - Start the BMAD agent server
   - ✅ This is what you need to run the agents
   - Starts on port 2000
   - All 7 agents (analyst, pm, architect, developer, qa, scout, po)

2. **`./setup-enterprise.sh`** - Initial setup for enterprise features
   - Run this ONCE when you first clone the repo
   - Installs Python dependencies
   - Sets up virtual environment
   - Tests the setup

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
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli
./setup-enterprise.sh    # One-time setup
./start_server.sh        # Start the agents
```

### Daily Development:
```bash
./start_server.sh        # That's it!
```

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