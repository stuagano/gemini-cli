# Gemini Documentation & Project Manager VS Code Extension

A comprehensive VS Code extension for managing documentation, tracking epics/stories, and integrating with RAG (Retrieval-Augmented Generation) datastores.

## Features

### 📊 Documentation Status Panel
- **Real-time Progress Tracking**: Visual indicators showing documentation completion status
- **Category Organization**: Documents organized by business case, product, architecture, manuals, quality, and project management
- **Completion Metrics**: Percentage completion for each category
- **Word Count Tracking**: Monitor document size and content growth
- **Missing Requirements Detection**: Automatically identifies missing required sections

### 🎯 Epics & Stories Management
- **Hierarchical View**: Epics with nested stories
- **Status Tracking**: Visual indicators for not-started, in-progress, and completed items
- **Quick Creation**: Create new epics and stories from templates
- **Progress Calculation**: Automatic completion percentage based on story status
- **One-Click Status Updates**: Mark stories as complete with a single click

### 🗄️ RAG Datastore Integration
- **Document Upload**: Easy upload of markdown files to RAG datastore
- **Bulk Upload**: Upload entire folders with one command
- **Search Integration**: Search across all indexed documents
- **Upload Queue**: Visual tracking of pending uploads
- **Index Statistics**: Monitor indexed documents and chunk counts
- **Offline Support**: Local storage with automatic sync when server is available

### 📝 Markdown Editor Integration
- **Template Generation**: Pre-filled templates for common document types
- **Quick Edit**: Open and edit documents directly from the tree view
- **Validation**: Real-time validation of document completeness
- **Section Detection**: Automatic detection of document sections and structure

### 🎨 Rich Dashboard
- **Overview Statistics**: Total documents, completion rate, word count
- **Category Progress**: Visual progress bars for each documentation category
- **RAG Metrics**: Upload status, indexing progress, storage usage
- **Quick Actions**: One-click access to common tasks
- **Auto-Refresh**: Configurable automatic refresh intervals

## 🚀 Getting Started

### Quick Install (Recommended)
```bash
# One-click installation from gemini-cli root
./scripts/install-vscode-extension.sh
```

This automated installer will:
- ✅ Check all prerequisites (VS Code, Node.js)
- ✅ Install dependencies
- ✅ Compile the extension
- ✅ Optionally package as .vsix
- ✅ Install in VS Code
- ✅ Configure settings

### Manual Installation

#### Option 1: From Source
```bash
# Navigate to extension directory
cd packages/vscode-extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Open in VS Code for testing
code .
# Press F5 to launch Extension Development Host
```

#### Option 2: From Marketplace (Coming Soon)
```bash
# When published to marketplace
code --install-extension gemini-docs-manager
```

#### Option 3: From VSIX Package
```bash
# Build the package
cd packages/vscode-extension
npm run compile
npx vsce package

# Install the generated .vsix file
code --install-extension gemini-docs-manager-*.vsix
```

### First Time Setup

1. **Open your project** in VS Code
2. **Click the Gemini Manager icon** in the Activity Bar (left sidebar)
3. **Configure settings** (optional):
   - Open Command Palette: `Cmd/Ctrl + Shift + P`
   - Type: `Preferences: Open Settings (JSON)`
   - Add:
   ```json
   {
     "gemini.documentationPath": "docs",
     "gemini.epicsPath": "docs/tasks",
     "gemini.ragServerUrl": "http://localhost:2000"
   }
   ```
4. **View the dashboard**: `Cmd/Ctrl + Shift + P` → "Gemini: Show Documentation Dashboard"

### Required Project Structure
```
your-project/
├── docs/                        # Documentation root
│   ├── 0_business_case/        # Business documentation
│   ├── 1_product/              # Product specs
│   ├── 2_architecture/         # Technical architecture
│   ├── 3_manuals/              # User manuals
│   ├── 4_quality/              # Quality docs
│   ├── 5_project_management/   # PM docs
│   └── tasks/                  # Epics and stories
│       ├── epic-*.md
│       └── story-*.md
└── .vscode/
    └── settings.json           # Extension settings
```

## Usage

### Viewing Documentation Status
1. Click the Gemini Manager icon in the Activity Bar
2. Expand the "Documentation Status" view
3. Browse categories and documents
4. Click on any document to open it

### Managing Epics & Stories
1. Open the "Epics & Stories" view
2. Click the + icon to create new epics or stories
3. Click on items to view/edit them
4. Right-click stories to mark them complete

### Using RAG Datastore
1. Open the "RAG Datastore" view
2. Right-click on any markdown file to upload it
3. Use the upload folder button for bulk uploads
4. Click search to query the knowledge base

### Dashboard
- Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
- Run "Gemini: Show Documentation Dashboard"
- View comprehensive statistics and perform quick actions

## Configuration

Configure the extension in VS Code settings:

```json
{
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true,
  "gemini.refreshInterval": 30000
}
```

### Settings

- **`gemini.documentationPath`**: Path to documentation folder (default: "docs")
- **`gemini.epicsPath`**: Path to epics and stories (default: "docs/tasks")
- **`gemini.ragServerUrl`**: RAG server URL (default: "http://localhost:2000")
- **`gemini.autoRefresh`**: Enable auto-refresh (default: true)
- **`gemini.refreshInterval`**: Refresh interval in milliseconds (default: 30000)

## Commands

All commands are available through the Command Palette (Ctrl+Shift+P / Cmd+Shift+P):

- `Gemini: Refresh Documentation Status` - Refresh documentation tree
- `Gemini: Open Document` - Open a documentation file
- `Gemini: Edit Document` - Edit or create a new document
- `Gemini: Upload to RAG Datastore` - Upload file to RAG
- `Gemini: Upload Folder to RAG` - Upload entire folder
- `Gemini: Refresh Epics & Stories` - Refresh project tracking
- `Gemini: Create New Epic` - Create a new epic
- `Gemini: Create New Story` - Create a new story
- `Gemini: Mark Story Complete` - Mark a story as done
- `Gemini: View RAG Status` - Check RAG server status
- `Gemini: Search Knowledge Base` - Search indexed documents
- `Gemini: Show Documentation Dashboard` - Open the dashboard

## Document Templates

The extension provides templates for:
- Business Case
- Product Requirements Document (PRD)
- Architecture Documentation
- API Specification
- Testing Strategy

Templates include required sections and placeholder content to ensure consistency.

## RAG Integration

### Server Setup
The extension integrates with a RAG server for document indexing and search. 

Default server: `http://localhost:2000`

### Offline Mode
When the server is unavailable, documents are stored locally and automatically synced when the connection is restored.

## Keyboard Shortcuts

- `Ctrl+Shift+D` / `Cmd+Shift+D` - Show dashboard
- `Ctrl+Shift+R` / `Cmd+Shift+R` - Refresh all views
- `Ctrl+Shift+U` / `Cmd+Shift+U` - Upload current file to RAG

## Requirements

- VS Code 1.85.0 or higher
- Node.js 18+ (for RAG server)
- Markdown files for documentation

## Extension Settings

This extension contributes the following settings:

* `gemini.enable`: Enable/disable this extension
* `gemini.documentationPath`: Set the path to documentation
* `gemini.ragServerUrl`: Configure RAG server URL

## Known Issues

- RAG server must be running for upload/search features
- Large folders may take time to upload
- Some markdown syntax may not be properly indexed

## Release Notes

### 1.0.0

Initial release with:
- Documentation status tracking
- Epics and stories management
- RAG datastore integration
- Rich dashboard
- Markdown editor integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Support

For issues and feature requests, please visit:
https://github.com/yourusername/gemini-docs-manager/issues

---

**Enjoy managing your documentation with Gemini!** 📚✨