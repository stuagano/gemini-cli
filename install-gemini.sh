#!/bin/bash
# Gemini Enterprise Architect - One-Click Installer
set -e

echo "🚀 Installing Gemini Enterprise Architect..."

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "❌ VS Code is not installed. Please install VS Code first."
    echo "   Download from: https://code.visualstudio.com/"
    exit 1
fi

# Check if Docker is available (preferred) or Python
USE_DOCKER=false
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    USE_DOCKER=true
    echo "✅ Docker detected - using containerized setup"
else
    echo "📦 Using local Python setup"
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required. Please install Python 3.9+ first."
        exit 1
    fi
fi

INSTALL_DIR="$HOME/.gemini"
EXTENSION_DIR="$INSTALL_DIR/vscode-extension"

echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download or copy the Gemini files
echo "📥 Setting up Gemini files..."
if [ -d "/Users/stuartgano/Documents/gemini-cli" ]; then
    echo "   Copying from local development..."
    cp -r "/Users/stuartgano/Documents/gemini-cli/"* .
else
    echo "   This script should be run from the gemini-cli directory"
    echo "   Please run: cd /Users/stuartgano/Documents/gemini-cli && ./install-gemini.sh"
    exit 1
fi

if [ "$USE_DOCKER" = true ]; then
    echo "🐳 Setting up Docker environment..."
    
    # Create production docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  gemini-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
EOF

    # Create Dockerfile if it doesn't exist
    if [ ! -f "Dockerfile" ]; then
        cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY packages/ ./packages/

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "src/start_server.py"]
EOF
    fi

    # Create requirements.txt if it doesn't exist
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
redis==5.0.1
asyncpg==0.29.0
aiofiles==23.2.1
python-multipart==0.0.6
numpy==1.24.3
faiss-cpu==1.7.4
python-jose[cryptography]==3.3.0
httpx==0.25.2
websockets==12.0
prometheus-client==0.19.0
pydantic==2.5.0
python-dotenv==1.0.0
EOF
    fi

    echo "   Building and starting services..."
    docker-compose up --build -d
    
    echo "   Waiting for services to be healthy..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/v1/health &>/dev/null; then
            echo "✅ Gemini server is running!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Server failed to start. Check logs with: docker-compose logs"
            exit 1
        fi
        echo "   Waiting... ($i/30)"
        sleep 2
    done

else
    echo "🐍 Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install requirements
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
redis==5.0.1
aiofiles==23.2.1
python-multipart==0.0.6
numpy==1.24.3
faiss-cpu==1.7.4
python-jose[cryptography]==3.3.0
httpx==0.25.2
pydantic==2.5.0
python-dotenv==1.0.0
EOF
    fi
    
    pip install -r requirements.txt
    
    # Start Redis if available
    if command -v redis-server &> /dev/null; then
        echo "   Starting Redis..."
        redis-server --daemonize yes --port 6379
    else
        echo "⚠️  Redis not found. Installing with Homebrew..."
        if command -v brew &> /dev/null; then
            brew install redis
            brew services start redis
        else
            echo "❌ Please install Redis manually or use Docker setup"
            exit 1
        fi
    fi
    
    # Start Gemini server in background
    echo "   Starting Gemini server..."
    nohup python src/start_server.py > gemini.log 2>&1 &
    
    # Wait for server to start
    for i in {1..15}; do
        if curl -f http://localhost:8000/api/v1/health &>/dev/null; then
            echo "✅ Gemini server is running!"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "❌ Server failed to start. Check gemini.log for details"
            exit 1
        fi
        sleep 2
    done
fi

echo "🔧 Installing VS Code extension..."

# Build and install extension
cd vscode-extension

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required for VS Code extension. Please install Node.js first."
    exit 1
fi

# Install dependencies and build
npm install --silent
npm run compile

# Install vsce if not available
if ! command -v vsce &> /dev/null; then
    npm install -g @vscode/vsce
fi

# Package and install extension
vsce package --out gemini-enterprise-architect.vsix
code --install-extension gemini-enterprise-architect.vsix --force

echo "⚙️  Configuring VS Code settings..."

# Create VS Code settings for Gemini
VSCODE_SETTINGS_DIR="$HOME/.vscode"
mkdir -p "$VSCODE_SETTINGS_DIR"

# Add Gemini settings to VS Code global settings
SETTINGS_FILE="$VSCODE_SETTINGS_DIR/settings.json"

if [ -f "$SETTINGS_FILE" ]; then
    # Backup existing settings
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add Gemini settings to existing settings
    python3 -c "
import json
import sys

try:
    with open('$SETTINGS_FILE', 'r') as f:
        settings = json.load(f)
except:
    settings = {}

# Add Gemini settings
gemini_settings = {
    'gemini.serverUrl': 'http://localhost:8000',
    'gemini.enableRealTimeValidation': True,
    'gemini.enableScoutFirst': True,
    'gemini.teachingMode': False,
    'gemini.skillLevel': 'mid',
    'gemini.learningStyle': 'hands_on',
    'gemini.validationSeverity': 'warning',
    'gemini.autoFix': False,
    'gemini.enablePerformanceOptimization': True
}

settings.update(gemini_settings)

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
"
else
    # Create new settings file
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "gemini.serverUrl": "http://localhost:8000",
  "gemini.enableRealTimeValidation": true,
  "gemini.enableScoutFirst": true,
  "gemini.teachingMode": false,
  "gemini.skillLevel": "mid",
  "gemini.learningStyle": "hands_on",
  "gemini.validationSeverity": "warning",
  "gemini.autoFix": false,
  "gemini.enablePerformanceOptimization": true
}
EOF
fi

# Create desktop shortcut for management
cat > "$HOME/Desktop/Gemini Control.sh" << 'EOF'
#!/bin/bash
echo "Gemini Enterprise Architect Control Panel"
echo "========================================"
echo "1. Start Gemini Server"
echo "2. Stop Gemini Server" 
echo "3. Restart Gemini Server"
echo "4. View Server Status"
echo "5. View Logs"
echo "6. Uninstall Gemini"
echo "========================================"
read -p "Select option (1-6): " choice

case $choice in
    1)
        cd ~/.gemini && docker-compose up -d 2>/dev/null || (source venv/bin/activate && nohup python src/start_server.py > gemini.log 2>&1 &)
        echo "Gemini server started"
        ;;
    2)
        cd ~/.gemini && docker-compose down 2>/dev/null || pkill -f "start_server.py"
        echo "Gemini server stopped"
        ;;
    3)
        cd ~/.gemini && docker-compose restart 2>/dev/null || (pkill -f "start_server.py" && sleep 2 && source venv/bin/activate && nohup python src/start_server.py > gemini.log 2>&1 &)
        echo "Gemini server restarted"
        ;;
    4)
        if curl -f http://localhost:8000/api/v1/health &>/dev/null; then
            echo "✅ Gemini server is running"
        else
            echo "❌ Gemini server is not responding"
        fi
        ;;
    5)
        cd ~/.gemini && (docker-compose logs --tail=50 || tail -50 gemini.log)
        ;;
    6)
        echo "Uninstalling Gemini..."
        cd ~/.gemini && docker-compose down -v 2>/dev/null
        code --uninstall-extension gemini-ai.gemini-enterprise-architect 2>/dev/null
        rm -rf ~/.gemini
        rm -f ~/Desktop/"Gemini Control.sh"
        echo "Gemini uninstalled"
        ;;
esac
EOF

chmod +x "$HOME/Desktop/Gemini Control.sh"

echo ""
echo "🎉 Installation Complete!"
echo "========================="
echo ""
echo "✅ Gemini Server: http://localhost:8000"
echo "✅ VS Code Extension: Installed and configured"
echo "✅ Desktop Control Panel: Created"
echo ""
echo "🚀 Quick Start:"
echo "   1. Open VS Code"
echo "   2. Open any Python/JavaScript file"
echo "   3. Press Ctrl+Shift+G, A to analyze"
echo "   4. Check the status bar for Gemini status"
echo ""
echo "📊 Web Dashboard: http://localhost:8000/docs"
echo "🛠️  Control Panel: Double-click 'Gemini Control' on desktop"
echo ""
echo "Need help? Check VS Code Output Panel: 'Gemini Enterprise Architect'"