# Gemini CLI with Enterprise AI Agent Team

[![Gemini CLI CI](https://github.com/google-gemini/gemini-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/google-gemini/gemini-cli/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/google-gemini/gemini-cli)](https://github.com/google-gemini/gemini-cli/blob/main/LICENSE)

## 🎯 What is This?

**A fork of Google's Gemini CLI that adds a team of 7 specialized AI agents that work like real software developers.**

Instead of one general AI assistant, you get an entire development team where each agent is an expert in their domain.

## 🤖 The AI Agent Team

| Agent | Role | What They Do |
|-------|------|--------------|
| **🎯 Analyst** | Business Analyst | Translates requirements to technical specs, creates user stories |
| **📋 PM** | Project Manager | Creates project plans, estimates effort, tracks progress |
| **🏗️ Architect** | System Architect | Designs architecture, chooses tech stacks, ensures scalability |
| **💻 Developer** | Software Engineer | Writes production code with tests and error handling |
| **🧪 QA** | Quality Assurance | Creates test suites, finds edge cases, ensures quality |
| **🔍 Scout** | Code Analyst | Prevents duplicates by finding existing implementations |
| **🎨 PO** | Product Owner | Prioritizes features, manages backlog, aligns with business |

## 🤔 Why This Exists

### The Problem
Generic AI gives generic answers. Ask ChatGPT to "build an auth system" and you get a messy mix of architecture advice, code snippets, and maybe some tests - all jumbled together.

### The Solution  
Specialized agents that maintain consistent expertise and perspective. Each agent thinks and responds like a real team member would.

### Example: "Build user authentication"

**Generic AI Response:**
```
Here's a basic JWT auth implementation... [random code]
```

**Our Agent Team Response:**
- **Analyst**: "Requirements: OAuth 2.0, MFA, password policies, session management"
- **Architect**: "Design: JWT + Redis sessions, bcrypt, rate limiting"  
- **Scout**: "Found existing JWT middleware in src/auth/jwt.ts to reuse"
- **Developer**: *Implements production code with proper error handling*
- **QA**: "Created 47 test cases covering auth flows and edge cases"

## 🚀 Quick Start (No Cloud Required!)

```bash
# 1. Clone and setup
git clone https://github.com/stuagano/gemini-cli.git
cd gemini-cli
./setup-enterprise.sh    # Installs dependencies

# 2. Start the agent team
./start_agent_server.sh  # Runs on http://localhost:2000

# 3. Talk to an agent
curl -X POST http://localhost:2000/api/v1/agent/request \
  -H "Content-Type: application/json" \
  -d '{"agent": "architect", "prompt": "Design a REST API for todos"}'
```

## 📚 Learn More

- **[What Are AI Agents?](docs/WHAT_ARE_AGENTS.md)** - Complete explanation
- **[Scripts Guide](SCRIPTS_GUIDE.md)** - Which scripts to use
- **[API Documentation](http://localhost:2000/docs)** - Interactive API docs (when running)

## 🔑 Key Features

### This Fork Adds
- ✅ **7 Specialized Agents** - Complete dev team simulation
- ✅ **No Cloud Required** - Works locally out of the box
- ✅ **Production Code** - Agents write real code, not examples
- ✅ **Scout Prevention** - Finds existing code before writing new
- ✅ **Killer Demo** - Detects N+1 queries, memory leaks, O(n²) algorithms

### From Base Gemini CLI
- ✅ **Terminal First** - Built for developers
- ✅ **Google Search** - Web grounding capabilities
- ✅ **File Operations** - Read, write, edit files
- ✅ **Shell Commands** - Execute system commands
- ✅ **MCP Support** - Extensible with custom tools

## 🛠️ Architecture

```
Your Request
     ↓
Agent Server (FastAPI on port 2000)
     ↓
Router (Selects appropriate agent)
     ↓
Specialized Agent (1 of 7)
     ↓
Structured Response
```

## 🌟 Optional Enhancements

If you have Google Cloud access, you can enable:
- **Vertex AI** - Enhanced embeddings for better code search
- **Cloud Storage** - Persistent knowledge base
- **Advanced RAG** - Better context retrieval

But these are **completely optional** - the agents work great without them!

## 📖 Documentation

- [Full Documentation](docs/)
- [Agent API Reference](docs/2_architecture/api-specification.md)
- [Architecture Overview](docs/2_architecture/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! The agent system is designed to be extensible:
- Add new agents by extending `UnifiedAgent` base class
- Add new tools in the agent toolkit
- Improve agent prompts and behaviors

## 📄 License

Apache 2.0 - Same as the original Gemini CLI

---

**Note**: This is a community fork that extends Google's Gemini CLI with enterprise features. The base Gemini CLI is maintained by Google.