#!/bin/bash

# Start the CLI in development mode

echo "🚀 Starting Gemini CLI in development mode..."

# Set development environment variables
export NODE_ENV=development

# Build packages first
echo "🔨 Building packages..."
npm run build:packages

# Start CLI development with watch mode
echo "🔥 Starting CLI with hot reload..."
exec npm run start