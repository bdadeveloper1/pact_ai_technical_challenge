#!/bin/bash

echo "🔍 PACT AI Demo Setup Verification"
echo "=================================="

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo "✅ Node.js: $NODE_VERSION"
    else
        echo "⚠️  Node.js: $NODE_VERSION (requires v18+)"
        echo "   Run: nvm install 18 && nvm use 18"
    fi
else
    echo "❌ Node.js not found"
    echo "   Install from: https://nodejs.org/"
fi

# Check backend dependencies
echo ""
echo "🐍 Backend Dependencies:"
cd backend 2>/dev/null || { echo "❌ backend/ directory not found"; exit 1; }

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
    
    # Check if uvicorn is available
    if python3 -c "import uvicorn" 2>/dev/null; then
        echo "✅ uvicorn installed"
    else
        echo "⚠️  uvicorn not installed"
        echo "   Run: pip install -r requirements.txt"
    fi
    
    # Check if FastAPI is available
    if python3 -c "import fastapi" 2>/dev/null; then
        echo "✅ fastapi installed"
    else
        echo "⚠️  fastapi not installed"
        echo "   Run: pip install -r requirements.txt"
    fi
else
    echo "❌ requirements.txt not found"
fi

cd ..

# Check frontend dependencies
echo ""
echo "🎨 Frontend Dependencies:"
cd frontend 2>/dev/null || { echo "❌ frontend/ directory not found"; exit 1; }

if [ -f "package.json" ]; then
    echo "✅ package.json found"
    
    if [ -d "node_modules" ]; then
        echo "✅ node_modules installed"
    else
        echo "⚠️  node_modules not found"
        echo "   Run: cd frontend && npm install"
    fi
else
    echo "❌ package.json not found"
fi

cd ..

# Check if ports are available
echo ""
echo "🔌 Port Availability:"

if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Port 8000 available (backend)"
else
    echo "⚠️  Port 8000 in use (kill existing backend)"
fi

if ! lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Port 3000 available (frontend)"
else
    echo "⚠️  Port 3000 in use (kill existing frontend)"
fi

echo ""
echo "🚀 Ready to start? Run: ./start-demo.sh"
