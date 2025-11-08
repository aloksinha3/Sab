#!/bin/bash

echo "🚀 Starting SabCare Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Set environment variable for OpenMP
export KMP_DUPLICATE_LIB_OK=TRUE

echo "📦 Installing backend dependencies (core only)..."
cd backend
pip install -r requirements.txt

echo ""
echo "💡 AI features are optional. To enable AI features, run:"
echo "   pip install -r requirements-ai.txt"
echo "   (This requires more system resources)"

echo "📦 Installing frontend dependencies..."
cd ..
npm install

echo "🗄️ Initializing database..."
cd backend
python init_db.py

echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Terminal 1: cd backend && KMP_DUPLICATE_LIB_OK=TRUE python -c \"import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\""
echo "  2. Terminal 2: npm run dev"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"

