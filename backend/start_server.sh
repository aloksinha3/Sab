#!/bin/bash

# Start SabCare Backend Server

echo "🚀 Starting SabCare Backend Server..."
echo ""

# Set environment variable for OpenMP
export KMP_DUPLICATE_LIB_OK=TRUE

# Change to backend directory
cd "$(dirname "$0")"

# Check if database exists
if [ ! -f "patients.db" ]; then
    echo "📦 Initializing database..."
    python init_db.py
fi

# Start the server
echo "🌐 Starting FastAPI server on http://0.0.0.0:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"

