# 🚀 Quick Start Guide - Gemini Documentation Manager

Get up and running with the Gemini Documentation Manager VS Code extension in under 2 minutes!

## 📦 One-Click Installation

### Option 1: Automatic Installer (Recommended)
```bash
# From the gemini-cli root directory
./scripts/install-vscode-extension.sh
```

This script will:
- ✅ Check for VS Code and Node.js
- ✅ Install dependencies
- ✅ Compile the extension
- ✅ Optionally package and install it
- ✅ Configure your settings

### Option 2: Manual Quick Install
```bash
# Navigate to extension directory
cd packages/vscode-extension

# Install and compile
npm install
npm run compile

# Open in VS Code
code .
# Then press F5 to test
```

### Option 3: Install Pre-built Package
```bash
# If you have a .vsix file
code --install-extension gemini-docs-manager-*.vsix
```

## 🎯 First Steps

### 1. Open the Extension
After installation, look for the **Gemini Manager** icon in the VS Code Activity Bar (left sidebar).

### 2. Explore the Three Main Views

#### 📊 Documentation Status
Shows your documentation progress:
- ✅ Green = Complete
- 🔄 Yellow = In Progress  
- ⚠️ Red = Not Started

#### 🎯 Epics & Stories
Track your project tasks:
- Click any epic to see its stories
- Right-click stories to mark complete
- Use + button to create new items

#### 🗄️ RAG Datastore
Manage your knowledge base:
- Upload documents for AI search
- View indexed documents
- Search across all content

### 3. Open the Dashboard
Press `Cmd/Ctrl + Shift + P` and type:
```
Gemini: Show Documentation Dashboard
```

## 🔧 Essential Configuration

### Basic Settings (Automatic)
The installer will ask for these, or add to `.vscode/settings.json`:

```json
{
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true
}
```

### Folder Structure Required
Ensure your project has this structure:
```
your-project/
├── docs/
│   ├── 0_business_case/
│   ├── 1_product/
│   ├── 2_architecture/
│   ├── 3_manuals/
│   ├── 4_quality/
│   ├── 5_project_management/
│   └── tasks/
│       ├── epic-*.md
│       └── story-*.md
```

## 💡 5 Most Useful Features

### 1. Create Document from Template
- Right-click in Documentation Status
- Select "Edit Document"
- Choose template type
- Auto-generates with required sections

### 2. Bulk Upload to RAG
- Right-click any folder in Explorer
- Select "Upload Folder to RAG"
- All markdown files uploaded automatically

### 3. Quick Story Completion
- In Epics & Stories view
- Click ✓ icon next to any story
- Automatically updates file and progress

### 4. Search Knowledge Base
- Click 🔍 in RAG Datastore toolbar
- Enter search query
- Get AI-powered results instantly

### 5. Live Dashboard
- Shows all metrics at a glance
- Quick action buttons
- Auto-refreshes every 30 seconds

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Show Dashboard | `Cmd/Ctrl + Shift + D` |
| Refresh All Views | `Cmd/Ctrl + Shift + R` |
| Upload Current File | `Cmd/Ctrl + Shift + U` |
| Command Palette | `Cmd/Ctrl + Shift + P` |

## 🎨 Common Workflows

### Starting a New Epic
1. Click + in Epics & Stories toolbar
2. Enter epic name
3. Template auto-generated
4. Start adding stories

### Documenting a Feature
1. Open Documentation Status
2. Right-click → Edit Document
3. Choose template
4. Fill in sections
5. Save → Auto-updates progress

### Building Knowledge Base
1. Select your docs folder
2. Right-click → Upload Folder to RAG
3. Wait for indexing
4. Use search to find content

## 🚨 Troubleshooting

### Extension Not Showing?
```bash
# Reload VS Code window
Cmd/Ctrl + Shift + P → "Developer: Reload Window"
```

### Views Empty?
```bash
# Check workspace folder is open
File → Open Folder → Select your project root
```

### RAG Upload Failing?
```bash
# Start local RAG server (if using)
cd src && python start_server.py

# Or use offline mode (auto-enabled)
```

### Can't Find Commands?
```bash
# Open command palette
Cmd/Ctrl + Shift + P
# Type "Gemini" to see all commands
```

## 📺 Video Walkthrough

[Coming Soon - 2-minute setup video]

## 🆘 Getting Help

### Quick Help
- Hover over any tree item for tooltips
- Check status bar for extension status
- View Output panel for logs

### Documentation
- Full README: `packages/vscode-extension/README.md`
- Features Guide: `packages/vscode-extension/FEATURES.md`
- API Docs: `src/api/README.md`

### Support
- GitHub Issues: [Report bugs](https://github.com/google-gemini/gemini-cli/issues)
- Discussions: [Ask questions](https://github.com/google-gemini/gemini-cli/discussions)

## 🎯 Next Steps

1. **Create your first epic**: Track a feature you're building
2. **Upload documentation**: Build your knowledge base
3. **Use the dashboard**: Monitor progress
4. **Create templates**: Standardize your docs
5. **Search everything**: Use RAG for instant answers

---

**Ready to boost your documentation productivity? Let's go!** 🚀