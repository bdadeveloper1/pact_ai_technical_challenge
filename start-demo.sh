#!/bin/bash

echo "🚀 Starting PACT AI EHR Document Processing Demo"
echo "=============================================="

# Function to check Node.js version
check_node_version() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2)
        REQUIRED_VERSION="18.17.0"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Start backend in background
echo "📊 Starting Python backend with Medallion architecture..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check Node.js version before starting frontend
if check_node_version; then
    # Start frontend
    echo "🌐 Starting Next.js frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    echo ""
    echo "✅ Full Demo is ready!"
    echo ""
    echo "📍 Backend API: http://localhost:8000"
    echo "📍 Frontend UI: http://localhost:3000"
    echo "📍 API Docs: http://localhost:8000/docs"
    echo ""
    echo "🏗️ Medallion Architecture Endpoints:"
    echo "   📊 Pipeline Stats: http://localhost:8000/api/medallion/pipeline-stats"
    echo "   🥇 Gold Profiles: http://localhost:8000/api/medallion/gold-profiles"
    echo "   🥈 Silver Entities: http://localhost:8000/api/medallion/silver-entities"
    echo ""
    echo "🔄 Press Ctrl+C to stop both services"

    # Wait for interrupt
    trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
else
    echo ""
    echo "⚠️  Node.js version 18.17.0+ required for frontend (current: $(node -v 2>/dev/null || echo 'not installed'))"
    echo "✅ Backend API Demo available:"
    echo ""
    echo "📍 Backend API: http://localhost:8000"
    echo "📍 API Docs: http://localhost:8000/docs"
    echo ""
    echo "🔥 Try these demo commands:"
    echo "   curl http://localhost:8000/"
    echo "   curl http://localhost:8000/api/patients"
    echo "   curl http://localhost:8000/api/resources"
    echo "   curl http://localhost:8000/api/medallion/pipeline-stats"
    echo ""
    echo "🏗️ Medallion Architecture Endpoints:"
    echo "   📊 Pipeline Stats: http://localhost:8000/api/medallion/pipeline-stats"
    echo "   🥇 Gold Profiles: http://localhost:8000/api/medallion/gold-profiles"
    echo "   🥈 Silver Entities: http://localhost:8000/api/medallion/silver-entities"
    echo ""
    echo "🔄 Press Ctrl+C to stop backend service"

    # Wait for interrupt
    trap "echo '🛑 Stopping backend...'; kill $BACKEND_PID; exit" INT
    wait
fi
