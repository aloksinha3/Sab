# Mada - Pregnancy Interactive Voice Response For Developing Health Care Systems

Revolutionizing maternal healthcare through intelligent automation and personalized AI-driven communication

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Gemma](https://img.shields.io/badge/Gemma-2B-orange.svg)
![Twilio](https://img.shields.io/badge/Twilio-Enabled-red.svg)

## Project Overview

SabCare is an advanced Interactive Voice Response (IVR) system designed specifically for maternal healthcare. It leverages fine-tuned Gemma AI models to provide personalized pregnancy care support through automated phone calls, intelligent message processing, and comprehensive patient management.

## Key Innovations

- **AI-Powered Personalization**: Fine-tuned Gemma 2B model generates context-aware, patient-specific health messages
- **Two-Way Communication**: Patients can leave voice messages and receive AI-processed callbacks
- **Intelligent Scheduling**: Automated medication reminders, weekly check-ins, and appointment notifications
- **Medical Knowledge Integration**: RAG (Retrieval-Augmented Generation) system with comprehensive pregnancy care database
- **Real-time Analytics**: Live call queue monitoring and patient engagement tracking

## 🚀 Core Features

### 1. **AI-Powered IVR Messaging** 🧠
- **Fine-tuned Gemma Model**: Trained on pregnancy care data for medical accuracy
- **Personalized Content**: Patient-specific messages based on gestational age, risk factors, and medical history
- **Risk-Aware Messaging**: Different message strategies for high-risk vs. low-risk pregnancies
- **Medication Integration**: Automated reminders with specific dosage and timing information

### 2. **Comprehensive Call Scheduling** 📅
- **Weekly Check-ins**: Personalized pregnancy updates and health monitoring
- **Medication Reminders**: Automated scheduling with specific timing requirements
- **Appointment Notifications**: Healthcare visit reminders with preparation instructions
- **High-Risk Monitoring**: Enhanced call frequency for at-risk patients

### 3. **Two-Way Communication System** 📞
- **"Press 1" Functionality**: Patients can leave voice messages after each call
- **Message Recording**: Secure audio capture and storage
- **AI Processing**: Intelligent analysis of patient messages using Gemma
- **Automated Callbacks**: Scheduled responses with personalized AI-generated content

### 4. **Patient Management System** 👥
- **Comprehensive Registration**: Complete patient data collection and risk assessment
- **Real-time Monitoring**: Live dashboard with patient status and engagement metrics
- **IVR Schedule Generation**: Automatic creation of personalized call schedules
- **Medical History Integration**: Risk factor analysis and treatment tracking

### 5. **Medical Knowledge Base** 📚
- **RAG System**: Retrieval-Augmented Generation for medical information
- **Pregnancy Database**: Comprehensive knowledge base with medical guidelines
- **Context-Aware Responses**: AI-generated responses based on medical best practices
- **Continuous Learning**: System improves with new patient interactions

## Installation & Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- Twilio Account (for voice calls)
- Git for version control

### Quick Start (One Command)
```bash
# Clone the repository
git clone https://github.com/aloksinha3/SabCare.git
cd SabCare

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

## Acknowledgments
- **Google Gemma Team**: For the open-source language model
- **Twilio**: For voice communication platform
- **FastAPI Team**: For the modern Python web framework
- **React Team**: For the frontend development framework

---

**SabCare** - Empowering pregnancy care through intelligent automation 🤖👶

Built with ❤️ for maternal healthcare innovation

