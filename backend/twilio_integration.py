import os
import yaml
from typing import Dict, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from database import Database

class TwilioService:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.db = Database()
        
        # Twilio credentials
        account_sid = os.getenv("TWILIO_ACCOUNT_SID") or self.config.get("twilio", {}).get("account_sid")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN") or self.config.get("twilio", {}).get("auth_token")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER") or self.config.get("twilio", {}).get("from_number")
        
        if account_sid and auth_token:
            self.client = Client(account_sid, auth_token)
        else:
            print("⚠️ Twilio credentials not found. Some features will be disabled.")
            self.client = None
    
    def _load_config(self, config_path: str) -> dict:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def make_call(self, to_number: str, message_text: str, patient_id: int = None) -> Optional[str]:
        """Make a phone call using Twilio"""
        if not self.client:
            print("⚠️ Twilio client not initialized. Cannot make call.")
            return None
        
        try:
            # Create TwiML URL or use webhook
            # You need to replace this with your actual server URL
            # Get server URL - for production, this should be your public URL
            # For local testing, use ngrok URL
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
            
            # Ensure URL is publicly accessible (use ngrok for local testing)
            webhook_url = f"{server_url}/twilio/voice"
            
            print(f"Making call to {to_number} using webhook: {webhook_url}")
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=webhook_url,
                method="POST"
            )
            
            print(f"Call initiated: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"❌ Error making call: {e}")
            return None
    
    def handle_inbound_call(self, request: Dict) -> str:
        """Handle inbound Twilio call and generate TwiML response"""
        response = VoiceResponse()
        
        # Get caller's phone number
        caller_number = request.get("From", "")
        
        # Find patient by phone number
        patients = self.db.get_all_patients()
        patient = next((p for p in patients if p.get("phone") == caller_number), None)
        
        if patient:
            # Get the next scheduled call message for this patient
            import json
            call_schedule = json.loads(patient.get("call_schedule", "[]"))
            
            if call_schedule:
                # Get the next scheduled message
                from datetime import datetime
                now = datetime.now()
                upcoming_calls = [
                    c for c in call_schedule
                    if datetime.fromisoformat(c["scheduled_time"]) > now
                ]
                
                if upcoming_calls:
                    next_call = upcoming_calls[0]
                    message_text = next_call.get("message_text", "Hello, this is Mada.")
                else:
                    message_text = f"Hello {patient.get('name', 'Patient')}, this is Mada. How can we help you today?"
            else:
                message_text = f"Hello {patient.get('name', 'Patient')}, this is Mada. How can we help you today?"
        else:
            message_text = "Hello, this is Mada. Thank you for calling."
        
        # Say the message
        response.say(message_text, voice="alice", language="en-US")
        
        # Add "Press 1" functionality
        gather = response.gather(
            num_digits=1,
            action="/twilio/handle_key",
            method="POST",
            timeout=10
        )
        gather.say("Press 1 if you'd like to leave a message for our medical team.", voice="alice")
        
        # If no input, hang up
        response.say("Thank you for calling SabCare. Goodbye.", voice="alice")
        response.hangup()
        
        return str(response)
    
    def handle_key_press(self, request: Dict) -> str:
        """Handle key press during call"""
        response = VoiceResponse()
        digits = request.get("Digits", "")
        
        if digits == "1":
            # Record message
            response.say("Please leave your message after the tone. Press the pound key when you're done.", voice="alice")
            response.record(
                action="/twilio/handle_recording",
                method="POST",
                finish_on_key="#",
                max_length=60
            )
        else:
            response.say("Thank you for calling. Goodbye.", voice="alice")
            response.hangup()
        
        return str(response)
    
    def handle_recording(self, request: Dict) -> str:
        """Handle recorded message"""
        response = VoiceResponse()
        recording_url = request.get("RecordingUrl", "")
        caller_number = request.get("From", "")
        
        # Find patient
        patients = self.db.get_all_patients()
        patient = next((p for p in patients if p.get("phone") == caller_number), None)
        
        if patient:
            # Save message to database
            self.db.create_message(
                patient_id=patient["id"],
                message_audio=recording_url,
                status="pending"
            )
            response.say("Thank you for your message. We will get back to you soon. Goodbye.", voice="alice")
        else:
            response.say("Message received. Thank you. Goodbye.", voice="alice")
        
        response.hangup()
        return str(response)
    
    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        """Send SMS using Twilio"""
        if not self.client:
            print("⚠️ Twilio client not initialized. Cannot send SMS.")
            return None
        
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.from_number,
                body=message
            )
            return message.sid
        except Exception as e:
            print(f"❌ Error sending SMS: {e}")
            return None

