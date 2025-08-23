# 📚 VS Code Extension Integration Guide

## Overview
The Gemini Documentation Manager is a comprehensive VS Code extension that integrates seamlessly with the Gemini CLI ecosystem, providing visual documentation management, project tracking, and AI-powered knowledge base capabilities.

## 🚀 Quick Start (2 Minutes)

### Fastest Installation
```bash
# From gemini-cli root directory
./scripts/install-vscode-extension.sh
```

**That's it!** The script handles everything automatically.

### What Gets Installed
- ✅ VS Code extension with all features
- ✅ Documentation status tracking
- ✅ Epics & stories management
- ✅ RAG datastore integration
- ✅ Rich dashboard
- ✅ Auto-configured settings

## 📂 File Locations

```
gemini-cli/
├── packages/
│   └── vscode-extension/          # Extension source code
│       ├── src/                   # TypeScript source
│       ├── package.json          # Extension manifest
│       ├── README.md             # Full documentation
│       ├── QUICK_START.md        # Quick start guide
│       ├── FEATURES.md           # Feature details
│       └── VISUAL_GUIDE.md       # Visual walkthrough
├── scripts/
│   └── install-vscode-extension.sh  # One-click installer
└── docs/
    ├── tasks/                     # Your epics and stories
    └── 0-5_*/                    # Documentation categories
```

## 🎯 Key Features

### 1. Documentation Status Panel
Tracks documentation completion across 6 categories:
- Business Case
- Product
- Architecture  
- Manuals
- Quality
- Project Management

**Visual Indicators:**
- ✅ Complete (green)
- 🔄 In Progress (yellow)
- ⚠️ Not Started (red)
- Percentage completion shown

### 2. Epics & Stories Management
- Hierarchical view of project tasks
- One-click story completion
- Automatic progress calculation
- Template generation for new items

### 3. RAG Datastore Integration
- Upload documents for AI search
- Bulk folder uploads
- Full-text semantic search
- Offline support with sync

### 4. Rich Dashboard
- Comprehensive metrics overview
- Quick action buttons
- Auto-refresh every 30 seconds
- Visual progress bars

## 🔧 Configuration

### Automatic Configuration
The installer configures everything, but you can customize:

```json
// .vscode/settings.json
{
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true,
  "gemini.refreshInterval": 30000
}
```

### Manual Configuration
1. Open VS Code Settings: `Cmd/Ctrl + ,`
2. Search for "Gemini"
3. Adjust paths and URLs as needed

## 💡 Usage Scenarios

### Scenario 1: Starting a New Project
1. Run installer: `./scripts/install-vscode-extension.sh`
2. Open VS Code
3. Click Gemini Manager icon
4. Create first epic with + button
5. Add stories to epic
6. Track progress visually

### Scenario 2: Document Your Code
1. Right-click in Documentation Status
2. Select "Edit Document"
3. Choose template (Architecture, API, etc.)
4. Fill in sections
5. Save to auto-update progress

### Scenario 3: Build Knowledge Base
1. Select your docs folder
2. Right-click → "Upload Folder to RAG"
3. Wait for indexing
4. Use search to find anything instantly

### Scenario 4: Track Team Progress
1. Open dashboard: `Cmd/Ctrl + Shift + P` → "Show Dashboard"
2. View real-time metrics
3. See completion percentages
4. Monitor documentation coverage

## ⌨️ Keyboard Shortcuts

| Action | Shortcut | Description |
|--------|----------|-------------|
| Show Dashboard | `Cmd/Ctrl + Shift + D` | Open metrics dashboard |
| Refresh All | `Cmd/Ctrl + Shift + R` | Refresh all views |
| Upload to RAG | `Cmd/Ctrl + Shift + U` | Upload current file |
| Command Palette | `Cmd/Ctrl + Shift + P` | Access all commands |

## 🔌 Integration with Gemini CLI

### RAG Server Connection
The extension integrates with the Gemini CLI's RAG server:

```bash
# Start RAG server (if using)
cd src
python start_server.py
```

### Document Structure
Follows Gemini CLI's documentation structure:
- GCAR methodology categories
- Epic/story format
- Markdown-based documentation

### Shared Configuration
Uses same paths and structure as CLI:
- `docs/` for documentation
- `docs/tasks/` for epics/stories
- `.vscode/` for settings

## 🚨 Troubleshooting

### Extension Not Showing?
```bash
# Reload VS Code
Cmd/Ctrl + Shift + P → "Developer: Reload Window"
```

### Views Empty?
```bash
# Ensure workspace is open
File → Open Folder → [your-project]
```

### Can't Install?
```bash
# Check prerequisites
node --version  # Should be 18+
code --version  # VS Code should be installed

# Try manual install
cd packages/vscode-extension
npm install
npm run compile
```

### RAG Upload Fails?
- Check server is running: `http://localhost:2000/health`
- Extension works offline (auto-syncs later)
- Check upload queue in RAG view

## 📊 Metrics & Reporting

### What Gets Tracked
- Document completion status
- Word counts
- Epic/story progress
- RAG indexing status
- Upload queue

### Dashboard Metrics
- Total documents
- Completion percentage
- Average document size
- RAG coverage
- Category breakdowns

## 🎨 Customization

### Templates
Located in `DocumentationService.ts`:
- Business Case
- Architecture
- API Specification
- PRD
- Testing Strategy

### Adding Custom Categories
Edit `DocumentationProvider.ts`:
```typescript
const categories = [
  { name: 'Custom', path: 'docs/custom', icon: '🎯' },
  // Add your categories
];
```

### Theme Support
Extension adapts to VS Code theme:
- Light themes
- Dark themes
- High contrast

## 📚 Documentation Links

### Extension Documentation
- [README](packages/vscode-extension/README.md) - Full documentation
- [Quick Start](packages/vscode-extension/QUICK_START.md) - 2-minute guide
- [Features](packages/vscode-extension/FEATURES.md) - Detailed features
- [Visual Guide](packages/vscode-extension/VISUAL_GUIDE.md) - Screenshots

### Related Documentation
- [Main README](README.md) - Gemini CLI overview
- [Enterprise Docs](docs/README.md) - Enterprise features
- [API Documentation](src/api/README.md) - API reference

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone [repo]
cd gemini-cli/packages/vscode-extension

# Install and test
npm install
npm run compile
npm test

# Open in VS Code
code .
# Press F5 to test
```

### Building for Distribution
```bash
# Create VSIX package
./build.sh

# Package will be created as:
# gemini-docs-manager-1.0.0.vsix
```

## 🆘 Support

### Getting Help
- **Quick Start**: Run `./scripts/install-vscode-extension.sh`
- **Issues**: [GitHub Issues](https://github.com/google-gemini/gemini-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/google-gemini/gemini-cli/discussions)

### Common Questions

**Q: Do I need the RAG server running?**
A: No, the extension works offline and syncs when available.

**Q: Can I use different folder structures?**
A: Yes, configure paths in settings.

**Q: How do I update the extension?**
A: Run the installer again or use `code --install-extension` with new .vsix

**Q: Can multiple team members use this?**
A: Yes, each team member installs the extension locally.

## 🎯 Next Steps

1. **Install Now**: `./scripts/install-vscode-extension.sh`
2. **Open Dashboard**: See your documentation status
3. **Create First Epic**: Start tracking a feature
4. **Upload Docs**: Build your knowledge base
5. **Share with Team**: Everyone gets visibility

---

**Ready to supercharge your documentation workflow? Install in 2 minutes!** 🚀