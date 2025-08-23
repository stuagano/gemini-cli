#!/bin/bash

# VS Code Extension Installer for Gemini Documentation Manager
# One-click setup for the VS Code extension

set -e

echo "🚀 Gemini Documentation Manager - VS Code Extension Installer"
echo "============================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if VS Code is installed
check_vscode() {
    if command -v code &> /dev/null; then
        echo -e "${GREEN}✅ VS Code found${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  VS Code not found${NC}"
        echo ""
        echo "Please install VS Code first:"
        echo "  Download from: https://code.visualstudio.com/"
        echo ""
        read -p "Press Enter after installing VS Code, or Ctrl+C to exit..."
        if command -v code &> /dev/null; then
            echo -e "${GREEN}✅ VS Code found${NC}"
            return 0
        else
            echo -e "${RED}❌ VS Code still not found. Please install it and try again.${NC}"
            exit 1
        fi
    fi
}

# Check Node.js installation
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        echo -e "${GREEN}✅ Node.js $NODE_VERSION found${NC}"
        return 0
    else
        echo -e "${RED}❌ Node.js not found${NC}"
        echo "Please install Node.js 18+ first"
        exit 1
    fi
}

# Navigate to extension directory
cd "$(dirname "$0")/.."
EXTENSION_DIR="packages/vscode-extension"

if [ ! -d "$EXTENSION_DIR" ]; then
    echo -e "${RED}❌ Extension directory not found at $EXTENSION_DIR${NC}"
    exit 1
fi

cd "$EXTENSION_DIR"
echo "📁 Working in: $(pwd)"
echo ""

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
check_vscode
check_node
echo ""

# Step 2: Install dependencies
echo "📦 Installing dependencies..."
npm install
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Compile TypeScript
echo "🔧 Compiling TypeScript..."
npm run compile
echo -e "${GREEN}✅ TypeScript compiled${NC}"
echo ""

# Step 4: Package the extension (optional)
echo "📦 Would you like to package the extension as a .vsix file?"
echo "   (This allows you to share or install it manually)"
read -p "Package extension? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if vsce is installed
    if ! command -v vsce &> /dev/null; then
        echo "Installing vsce (Visual Studio Code Extension manager)..."
        npm install -g vsce
    fi
    
    echo "📦 Packaging extension..."
    vsce package --allow-missing-repository
    echo -e "${GREEN}✅ Extension packaged as .vsix file${NC}"
    VSIX_FILE=$(ls -t *.vsix | head -1)
    echo "   Package created: $VSIX_FILE"
fi
echo ""

# Step 5: Install or open in VS Code
echo "🎯 How would you like to proceed?"
echo "1) Open extension project in VS Code (for development/testing)"
echo "2) Install packaged extension in VS Code"
echo "3) Both"
echo "4) Skip"
read -p "Choice (1-4): " INSTALL_CHOICE

case $INSTALL_CHOICE in
    1)
        echo "Opening extension in VS Code..."
        code .
        echo -e "${GREEN}✅ Extension opened in VS Code${NC}"
        echo ""
        echo "To test the extension:"
        echo "  1. Press F5 in VS Code"
        echo "  2. A new VS Code window will open with the extension loaded"
        ;;
    2)
        if [ -z "$VSIX_FILE" ]; then
            # Try to find existing vsix file
            VSIX_FILE=$(ls -t *.vsix 2>/dev/null | head -1)
            if [ -z "$VSIX_FILE" ]; then
                echo -e "${YELLOW}No .vsix file found. Running packaging first...${NC}"
                vsce package --allow-missing-repository
                VSIX_FILE=$(ls -t *.vsix | head -1)
            fi
        fi
        echo "Installing extension in VS Code..."
        code --install-extension "$VSIX_FILE"
        echo -e "${GREEN}✅ Extension installed${NC}"
        ;;
    3)
        if [ -z "$VSIX_FILE" ]; then
            VSIX_FILE=$(ls -t *.vsix 2>/dev/null | head -1)
            if [ -z "$VSIX_FILE" ]; then
                echo -e "${YELLOW}No .vsix file found. Running packaging first...${NC}"
                vsce package --allow-missing-repository
                VSIX_FILE=$(ls -t *.vsix | head -1)
            fi
        fi
        echo "Installing extension and opening project..."
        code --install-extension "$VSIX_FILE"
        code .
        echo -e "${GREEN}✅ Extension installed and project opened${NC}"
        ;;
    4)
        echo "Skipping VS Code operations"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📚 Extension Features:"
echo "  • Documentation Status Panel - Track documentation progress"
echo "  • Epics & Stories View - Manage project tasks"
echo "  • RAG Datastore - Upload and search documentation"
echo "  • Rich Dashboard - View comprehensive metrics"
echo "  • Smart Templates - Create documents from templates"
echo ""
echo "🚀 Quick Start:"
echo "  1. Open VS Code"
echo "  2. Look for the Gemini Manager icon in the Activity Bar (left sidebar)"
echo "  3. Click it to see your documentation and project status"
echo "  4. Use Cmd/Ctrl+Shift+P → 'Gemini: Show Documentation Dashboard'"
echo ""
echo "📖 Documentation: packages/vscode-extension/README.md"
echo "🐛 Issues: https://github.com/google-gemini/gemini-cli/issues"
echo ""

# Optional: Configure extension settings
echo "Would you like to configure the extension settings now?"
read -p "Configure settings? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 Extension Settings"
    echo "===================="
    
    # Documentation path
    read -p "Documentation path (default: docs): " DOC_PATH
    DOC_PATH=${DOC_PATH:-docs}
    
    # Epics path
    read -p "Epics/Stories path (default: docs/tasks): " EPICS_PATH
    EPICS_PATH=${EPICS_PATH:-docs/tasks}
    
    # RAG server URL
    read -p "RAG Server URL (default: http://localhost:2000): " RAG_URL
    RAG_URL=${RAG_URL:-http://localhost:2000}
    
    # Create VS Code settings
    VSCODE_DIR="../../.vscode"
    mkdir -p "$VSCODE_DIR"
    
    SETTINGS_FILE="$VSCODE_DIR/settings.json"
    
    # Check if settings.json exists
    if [ -f "$SETTINGS_FILE" ]; then
        echo "Updating existing settings.json..."
        # This is a simple append - in production you'd want to properly merge JSON
        echo "Note: Please manually merge these settings into your .vscode/settings.json:"
    else
        echo "Creating settings.json..."
        cat > "$SETTINGS_FILE" << EOF
{
    "gemini.documentationPath": "$DOC_PATH",
    "gemini.epicsPath": "$EPICS_PATH",
    "gemini.ragServerUrl": "$RAG_URL",
    "gemini.autoRefresh": true,
    "gemini.refreshInterval": 30000
}
EOF
        echo -e "${GREEN}✅ Settings saved to .vscode/settings.json${NC}"
    fi
    
    cat << EOF

Gemini Extension Settings:
  • Documentation Path: $DOC_PATH
  • Epics Path: $EPICS_PATH
  • RAG Server URL: $RAG_URL
  • Auto-refresh: Enabled (30 seconds)
EOF
fi

echo ""
echo -e "${GREEN}✨ Setup complete! Enjoy using Gemini Documentation Manager!${NC}"