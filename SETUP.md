# SabCare Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8+ 
- Node.js 16+
- Twilio Account (for voice calls)
- Git

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/aloksinha3/SabCare.git
cd SabCare

# Run the setup script
./start.sh
```

### 3. Configuration

#### Backend Configuration
1. Copy the example config file:
   ```bash
   cp backend/config.yaml.example backend/config.yaml
   ```

2. Edit `backend/config.yaml` with your Twilio credentials:
   ```yaml
   twilio:
     account_sid: "YOUR_TWILIO_ACCOUNT_SID"
     auth_token: "YOUR_TWILIO_AUTH_TOKEN"
     from_number: "YOUR_TWILIO_PHONE_NUMBER"
   ```

#### Environment Variables (Optional)
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
SERVER_URL=http://localhost:8000
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=your_twilio_phone_number
```

### 4. Running the Application

#### Backend
```bash
cd backend
export KMP_DUPLICATE_LIB_OK=TRUE
python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

Or use the run script:
```bash
./backend/run.sh
```

#### Frontend
```bash
npm run dev
```

### 5. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Features

### Patient Management
- Add new patients with comprehensive information
- Update patient details
- View all patients
- Generate IVR schedules automatically

### IVR Scheduling
- Automatic schedule generation based on:
  - Gestational age
  - Risk category
  - Medications
  - Risk factors
- Weekly check-ins
- Medication reminders
- High-risk monitoring calls

### Call Queue
- View upcoming calls
- Real-time updates
- Call status tracking

### Analytics
- Patient statistics
- Risk distribution
- Call metrics
- Pending messages

## Twilio Setup

1. Create a Twilio account at https://www.twilio.com
2. Get your Account SID and Auth Token
3. Purchase a phone number
4. Configure webhooks:
   - Voice URL: `http://your-server.com/twilio/voice`
   - Status Callback: `http://your-server.com/twilio/status`

## AI Model Setup

The application uses Google's Gemma model for AI-powered message generation. The model will be automatically downloaded on first use.

### Model Options
- Default: `google/gemma-2b-it` (runs on CPU)
- Can be configured in `backend/config.yaml`

### Fallback Mode
If the AI model fails to load, the system will use fallback text generation that still provides personalized messages.

## Database

The application uses SQLite for data storage. The database file `patients.db` will be created automatically on first run.

### Database Schema
- `patients`: Patient information and schedules
- `patient_messages`: Voice messages from patients
- `call_logs`: Call history and scheduling

## Troubleshooting

### Backend Issues
- **Model loading errors**: Set `use_cpu: true` in config.yaml
- **Twilio errors**: Verify credentials in config.yaml
- **Database errors**: Delete `patients.db` to reset

### Frontend Issues
- **API connection errors**: Verify backend is running on port 8000
- **CORS errors**: Check CORS settings in `backend/main.py`

### Common Issues
1. **Port already in use**: Change port in `vite.config.ts` or `main.py`
2. **Module not found**: Run `pip install -r backend/requirements.txt` and `npm install`
3. **Twilio webhook errors**: Ensure your server is publicly accessible (use ngrok for local testing)

## Development

### Project Structure
```
SabCare/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database operations
│   ├── twilio_integration.py # Twilio service
│   ├── ai_models/
│   │   ├── gemma_model.py   # AI model wrapper
│   │   └── rag_system.py    # RAG system
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── pages/               # React pages
│   ├── components/          # React components
│   └── api/                 # API client
├── medgemma_training_data.json
├── pregnancy_rag_database.json
└── package.json
```

## Deployment

See the main README.md for deployment options including Railway, Heroku, Render, Vercel, and Netlify.

## Support

For issues and questions, please open an issue on GitHub.

