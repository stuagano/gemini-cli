# Gemini Documentation & Project Manager

A flexible VS Code extension for managing documentation, epics/stories, and RAG (Retrieval-Augmented Generation) integration. Works with any project structure!

## ✨ Features

### 📊 Documentation Status Tracking
- **Multiple Structures**: GCAR methodology, flat structure, or custom categories
- **Progress Visualization**: Shows completion percentages for each documentation category  
- **Smart Analysis**: Analyzes document content to determine completeness
- **Quick Actions**: Open, edit, and upload documents directly from the tree view

### 📋 Epic & Story Management
- **Project Tracking**: View and manage epics and stories
- **Status Indicators**: Visual indicators for todo, in-progress, and completed items
- **Template Generation**: Create new epics and stories with predefined templates
- **Progress Tracking**: Automatic calculation of epic completion based on story status

### 🔍 RAG Datastore Integration  
- **Knowledge Base Management**: Upload and manage documents in your RAG datastore
- **Multi-format Support**: Markdown, code, and documentation files
- **Search Interface**: Search through your indexed knowledge base
- **Batch Operations**: Upload entire folders or individual files

## 🚀 Quick Install

```bash
git clone <this-extension>
cd vscode-extension
./install.sh
```

That's it! Reload VS Code and look for the 📖 Gemini Manager panel.

## ⚙️ Configuration

Configure for your project structure:

### 1. GCAR Structure (Default)
Perfect for enterprise projects following GCAR methodology:

```json
{
  "gemini.documentationStructure": "gcar",
  "gemini.documentationPath": "docs"
}
```

Expected structure:
```
docs/
├── 0_business_case/
├── 1_product/  
├── 2_architecture/
├── 3_manuals/
├── 4_quality/
├── 5_project_management/
└── tasks/
    ├── epic-*.md
    └── story-*.md
```

### 2. Flat Structure
For simple projects with all docs in one folder:

```json
{
  "gemini.documentationStructure": "flat",
  "gemini.documentationPath": "docs"
}
```

Expected structure:
```
docs/
├── *.md (all documentation files)
└── tasks/
    ├── epic-*.md
    └── story-*.md
```

### 3. Custom Structure
Define your own categories:

```json
{
  "gemini.documentationStructure": "custom",
  "gemini.customCategories": [
    {"name": "Requirements", "path": "docs/requirements", "icon": "📋"},
    {"name": "Design", "path": "docs/design", "icon": "🎨"},
    {"name": "API Docs", "path": "docs/api", "icon": "🔌"},
    {"name": "Guides", "path": "docs/guides", "icon": "📚"}
  ]
}
```

### Other Settings
```json
{
  "gemini.epicsPath": "docs/tasks",           // Path to epics/stories
  "gemini.ragServerUrl": "http://localhost:2000", // RAG server URL
  "gemini.autoRefresh": true,                 // Auto-refresh tree views
  "gemini.refreshInterval": 30000             // Refresh every 30 seconds
}
```

## 📁 Adapting to Your Project

### Existing Project with Different Structure?

**Option 1: Use Custom Categories**
```json
{
  "gemini.documentationStructure": "custom",
  "gemini.customCategories": [
    {"name": "README", "path": ".", "icon": "📖"},
    {"name": "Docs", "path": "documentation", "icon": "📚"},
    {"name": "Specs", "path": "specs", "icon": "📋"}
  ]
}
```

**Option 2: Use Flat Structure**
```json
{
  "gemini.documentationStructure": "flat",
  "gemini.documentationPath": "."
}
```

**Option 3: Create Symbolic Links**
```bash
# Link your existing docs to expected structure
ln -s existing-docs docs
ln -s project-tasks docs/tasks
```

### No Epic/Story Files?
The extension works fine without them! The Epic & Story panel will just show an empty state.

To add epic/story tracking:
1. Create a `docs/tasks/` folder (or configure `gemini.epicsPath`)
2. Add files like `epic-user-auth.md` and `story-001-login.md`
3. Use the "Create Epic" and "Create Story" commands for templates

## 🔧 Available Commands

**Documentation:**
- `gemini.refreshDocStatus` - Refresh documentation status
- `gemini.openDocument` - Open document 
- `gemini.editDocument` - Edit/create document

**Epics & Stories:**
- `gemini.createEpic` - Create new epic
- `gemini.createStory` - Create new story  
- `gemini.markStoryComplete` - Mark story complete

**RAG Integration:**
- `gemini.uploadFileToRAG` - Upload single file
- `gemini.uploadFolderToRAG` - Upload folder
- `gemini.searchRAG` - Search knowledge base
- `gemini.checkRAGServer` - Check server status

## 🤖 RAG Server (Optional)

The RAG integration is completely optional. If you don't have a RAG server:
- The RAG panel will show helpful getting-started info
- All other features work normally
- No errors or warnings

To enable RAG features, ensure your server provides:
- `GET /documents` - List documents
- `POST /upload` - Upload documents  
- `GET /search?q=query` - Search
- `GET /status` - Server status

## 🚀 Installation for Other Projects

### Method 1: Copy Extension Files
```bash
# Copy the extension to your new project
cp -r path/to/vscode-extension ./tools/vscode-extension
cd tools/vscode-extension
./install.sh
```

### Method 2: Package and Distribute
```bash
# Package the extension
npm run package
# Copy the .vsix file to other projects
cp gemini-docs-manager-1.0.0.vsix /path/to/other/project/
# Install on the other project
cd /path/to/other/project
code --install-extension gemini-docs-manager-1.0.0.vsix
```

### Method 3: VS Code Marketplace (Future)
This extension could be published to the VS Code Marketplace for easy installation across projects.

## 🛠️ Customization

The extension is designed for easy customization:

**Document Templates**: Edit `src/commands/index.ts` to modify epic/story templates
**Document Analysis**: Modify `src/services/DocumentationService.ts` for custom document requirements  
**Tree Providers**: Extend providers in `src/providers/` for additional data sources
**RAG Integration**: Adapt `src/services/RAGService.ts` for different RAG implementations

## 📞 Troubleshooting

**Extension not showing?**
- Reload VS Code (Cmd+R)
- Check Activity Bar for 📖 Gemini Manager icon
- Verify extension is installed: `code --list-extensions`

**No data in tree views?**
- Check your folder structure matches configuration
- Use refresh buttons in tree view headers
- Verify paths in settings

**RAG features not working?**
- RAG server is optional - other features work without it
- Check server URL in settings
- Use "Check RAG Server Status" command

## 🎯 Perfect For

- ✅ Enterprise projects with structured documentation
- ✅ Open source projects needing documentation tracking
- ✅ Teams using epic/story methodology
- ✅ Projects with knowledge management needs
- ✅ Any project wanting better documentation visibility

Works with any folder structure - just configure it for your needs!