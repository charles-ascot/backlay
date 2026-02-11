#!/bin/bash

echo "🚀 Starting CHIMERA Backtest Simulator"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "⚠️  Backend not running. Start it with:"
    echo "   cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload"
    echo ""
else
    echo "✅ Backend running at http://localhost:8000"
fi

# Check if frontend is running
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "⚠️  Frontend not running. Start it with:"
    echo "   cd frontend && npm install && npm run dev"
    echo ""
else
    echo "✅ Frontend running at http://localhost:5173"
fi

echo "📖 See README.md for full setup instructions"
