#!/bin/bash

# Quick test script for VS Code extension
echo "🧪 Testing Gemini Documentation Manager Extension"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in extension directory"
    echo "Please run from packages/vscode-extension/"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Compile TypeScript
echo "🔧 Compiling TypeScript..."
npm run compile

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed"
    exit 1
fi

echo "✅ Compilation successful"
echo ""

# Run basic validation
echo "🔍 Validating extension manifest..."
node -e "
const pkg = require('./package.json');
console.log('Extension name:', pkg.displayName);
console.log('Version:', pkg.version);
console.log('Publisher:', pkg.publisher);

// Check required fields
const required = ['name', 'displayName', 'version', 'engines', 'main', 'contributes'];
const missing = required.filter(field => !pkg[field]);

if (missing.length > 0) {
    console.error('❌ Missing required fields:', missing.join(', '));
    process.exit(1);
}

// Check contributes
const contributes = pkg.contributes;
console.log('Views:', Object.keys(contributes.views || {}).length);
console.log('Commands:', (contributes.commands || []).length);
console.log('Configuration properties:', Object.keys(contributes.configuration?.properties || {}).length);

console.log('✅ Extension manifest is valid');
"

echo ""
echo "🎯 Extension Test Summary"
echo "========================"
echo "✅ Dependencies installed"
echo "✅ TypeScript compiled"
echo "✅ Manifest validated"
echo ""
echo "📝 Next Steps:"
echo "1. Open VS Code in this directory: code ."
echo "2. Press F5 to launch Extension Development Host"
echo "3. Test the extension features"
echo ""
echo "Or run the full installer:"
echo "  ../../scripts/install-vscode-extension.sh"
echo ""