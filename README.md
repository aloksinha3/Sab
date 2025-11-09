# Mada
Pregnancy IVR With AI Voice Features For Developing Health Care Systems

Across low-resource settings, patients—especially expectant mothers—receive only brief clinic interactions before returning home with limited support and high risk of complications. This post-clinic gap affects billions: 4.5 billion lack essential services, 1.3 billion face financial hardship due to care costs, and primary-care visits can be as short as 48 seconds, leaving little time to ensure understanding of critical medications. Half of patients worldwide fail to take medicines as prescribed, contributing to avoidable deaths and preventable neonatal and maternal mortality. Digital health tools have struggled to reach the most vulnerable due to lack of internet access, literacy barriers, and limited smartphone penetration. Yet evidence from interventions and recent clinical trials shows that voice-based outreach can sustainably improve adherence, detect danger signs, and save lives at national scale. With an 11-million-worker shortage projected by 2030 and poor follow-up driving preventable harms, the greatest risks begin after discharge—when patients are alone, unsupported, and disconnected from care.

We built a voice-first follow-up system designed to reach any patient with a phone, no apps, literacy, or data required. Clinicians register patients through a dashboard that captures diagnosis, dosage requirements, anetnatal progress, and comorbidities; a Twilio-powered IVR then generates personalized medication-adherence call schedules using basic dosing logic and engagement history. During each scheduled call, an AI voice agent fine tuned on pregnancy care and RAG embedded guidelines conducts two-way check-ins, reinforces medication instructions, screens for danger signs, and adapts follow-up cadence based on adherence risk. Missed calls, concerning symptoms, and non-response trigger automated clinician alerts, creating a real-time safety net. The system supports multi-language delivery and extends care beyond the post-clinic gap, improving adherence, catching complications earlier, and providing equitable support at population scale with minimal costs.

## Installation & Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- config.yaml file containing unique Twilio and ElevenLabs API keys
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

