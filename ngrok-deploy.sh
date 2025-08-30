#!/bin/bash

# Install ngrok if not already installed
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ngrok/ngrok/ngrok
    else
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt update && sudo apt install ngrok
    fi
fi

echo "🚀 Starting PACT AI Demo on ngrok..."

# Start backend
echo "📊 Starting backend on port 8000..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend  
echo "🎨 Starting frontend on port 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Start ngrok tunnels
echo "🌐 Creating ngrok tunnels..."
ngrok http 8000 --log=stdout > backend.log &
NGROK_BACKEND_PID=$!

ngrok http 3000 --log=stdout > frontend.log &
NGROK_FRONTEND_PID=$!

echo "✅ Demo deployed!"
echo "📊 Backend: Check backend.log for ngrok URL"
echo "🎨 Frontend: Check frontend.log for ngrok URL"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID $NGROK_BACKEND_PID $NGROK_FRONTEND_PID"

# Keep script running
wait
