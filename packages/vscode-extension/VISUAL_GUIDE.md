# 📸 Visual Installation & Usage Guide

A step-by-step visual guide to installing and using the Gemini Documentation Manager VS Code Extension.

## 📦 Installation Steps

### Step 1: Run the Installer
```bash
./scripts/install-vscode-extension.sh
```

![Installation Script Running](./screenshots/install-script.png)
*The installer checks prerequisites and guides you through setup*

### Step 2: Open VS Code
After installation, the extension appears in your Activity Bar:

![VS Code Activity Bar](./screenshots/activity-bar.png)
*Look for the Gemini Manager icon (book icon)*

### Step 3: First View - Documentation Status
Click the Gemini Manager icon to see three panels:

![Documentation Status Panel](./screenshots/doc-status-panel.png)
*Visual indicators show completion status for each category*

#### Status Indicators:
- ✅ **Green checkmark** = Complete
- 🔄 **Yellow spinner** = In Progress
- ⚠️ **Red warning** = Not Started
- **Percentage** = Category completion

## 🎯 Core Features

### 1. Documentation Management

![Documentation Tree View](./screenshots/doc-tree-view.png)
*Hierarchical view of all documentation with real-time status*

**Actions:**
- Click any document to open
- Right-click for context menu
- Hover for word count and status

### 2. Epics & Stories Tracking

![Epics and Stories](./screenshots/epics-stories.png)
*Project management with automatic progress calculation*

**Visual Elements:**
- 📋 Epic with completion percentage
- ✅ Completed stories
- 🔄 In-progress stories
- ⭕ Todo stories

### 3. RAG Datastore

![RAG Datastore View](./screenshots/rag-datastore.png)
*Upload and search documentation with AI*

**Features Shown:**
- Upload queue
- Indexed documents count
- Search interface
- Document statistics

### 4. Rich Dashboard

![Dashboard Overview](./screenshots/dashboard.png)
*Comprehensive metrics and quick actions*

**Dashboard Sections:**
1. **Overview Stats** - Total docs, completion rate
2. **Category Progress** - Visual progress bars
3. **RAG Metrics** - Upload and indexing status
4. **Quick Actions** - One-click operations

## 🔧 Configuration

### Settings UI
Access via `Cmd/Ctrl + ,` → Extensions → Gemini Documentation Manager

![Settings Interface](./screenshots/settings.png)
*Configure paths, URLs, and refresh intervals*

### settings.json
```json
{
  "gemini.documentationPath": "docs",
  "gemini.epicsPath": "docs/tasks",
  "gemini.ragServerUrl": "http://localhost:2000",
  "gemini.autoRefresh": true,
  "gemini.refreshInterval": 30000
}
```

## 💡 Common Workflows

### Creating a Document from Template

![Create Document Flow](./screenshots/create-document.png)

1. Right-click in Documentation Status
2. Select "Edit Document"
3. Choose template type
4. Document opens with pre-filled sections

### Uploading to RAG

![Upload to RAG](./screenshots/upload-rag.png)

1. Right-click any markdown file or folder
2. Select "Upload to RAG Datastore"
3. Monitor progress in RAG view
4. Search uploaded content instantly

### Managing Stories

![Story Management](./screenshots/story-management.png)

1. Expand epic to see stories
2. Click checkmark to complete
3. Status updates automatically
4. Epic progress recalculates

## ⌨️ Keyboard Shortcuts

![Command Palette](./screenshots/command-palette.png)
*Access all commands via Command Palette*

| Visual Cue | Shortcut | Action |
|------------|----------|--------|
| ![Dashboard Icon](./icons/dashboard.png) | `Cmd/Ctrl + Shift + D` | Show Dashboard |
| ![Refresh Icon](./icons/refresh.png) | `Cmd/Ctrl + Shift + R` | Refresh All |
| ![Upload Icon](./icons/upload.png) | `Cmd/Ctrl + Shift + U` | Upload to RAG |

## 🎨 Themes Support

The extension adapts to your VS Code theme:

### Light Theme
![Light Theme View](./screenshots/theme-light.png)

### Dark Theme
![Dark Theme View](./screenshots/theme-dark.png)

### High Contrast
![High Contrast View](./screenshots/theme-high-contrast.png)

## 📊 Dashboard Features

### Metrics Overview
![Metrics Section](./screenshots/metrics.png)
*Real-time statistics update every 30 seconds*

### Quick Actions
![Quick Actions](./screenshots/quick-actions.png)
*One-click access to common tasks*

### Progress Visualization
![Progress Bars](./screenshots/progress-bars.png)
*Visual representation of completion status*

## 🔍 Search Features

### RAG Search Interface
![Search Interface](./screenshots/search-interface.png)

1. Click search icon
2. Enter query
3. View ranked results
4. Click to open document

### Search Results
![Search Results](./screenshots/search-results.png)
*AI-powered semantic search across all documentation*

## 🚨 Troubleshooting Views

### Empty State
![Empty State](./screenshots/empty-state.png)
*What you see when no workspace is open*

### Loading State
![Loading State](./screenshots/loading-state.png)
*Spinner indicates data is being fetched*

### Error State
![Error State](./screenshots/error-state.png)
*Clear error messages with suggested actions*

## 📱 Responsive Design

### Narrow Sidebar
![Narrow View](./screenshots/narrow-view.png)
*Adapts to different sidebar widths*

### Wide Dashboard
![Wide Dashboard](./screenshots/wide-dashboard.png)
*Makes use of available space*

## 🎬 Video Tutorials

### Installation (2 min)
[![Installation Video](./thumbnails/install-video.png)](https://example.com/install-video)

### Quick Tour (3 min)
[![Tour Video](./thumbnails/tour-video.png)](https://example.com/tour-video)

### Advanced Features (5 min)
[![Advanced Video](./thumbnails/advanced-video.png)](https://example.com/advanced-video)

## 📝 Notes on Screenshots

**For Contributors:** When adding actual screenshots, please:
1. Use VS Code's default dark theme for consistency
2. Capture at 1920x1080 resolution when possible
3. Highlight relevant UI elements with red boxes
4. Keep file sizes under 500KB (use PNG format)
5. Name files descriptively as shown above

**Screenshot Checklist:**
- [ ] Installation script output
- [ ] Activity bar with extension icon
- [ ] Documentation status panel
- [ ] Epics and stories view
- [ ] RAG datastore view
- [ ] Dashboard webview
- [ ] Settings interface
- [ ] Command palette
- [ ] Context menus
- [ ] Search interface
- [ ] Error states
- [ ] Success notifications

---

*Screenshots are placeholders. Actual screenshots will be added after extension testing.*