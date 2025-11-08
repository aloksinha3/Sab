#!/bin/bash

# Set environment variable for OpenMP
export KMP_DUPLICATE_LIB_OK=TRUE

# Change to backend directory
cd "$(dirname "$0")"

# Run the FastAPI server
python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"

