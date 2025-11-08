from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from ai_models.gemma_model import FineTunedMedGemmaAI
from ai_models.rag_system import RAGSystem
from twilio_integration import TwilioService

app = FastAPI(title="SabCare API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
gemma_ai = FineTunedMedGemmaAI()
rag_system = RAGSystem()
twilio_service = TwilioService()

# Pydantic models
class Medication(BaseModel):
    name: str
    dosage: str = ""
    frequency: List[str] = []  # Array of days: ["Sun", "Mon", "Tue", etc.]
    time: str = ""  # Time in HH:MM format (24-hour)

class PatientCreate(BaseModel):
    name: str
    phone: str
    gestational_age_weeks: int
    risk_factors: List[str] = []
    medications: List[Medication] = []
    risk_category: str = "low"

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    gestational_age_weeks: Optional[int] = None
    risk_factors: Optional[List[str]] = None
    medications: Optional[List[Medication]] = None
    risk_category: Optional[str] = None

class IVRScheduleItem(BaseModel):
    call_type: str
    scheduled_time: datetime
    message_text: str

class MessageProcess(BaseModel):
    transcript: str

class ScheduleRequest(BaseModel):
    patient_id: int

# API Routes
@app.get("/")
async def root():
    return {"message": "Mada API", "version": "1.0.0"}

@app.get("/patients/")
async def get_all_patients():
    """Get all patients"""
    patients = db.get_all_patients()
    # Parse JSON fields
    for patient in patients:
        if patient.get('risk_factors'):
            try:
                import json
                patient['risk_factors'] = json.loads(patient['risk_factors'])
            except:
                patient['risk_factors'] = []
        if patient.get('medications'):
            try:
                import json
                meds = json.loads(patient['medications'])
                # Ensure medications are in the correct format
                if meds and isinstance(meds, list):
                    # Convert old formats to new format
                    converted_meds = []
                    for m in meds:
                        if isinstance(m, str):
                            # Old format: just string
                            converted_meds.append({"name": m, "dosage": "", "frequency": [], "time": ""})
                        elif isinstance(m, dict):
                            # Check if frequency is string (old) or array (new)
                            freq = m.get("frequency", [])
                            if isinstance(freq, str):
                                # Old format: string frequency
                                converted_meds.append({
                                    "name": m.get("name", ""),
                                    "dosage": m.get("dosage", ""),
                                    "frequency": [freq] if freq else [],
                                    "time": m.get("time", "")
                                })
                            else:
                                # New format: array frequency
                                converted_meds.append({
                                    "name": m.get("name", ""),
                                    "dosage": m.get("dosage", ""),
                                    "frequency": freq if isinstance(freq, list) else [],
                                    "time": m.get("time", "")
                                })
                        else:
                            converted_meds.append({"name": str(m), "dosage": "", "frequency": [], "time": ""})
                    patient['medications'] = converted_meds
                else:
                    patient['medications'] = []
            except Exception as e:
                print(f"Error parsing medications: {e}")
                patient['medications'] = []
        if patient.get('call_schedule'):
            try:
                import json
                patient['call_schedule'] = json.loads(patient['call_schedule'])
            except:
                patient['call_schedule'] = []
    return patients

@app.post("/patients/")
async def create_patient(patient: PatientCreate):
    """Create a new patient"""
    try:
        # Convert medications to dict format for storage
        medications_list = [med.dict() if isinstance(med, Medication) else med for med in patient.medications]
        
        patient_id = db.create_patient(
            name=patient.name,
            phone=patient.phone,
            gestational_age_weeks=patient.gestational_age_weeks,
            risk_factors=patient.risk_factors,
            medications=medications_list,
            risk_category=patient.risk_category
        )
        
        # Generate IVR schedule
        schedule = generate_ivr_schedule(patient_id, patient)
        db.update_patient(patient_id, call_schedule=schedule)
        
        return {"id": patient_id, "message": "Patient created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    """Get a specific patient"""
    patient = db.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Parse JSON fields
    import json
    if patient.get('risk_factors'):
        try:
            patient['risk_factors'] = json.loads(patient['risk_factors'])
        except:
            patient['risk_factors'] = []
    if patient.get('medications'):
        try:
            meds = json.loads(patient['medications'])
            # Ensure medications are in the correct format
            if meds and isinstance(meds, list):
                # Convert old string format to new format if needed
                if len(meds) > 0 and isinstance(meds[0], str):
                    patient['medications'] = [{"name": m, "dosage": "", "frequency": ""} for m in meds]
                else:
                    patient['medications'] = meds
            else:
                patient['medications'] = []
        except:
            patient['medications'] = []
    if patient.get('call_schedule'):
        try:
            patient['call_schedule'] = json.loads(patient['call_schedule'])
        except:
            patient['call_schedule'] = []
    
    return patient

@app.put("/patients/{patient_id}")
async def update_patient(patient_id: int, patient_update: PatientUpdate):
    """Update a patient"""
    update_data = patient_update.dict(exclude_unset=True)
    
    # Handle medications conversion
    if 'medications' in update_data and update_data['medications'] is not None:
        medications_list = [med.dict() if isinstance(med, Medication) else med for med in update_data['medications']]
        update_data['medications'] = medications_list
    
    success = db.update_patient(patient_id, **update_data)
    
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Regenerate schedule if relevant fields changed
    if any(key in update_data for key in ['gestational_age_weeks', 'risk_factors', 'medications', 'risk_category']):
        patient = db.get_patient(patient_id)
        if patient:
            import json
            meds = json.loads(patient.get('medications', '[]'))
            # Convert medication dicts to Medication objects if needed
            if meds and isinstance(meds, list) and len(meds) > 0:
                converted_meds = []
                for m in meds:
                    if isinstance(m, dict):
                        # Ensure frequency is array and time exists
                        freq = m.get("frequency", [])
                        if isinstance(freq, str):
                            freq = [freq] if freq else []
                        converted_meds.append(Medication(
                            name=m.get("name", ""),
                            dosage=m.get("dosage", ""),
                            frequency=freq if isinstance(freq, list) else [],
                            time=m.get("time", "")
                        ))
                    elif isinstance(m, str):
                        converted_meds.append(Medication(name=m, dosage="", frequency=[], time=""))
                meds = converted_meds
            
            patient_data = PatientCreate(
                name=patient['name'],
                phone=patient['phone'],
                gestational_age_weeks=patient['gestational_age_weeks'],
                risk_factors=json.loads(patient.get('risk_factors', '[]')),
                medications=meds,
                risk_category=patient.get('risk_category', 'low')
            )
            schedule = generate_ivr_schedule(patient_id, patient_data)
            db.update_patient(patient_id, call_schedule=schedule)
    
    return {"message": "Patient updated successfully"}

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: int):
    """Delete a patient and all associated data"""
    try:
        success = db.delete_patient(patient_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found or could not be deleted")
        
        return {"message": "Patient deleted successfully"}
    except Exception as e:
        print(f"Error in delete_patient endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting patient: {str(e)}")

@app.post("/generate_comprehensive_ivr_schedule")
async def generate_comprehensive_ivr_schedule(request: ScheduleRequest):
    """Generate comprehensive IVR schedule for a patient"""
    patient_id = request.patient_id
    patient = db.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    import json
    patient_data = PatientCreate(
        name=patient['name'],
        phone=patient['phone'],
        gestational_age_weeks=patient['gestational_age_weeks'],
        risk_factors=json.loads(patient.get('risk_factors', '[]')),
        medications=json.loads(patient.get('medications', '[]')),
        risk_category=patient.get('risk_category', 'low')
    )
    
    schedule = generate_ivr_schedule(patient_id, patient_data)
    db.update_patient(patient_id, call_schedule=schedule)
    
    return {"schedule": schedule, "message": "IVR schedule generated successfully"}

@app.get("/upcoming-calls-summary")
async def get_upcoming_calls_summary():
    """Get summary of upcoming calls (limited to 10 most recent)"""
    calls = db.get_upcoming_calls(limit=10)
    return {"calls": calls, "count": len(calls)}

@app.put("/patients/{patient_id}/ivr-schedule")
async def update_ivr_schedule(patient_id: int, schedule: List[IVRScheduleItem]):
    """Update patient's IVR schedule"""
    schedule_dict = [item.dict() for item in schedule]
    success = db.update_patient(patient_id, call_schedule=schedule_dict)
    
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"message": "IVR schedule updated successfully"}

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    """Handle inbound Twilio voice calls"""
    form_data = await request.form()
    form_dict = dict(form_data)
    twiml = twilio_service.handle_inbound_call(form_dict)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/handle_key")
async def twilio_handle_key(request: Request):
    """Handle key press during call"""
    form_data = await request.form()
    form_dict = dict(form_data)
    twiml = twilio_service.handle_key_press(form_dict)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/handle_recording")
async def twilio_handle_recording(request: Request):
    """Handle recorded message"""
    form_data = await request.form()
    form_dict = dict(form_data)
    twiml = twilio_service.handle_recording(form_dict)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/process_message")
async def process_twilio_message(request: dict):
    """Handle inbound Twilio messages"""
    return twilio_service.handle_inbound_call(request)

@app.post("/messages/{message_id}/process")
async def process_message(message_id: int, message_data: MessageProcess):
    """Process a pending patient message"""
    # Get message from database
    pending_messages = db.get_pending_messages()
    message = next((m for m in pending_messages if m['id'] == message_id), None)
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get patient context
    patient = db.get_patient(message['patient_id'])
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    import json
    patient_context = {
        'name': patient['name'],
        'gestational_age_weeks': patient['gestational_age_weeks'],
        'risk_category': patient.get('risk_category', 'low'),
        'risk_factors': json.loads(patient.get('risk_factors', '[]'))
    }
    
    # Process message with AI
    response = gemma_ai.process_patient_message(message_data.transcript, patient_context)
    
    # Update message in database
    db.update_message(message_id, gemma_response=response, status="processed")
    
    # Schedule callback if needed
    callback_time = datetime.now() + timedelta(hours=24)
    db.update_message(message_id, scheduled_callback=callback_time)
    
    return {"response": response, "scheduled_callback": callback_time.isoformat()}

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data"""
    patients = db.get_all_patients()
    calls = db.get_upcoming_calls(limit=10)
    pending_messages = db.get_pending_messages()
    
    return {
        "total_patients": len(patients),
        "upcoming_calls": len(calls),
        "pending_messages": len(pending_messages),
        "high_risk_patients": len([p for p in patients if p.get('risk_category') == 'high']),
        "low_risk_patients": len([p for p in patients if p.get('risk_category') == 'low'])
    }

@app.post("/calls/{call_id}/execute")
async def execute_call(call_id: int):
    """Execute a scheduled call"""
    try:
        # Get call details directly from database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cl.*, p.name, p.phone 
            FROM call_logs cl
            JOIN patients p ON cl.patient_id = p.id
            WHERE cl.id = ?
        """, (call_id,))
        call_row = cursor.fetchone()
        conn.close()
        
        if not call_row:
            raise HTTPException(status_code=404, detail="Call not found")
        
        call = dict(call_row)
        
        # Check if call is already completed
        if call.get('status') == 'completed':
            raise HTTPException(status_code=400, detail="Call already completed")
        
        # Make the call
        call_sid = twilio_service.make_call(
            to_number=call['phone'],
            message_text=call.get('message_text', ''),
            patient_id=call['patient_id']
        )
        
        if call_sid:
            # Update call status
            db.update_call_status(call_id, 'completed', datetime.now())
            return {"message": "Call executed successfully", "call_sid": call_sid}
        else:
            raise HTTPException(status_code=500, detail="Failed to make call. Check Twilio configuration and ensure SERVER_URL is set correctly (use ngrok for local testing).")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def generate_ivr_schedule(patient_id: int, patient: PatientCreate) -> List[Dict]:
    """Generate comprehensive IVR schedule for a patient"""
    schedule = []
    current_time = datetime.now()
    gestational_age = patient.gestational_age_weeks
    weeks_remaining = max(0, 40 - gestational_age)
    
    # Determine call frequency based on risk category
    if patient.risk_category == "high":
        call_frequency_days = 3
    elif patient.risk_category == "medium":
        call_frequency_days = 5
    else:
        call_frequency_days = 7
    
    # Generate weekly check-ins
    for week in range(min(weeks_remaining, 20)):  # Up to 20 weeks of calls
        call_time = current_time + timedelta(days=week * call_frequency_days)
        
        # Weekly check-in
        message = gemma_ai.generate_personalized_ivr_message(
            topic="weekly_checkin",
            patient_name=patient.name,
            gestational_age_weeks=gestational_age + week,
            risk_factors=patient.risk_factors,
            risk_category=patient.risk_category,
            medications=patient.medications
        )
        
        schedule.append({
            "call_type": "weekly_checkin",
            "scheduled_time": call_time.isoformat(),
            "message_text": message,
            "status": "scheduled"
        })
        
        # Create call log
        db.create_call_log(
            patient_id=patient_id,
            call_type="weekly_checkin",
            status="scheduled",
            message_text=message,
            scheduled_time=call_time
        )
    
    # Generate medication reminders based on days and times
    if patient.medications:
        # Convert medications to list of strings for message generation
        med_strings = []
        for med in patient.medications:
            if isinstance(med, dict):
                med_str = med.get("name", "")
                if med.get("dosage"):
                    med_str += f" {med.get('dosage')}"
                frequency = med.get("frequency", [])
                if frequency:
                    if isinstance(frequency, list):
                        med_str += f" ({', '.join(frequency)})"
                    else:
                        med_str += f" ({frequency})"
                med_strings.append(med_str)
            elif isinstance(med, Medication):
                med_str = med.name
                if med.dosage:
                    med_str += f" {med.dosage}"
                if med.frequency:
                    if isinstance(med.frequency, list):
                        med_str += f" ({', '.join(med.frequency)})"
                    else:
                        med_str += f" ({med.frequency})"
                med_strings.append(med_str)
            else:
                med_strings.append(str(med))
        
        # Generate calls for each medication based on days and times
        from datetime import datetime, time as dt_time
        day_map = {'Sun': 6, 'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5}
        
        for med in patient.medications:
            med_dict = med.dict() if isinstance(med, Medication) else med
            med_name = med_dict.get("name", "")
            med_dosage = med_dict.get("dosage", "")
            med_days = med_dict.get("frequency", [])
            med_time = med_dict.get("time", "09:00")  # Default to 9 AM if no time specified
            
            if not med_days or len(med_days) == 0:
                continue
            
            # Parse time
            try:
                if isinstance(med_time, str) and ':' in med_time:
                    hour, minute = map(int, med_time.split(':'))
                else:
                    hour, minute = 9, 0
            except:
                hour, minute = 9, 0
            
            # Generate calls for the next 20 weeks
            for week in range(min(weeks_remaining, 20)):
                for day_name in med_days:
                    if day_name not in day_map:
                        continue
                    
                    # Calculate the next occurrence of this day
                    day_of_week = day_map[day_name]
                    days_ahead = day_of_week - current_time.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    
                    # Add weeks offset
                    days_ahead += week * 7
                    
                    call_date = current_time + timedelta(days=days_ahead)
                    call_time = call_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Only schedule if it's in the future
                    if call_time > current_time:
                        message = gemma_ai.generate_personalized_ivr_message(
                            topic="medication_reminder",
                            patient_name=patient.name,
                            gestational_age_weeks=gestational_age + week,
                            risk_factors=patient.risk_factors,
                            risk_category=patient.risk_category,
                            medications=[f"{med_name} {med_dosage}".strip()]
                        )
                        
                        schedule.append({
                            "call_type": "medication_reminder",
                            "scheduled_time": call_time.isoformat(),
                            "message_text": message,
                            "status": "scheduled"
                        })
                        
                        db.create_call_log(
                            patient_id=patient_id,
                            call_type="medication_reminder",
                            status="scheduled",
                            message_text=message,
                            scheduled_time=call_time
                        )
    
    # High-risk monitoring calls
    if patient.risk_category == "high":
        for week in range(min(weeks_remaining, 20)):
            call_time = current_time + timedelta(days=week * call_frequency_days + 1)
            
            message = gemma_ai.generate_personalized_ivr_message(
                topic="high_risk_monitoring",
                patient_name=patient.name,
                gestational_age_weeks=gestational_age + week,
                risk_factors=patient.risk_factors,
                risk_category=patient.risk_category,
                medications=patient.medications
            )
            
            schedule.append({
                "call_type": "high_risk_monitoring",
                "scheduled_time": call_time.isoformat(),
                "message_text": message,
                "status": "scheduled"
            })
            
            db.create_call_log(
                patient_id=patient_id,
                call_type="high_risk_monitoring",
                status="scheduled",
                message_text=message,
                scheduled_time=call_time
            )
    
    return schedule

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

