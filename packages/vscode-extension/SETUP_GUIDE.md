# Quick Setup Guide for New Projects

## 🚀 1-Minute Setup

### For Any Project Structure

1. **Copy the extension:**
   ```bash
   cp -r /path/to/gemini-cli/packages/vscode-extension ./vscode-extension
   cd vscode-extension
   ```

2. **Install:**
   ```bash
   ./install.sh
   ```

3. **Configure for your project** in VS Code settings (`Cmd+,`):

   **Option A: Simple Projects**
   ```json
   {
     "gemini.documentationStructure": "flat",
     "gemini.documentationPath": "docs"
   }
   ```

   **Option B: Custom Structure**
   ```json
   {
     "gemini.documentationStructure": "custom", 
     "gemini.customCategories": [
       {"name": "README", "path": ".", "icon": "📖"},
       {"name": "Docs", "path": "documentation", "icon": "📚"}
     ]
   }
   ```

4. **Reload VS Code** (`Cmd+R`) and look for 📖 Gemini Manager panel!

## 📁 Common Project Structures

### Standard Open Source Project
```json
{
  "gemini.documentationStructure": "custom",
  "gemini.documentationPath": ".",
  "gemini.customCategories": [
    {"name": "README", "path": ".", "icon": "📖"},
    {"name": "Docs", "path": "docs", "icon": "📚"},
    {"name": "Wiki", "path": "wiki", "icon": "📄"}
  ],
  "gemini.epicsPath": "docs/roadmap"
}
```

### React/Frontend Project  
```json
{
  "gemini.documentationStructure": "custom",
  "gemini.customCategories": [
    {"name": "Components", "path": "src/components", "icon": "⚛️"},
    {"name": "Docs", "path": "docs", "icon": "📚"},  
    {"name": "Storybook", "path": "stories", "icon": "📖"}
  ]
}
```

### API Project
```json
{
  "gemini.documentationStructure": "custom",
  "gemini.customCategories": [
    {"name": "API Docs", "path": "api-docs", "icon": "🔌"},
    {"name": "Swagger", "path": "swagger", "icon": "📋"},
    {"name": "Examples", "path": "examples", "icon": "💡"}
  ]
}
```

### Monorepo
```json
{
  "gemini.documentationStructure": "custom",
  "gemini.customCategories": [
    {"name": "Root Docs", "path": "docs", "icon": "📚"},
    {"name": "Frontend", "path": "packages/frontend/docs", "icon": "🖥️"},
    {"name": "Backend", "path": "packages/backend/docs", "icon": "⚙️"},
    {"name": "Shared", "path": "packages/shared/docs", "icon": "📦"}
  ]
}
```

## 🎯 No Epic/Story Files?

The extension works great without them! Epic & Story tracking is optional.

To add project tracking:
1. Create folder: `mkdir docs/roadmap` (or whatever you prefer)
2. Set path: `"gemini.epicsPath": "docs/roadmap"`
3. Use commands "Create Epic" and "Create Story" for templates

## 🔧 Distribution

### Share Extension Package
```bash
# Package once
npm run package

# Distribute to other projects  
cp gemini-docs-manager-1.0.0.vsix /path/to/other-project/
cd /path/to/other-project
code --install-extension gemini-docs-manager-1.0.0.vsix
```

### Team Installation
Add to your project's setup docs:
```bash
# In project README.md
## VS Code Extension
We use a custom documentation manager extension:

1. Install: `code --install-extension tools/gemini-docs-manager-1.0.0.vsix`
2. Reload VS Code
3. Configure in settings (see .vscode/settings.json)
```

## 🛠️ Customization Tips

**Change Extension Name/Icon**: Edit `package.json`:
```json
{
  "name": "your-project-docs-manager", 
  "displayName": "Your Project Documentation Manager",
  "description": "Documentation manager for Your Project"
}
```

**Different Document Templates**: Edit `src/commands/index.ts` epic/story templates

**Additional File Types**: Modify `src/providers/DocumentationProvider.ts` file filters

**Custom Document Analysis**: Edit `src/services/DocumentationService.ts` requirements

## ✅ Works Great For

- Any project with documentation folders
- Teams wanting documentation visibility  
- Projects using epic/story methodology
- Knowledge management needs
- Zero configuration for basic usage

The extension adapts to your existing structure - no need to reorganize your project!