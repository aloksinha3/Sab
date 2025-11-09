# Mada - Pregnancy Interactive Voice Response For Developing Health Care Systems


## Installation & Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- config.yaml file containing Twilio and ElevenLabs API keys
- Git for version control

### Quick Start (One Command)
```bash
# Clone the repository
git clone https://github.com/aloksinha3/SabCare.git
cd Mada

# Run the complete setup
./start.sh
```

### Manual Setup

#### 1. Backend Setup
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Configure Twilio credentials in backend/config.yaml
# Start the backend server
KMP_DUPLICATE_LIB_OK=TRUE python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

#### 2. Frontend Setup
```bash
# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

#### 3. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## License

This project is licensed under the MIT License.

---

Built with ❤️ for mothers around the world

