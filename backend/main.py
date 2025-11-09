from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import sys
import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from twilio_integration import TwilioService

from contextlib import asynccontextmanager

# Initialize services (must be before scheduler functions)
db = Database()
twilio_service = TwilioService()

# Initialize scheduler for automatic call execution (must be before app creation)
scheduler = AsyncIOScheduler()

async def check_and_execute_calls():
    """Background task to check for scheduled calls and execute them"""
    try:
        from datetime import datetime
        current_time = datetime.now()
        
        # Get calls that are scheduled and due
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cl.id, cl.patient_id, cl.call_type, cl.message_text, cl.scheduled_time, p.name, p.phone
            FROM call_logs cl
            JOIN patients p ON cl.patient_id = p.id
            WHERE cl.status = 'scheduled'
            AND datetime(cl.scheduled_time) <= datetime(?)
            ORDER BY cl.scheduled_time ASC
            LIMIT 10
        """, (current_time.isoformat(),))
        
        calls_to_execute = cursor.fetchall()
        conn.close()
        
        if calls_to_execute:
            print(f"🕐 Found {len(calls_to_execute)} calls to execute")
        
        for call_row in calls_to_execute:
            call = dict(call_row)
            call_id = call['id']
            
            try:
                # Use TwiML directly for local testing
                server_url = os.getenv("SERVER_URL", "http://localhost:8000")
                use_twiml = "localhost" in server_url or "127.0.0.1" in server_url
                
                print(f"📞 Auto-executing call {call_id} for {call['name']} at {call['scheduled_time']}")
                
                call_sid = twilio_service.make_call(
                    to_number=call['phone'],
                    message_text=call.get('message_text', ''),
                    patient_id=call['patient_id'],
                    use_twiml=use_twiml
                )
                
                if call_sid:
                    # Update call status
                    db.update_call_status(call_id, 'completed', datetime.now())
                    print(f"✅ Call {call_id} executed successfully (SID: {call_sid})")
                else:
                    print(f"❌ Failed to execute call {call_id}")
            except Exception as e:
                print(f"❌ Error executing call {call_id}: {e}")
    except Exception as e:
        print(f"❌ Error in check_and_execute_calls: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage scheduler lifecycle"""
    # Startup
    # Check for calls every 30 seconds
    scheduler.add_job(
        check_and_execute_calls,
        trigger=IntervalTrigger(seconds=30),
        id="execute_scheduled_calls",
        name="Execute scheduled calls",
        replace_existing=True
    )
    scheduler.start()
    print("✅ Call scheduler started - checking for scheduled calls every 30 seconds")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    print("🛑 Call scheduler stopped")

# Create FastAPI app with lifespan
app = FastAPI(title="SabCare API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services are initialized above (before app creation)

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
        medications_list = [med.model_dump() if hasattr(med, 'model_dump') else (med.dict() if hasattr(med, 'dict') else med) for med in patient.medications]
        
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
            patient['call_schedule'] = json.loads(patient['call_schedule'])
        except:
            patient['call_schedule'] = []
    
    return patient

@app.put("/patients/{patient_id}")
async def update_patient(patient_id: int, patient_update: PatientUpdate):
    """Update a patient"""
    try:
        update_data = patient_update.dict(exclude_unset=True)
        
        # Handle medications conversion
        if 'medications' in update_data and update_data['medications'] is not None:
            medications_list = [med.dict() if isinstance(med, Medication) else med for med in update_data['medications']]
            update_data['medications'] = medications_list
        
        success = db.update_patient(patient_id, **update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
    except ValueError as e:
        # Handle duplicate phone number error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
async def get_upcoming_calls_summary(patient_id: Optional[int] = None):
    """Get summary of upcoming calls (limited to 10 most recent)
    
    Returns only future scheduled calls, ordered by scheduled time (earliest first).
    Optional patient_id parameter to filter calls for a specific patient.
    """
    from datetime import datetime
    calls = db.get_upcoming_calls(limit=10, patient_id=patient_id)
    # Add timestamp to response to help with cache busting
    return {
        "calls": calls, 
        "count": len(calls),
        "timestamp": datetime.now().isoformat()
    }

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
    """Handle key press during call (DISABLED - feature removed)"""
    form_data = await request.form()
    form_dict = dict(form_data)
    twiml = twilio_service.handle_key_press(form_dict)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twilio/handle_recording")
async def twilio_handle_recording(request: Request):
    """Handle recorded message (DISABLED - feature removed)"""
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
    """Process a pending patient message (DISABLED - message recording feature removed)"""
    raise HTTPException(status_code=410, detail="Message processing feature has been removed. Patient message recording is no longer available.")

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

@app.delete("/calls/{call_id}")
async def cancel_call(call_id: int):
    """Cancel/delete a scheduled call"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if call exists
        cursor.execute("SELECT id, status FROM call_logs WHERE id = ?", (call_id,))
        call_row = cursor.fetchone()
        
        if not call_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Call not found")
        
        call = dict(call_row)
        
        # If call is already completed, just mark it as cancelled
        # Otherwise, delete it
        if call.get('status') == 'completed':
            # Mark as cancelled
            cursor.execute("""
                UPDATE call_logs 
                SET status = 'cancelled'
                WHERE id = ?
            """, (call_id,))
        else:
            # Delete the call
            cursor.execute("DELETE FROM call_logs WHERE id = ?", (call_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Call cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def generate_simple_message(
    topic: str,
    patient_name: str,
    gestational_age_weeks: int,
    risk_factors: List[str] = None,
    risk_category: str = "low",
    medications: List[str] = None
) -> str:
    """Generate simple IVR messages without AI model
    
    Args:
        topic: Type of message (weekly_checkin, medication_reminder, high_risk_monitoring)
        patient_name: Patient's name
        gestational_age_weeks: Current gestational age in weeks
        risk_factors: List of risk factors
        risk_category: Risk category (low, medium, high)
        medications: List of medication strings
    """
    risk_factors = risk_factors or []
    medications = medications or []
    
    if topic == "weekly_checkin":
        message = f"Hello {patient_name}, this is your week {gestational_age_weeks} pregnancy check-in from SabCare. "
        if gestational_age_weeks < 12:
            message += "During your first trimester, it's important to take your prenatal vitamins and get plenty of rest."
        elif gestational_age_weeks < 28:
            message += "You're in your second trimester. Continue with regular prenatal care and maintain a healthy diet."
        else:
            message += "You're in your third trimester. Monitor for any signs of labor and stay in close contact with your healthcare provider."
    
    elif topic == "medication_reminder":
        if medications:
            med_list = ", ".join(medications)
            message = f"Hello {patient_name}, this is your reminder to take your medications: {med_list}. "
        else:
            message = f"Hello {patient_name}, this is your medication reminder. "
        message += "Please take your medications as prescribed by your healthcare provider."
    
    elif topic == "high_risk_monitoring":
        message = f"Hello {patient_name}, this is your high-risk pregnancy monitoring call from SabCare. "
        if risk_factors:
            message += f"Given your risk factors including {', '.join(risk_factors)}, "
        message += "it's important to monitor your symptoms closely and contact your healthcare provider immediately if you experience any concerns."
    
    else:
        message = f"Hello {patient_name}, this is a message from your SabCare pregnancy care team. "
        message += "Please stay in touch with your healthcare provider regarding your pregnancy care."
    
    if risk_category == "high":
        message += " Given your high-risk status, please be extra vigilant about any changes in your condition."
    
    return message

def convert_medications_to_strings(medications: List) -> List[str]:
    """Convert medication objects/dicts to string format"""
    med_strings = []
    for med in medications:
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
    return med_strings

def generate_ivr_schedule(patient_id: int, patient: PatientCreate) -> List[Dict]:
    """Generate comprehensive IVR schedule for a patient"""
    schedule = []
    call_logs_to_create = []  # Batch all call log creations
    current_time = datetime.now()
    gestational_age = patient.gestational_age_weeks
    weeks_remaining = max(0, 40 - gestational_age)
    
    # Convert medications to strings for AI model
    medications_strings = convert_medications_to_strings(patient.medications)
    
    # Determine call frequency based on risk category
    if patient.risk_category == "high":
        call_frequency_days = 3
    elif patient.risk_category == "medium":
        call_frequency_days = 5
    else:
        call_frequency_days = 7
    
    # Generate weekly check-ins
    # Start from tomorrow to avoid scheduling calls in the past
    # For test calls, we can schedule for today if needed
    start_day = 1  # Start from tomorrow (1 day ahead)
    for week in range(min(weeks_remaining, 20)):  # Up to 20 weeks of calls
        call_time = current_time + timedelta(days=start_day + (week * call_frequency_days))
        # Set a default time (e.g., 9 AM) for weekly check-ins
        call_time = call_time.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Weekly check-in
        message = generate_simple_message(
            topic="weekly_checkin",
            patient_name=patient.name,
            gestational_age_weeks=gestational_age + week,
            risk_factors=patient.risk_factors,
            risk_category=patient.risk_category,
            medications=medications_strings
        )
        
        schedule.append({
            "call_type": "weekly_checkin",
            "scheduled_time": call_time.isoformat(),
            "message_text": message,
            "status": "scheduled"
        })
        
        # Add to batch for call log creation
        call_logs_to_create.append({
            "patient_id": patient_id,
            "call_type": "weekly_checkin",
            "status": "scheduled",
            "message_text": message,
            "scheduled_time": call_time
        })
    
    # Generate medication reminders based on days and times
    if patient.medications:
        # Generate calls for each medication based on days and times
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
            # For each day in the frequency, calculate the next occurrence for each week
            day_of_week_map = {}  # Map each day to its occurrences
            
            for day_name in med_days:
                if day_name not in day_map:
                    continue
                
                day_of_week = day_map[day_name]
                current_day = current_time.weekday()
                days_ahead = day_of_week - current_day
                
                # Calculate the base occurrence (first time this day occurs)
                if days_ahead == 0:
                    # Today is the target day
                    call_time_today = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if call_time_today > current_time:
                        # Time hasn't passed today, first occurrence is today
                        base_days_ahead = 0
                    else:
                        # Time has passed today, first occurrence is next week
                        base_days_ahead = 7
                elif days_ahead < 0:
                    # Target day already happened this week, first occurrence is next week
                    base_days_ahead = 7 + days_ahead
                else:
                    # Target day is later this week
                    base_days_ahead = days_ahead
                
                # Store the base days ahead for this day
                if day_name not in day_of_week_map:
                    day_of_week_map[day_name] = base_days_ahead
            
            # Now generate calls for each week and each day
            for week in range(min(weeks_remaining, 20)):
                for day_name in med_days:
                    if day_name not in day_map or day_name not in day_of_week_map:
                        continue
                    
                    # Calculate days ahead for this specific week
                    base_days_ahead = day_of_week_map[day_name]
                    days_ahead = base_days_ahead + (week * 7)
                    
                    # Calculate the call time
                    call_date = current_time + timedelta(days=days_ahead)
                    call_time = call_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Only schedule if it's in the future
                    if call_time > current_time:
                        message = generate_simple_message(
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
                        
                        # Add to batch for call log creation
                        call_logs_to_create.append({
                            "patient_id": patient_id,
                            "call_type": "medication_reminder",
                            "status": "scheduled",
                            "message_text": message,
                            "scheduled_time": call_time
                        })
    
    # High-risk monitoring calls
    if patient.risk_category == "high":
        for week in range(min(weeks_remaining, 20)):
            call_time = current_time + timedelta(days=week * call_frequency_days + 1)
            
            message = generate_simple_message(
                topic="high_risk_monitoring",
                patient_name=patient.name,
                gestational_age_weeks=gestational_age + week,
                risk_factors=patient.risk_factors,
                risk_category=patient.risk_category,
                medications=medications_strings
            )
            
            schedule.append({
                "call_type": "high_risk_monitoring",
                "scheduled_time": call_time.isoformat(),
                "message_text": message,
                "status": "scheduled"
            })
            
            # Add to batch for call log creation
            call_logs_to_create.append({
                "patient_id": patient_id,
                "call_type": "high_risk_monitoring",
                "status": "scheduled",
                "message_text": message,
                "scheduled_time": call_time
            })
    
    # Create all call logs in a single batch transaction
    if call_logs_to_create:
        try:
            db.create_call_logs_batch(call_logs_to_create)
        except Exception as e:
            # If batch creation fails, log error but don't fail the entire operation
            # The schedule will still be saved to the patient record
            print(f"Warning: Failed to create some call logs: {e}")
    
    return schedule

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

