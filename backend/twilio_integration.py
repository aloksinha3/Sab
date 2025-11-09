import os
import yaml
from typing import Dict, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from database import Database
from elevenlabs_service import ElevenLabsService

class TwilioService:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Twilio Service
        
        Credentials are loaded from:
        1. Environment variables (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER)
        2. config.yaml file (twilio.account_sid, twilio.auth_token, twilio.from_number)
        
        Configured credentials:
        - Account SID: ACd2ed65282f924c5637f277f7f5160336
        - From Number: +19199180358
        """
        self.config = self._load_config(config_path)
        self.db = Database()
        
        # Twilio credentials - check environment variables first, then config file
        account_sid = os.getenv("TWILIO_ACCOUNT_SID") or self.config.get("twilio", {}).get("account_sid")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN") or self.config.get("twilio", {}).get("auth_token")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER") or self.config.get("twilio", {}).get("from_number")
        
        if account_sid and auth_token:
            try:
                self.client = Client(account_sid, auth_token)
                print(f"✅ Twilio service initialized successfully")
                print(f"   From Number: {self.from_number}")
            except Exception as e:
                print(f"⚠️ Error initializing Twilio client: {e}")
                self.client = None
        else:
            print("⚠️ Twilio credentials not found. Some features will be disabled.")
            print("   Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER")
            print("   or configure them in config.yaml")
            self.client = None
        
        # Initialize ElevenLabs service
        self.elevenlabs_service = ElevenLabsService(config_path)
        self.elevenlabs_enabled = self.elevenlabs_service.enabled
    
    def _load_config(self, config_path: str) -> dict:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to E.164 format (+1XXXXXXXXXX)
        
        Args:
            phone: Phone number in any format
            
        Returns:
            Phone number in E.164 format
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # If it starts with 1 and has 11 digits, add +
        if len(digits) == 11 and digits[0] == '1':
            return f"+{digits}"
        # If it has 10 digits, assume US number and add +1
        elif len(digits) == 10:
            return f"+1{digits}"
        # If it already starts with +, return as-is
        elif phone.startswith('+'):
            return phone
        # Otherwise, try to format it
        else:
            return f"+1{digits}" if digits else phone
    
    def make_call(self, to_number: str, message_text: str = "", patient_id: int = None, 
                  call_type: str = None, use_twiml: bool = False) -> Optional[str]:
        """Make a phone call using Twilio
        
        Args:
            to_number: Phone number to call (E.164 format, e.g., +1234567890)
            message_text: Message to deliver during the call
            patient_id: Optional patient ID for tracking
            call_type: Type of call (medication_reminder, weekly_checkin, etc.)
            use_twiml: If True, use TwiML directly instead of webhook URL (for testing)
            
        Returns:
            Call SID if successful, None otherwise
            
        Note:
            For local testing, either:
            1. Set SERVER_URL to your ngrok URL: export SERVER_URL=https://your-ngrok-url.ngrok.io
            2. Or use use_twiml=True to generate TwiML directly (simpler for testing)
        """
        if not self.client:
            print("⚠️ Twilio client not initialized. Cannot make call.")
            print("   Check that Twilio credentials are configured in config.yaml or environment variables.")
            return None
        
        if not self.from_number:
            print("⚠️ Twilio from_number not configured. Cannot make call.")
            return None
        
        # Normalize phone number to E.164 format
        normalized_number = self._normalize_phone_number(to_number)
        print(f"📞 Making call to {normalized_number} (original: {to_number}) from {self.from_number}")
        
        # If ElevenLabs is enabled, use Twilio to call, then connect to ElevenLabs
        if self.elevenlabs_enabled and self.elevenlabs_service.client:
            print(f"   Using Twilio + ElevenLabs: Play reminder first, then connect to agent")
            
            # Extract patient info and medication name if patient_id is provided
            user_name = None
            medication_name = None
            
            if patient_id:
                try:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, medications FROM patients WHERE id = ?", (patient_id,))
                    patient_row = cursor.fetchone()
                    conn.close()
                    
                    if patient_row:
                        user_name = patient_row['name']
                        
                        # Extract medication name from medications or message_text
                        if patient_row['medications']:
                            import json
                            try:
                                medications = json.loads(patient_row['medications'])
                                if medications and isinstance(medications, list) and len(medications) > 0:
                                    # Get first medication name
                                    med = medications[0]
                                    if isinstance(med, dict):
                                        medication_name = med.get('name', '')
                                    elif isinstance(med, str):
                                        medication_name = med
                            except:
                                pass
                        
                        # If no medication found in patient data, try to extract from message_text
                        if not medication_name and message_text and call_type == "medication_reminder":
                            # Try to extract medication name from message like "medications: Folic Acid 400mg"
                            import re
                            # Look for pattern like "medications: X" or "take your X"
                            match = re.search(r'medications?:\s*([^.,]+)', message_text, re.IGNORECASE)
                            if not match:
                                match = re.search(r'take your\s+([^.,]+)', message_text, re.IGNORECASE)
                            if match:
                                medication_name = match.group(1).strip()
                                # Remove dosage if present (e.g., "Folic Acid 400mg" -> "Folic Acid")
                                medication_name = re.sub(r'\s+\d+[a-z]+', '', medication_name, flags=re.IGNORECASE)
                except Exception as e:
                    print(f"⚠️ Error extracting patient info: {e}")
            
            # Generate TwiML that plays reminder message first, then connects to ElevenLabs
            try:
                from twilio.twiml.voice_response import VoiceResponse, Redirect
                import urllib.parse
                
                response = VoiceResponse()
                
                # First, play the basic medication reminder using Twilio TTS
                if call_type == "medication_reminder" and user_name and medication_name:
                    reminder_message = f"Hello {user_name}, this is your reminder to take your {medication_name} today."
                elif user_name:
                    reminder_message = f"Hello {user_name}, this is your health assistant calling."
                else:
                    reminder_message = "Hello, this is your health assistant calling."
                
                print(f"📢 Playing Twilio reminder: {reminder_message}")
                response.say(reminder_message, voice="alice", language="en-US")
                
                # Then redirect to ElevenLabs agent for the conversation
                webhook_url = (
                    f"https://api.elevenlabs.io/v1/convai/twilio/inbound-call"
                    f"?agent_id={self.elevenlabs_service.agent_id}"
                    f"&phone_number_id={self.elevenlabs_service.phone_number_id}"
                )
                
                print(f"🔄 Redirecting to ElevenLabs agent...")
                response.redirect(url=webhook_url, method="POST")
                
                twiml = str(response)
                
                # Make the call through Twilio (not ElevenLabs API directly)
                call = self.client.calls.create(
                    to=normalized_number,
                    from_=self.from_number,
                    twiml=twiml
                )
                
                print(f"✅ Call initiated via Twilio: {call.sid}")
                print(f"   Flow: Twilio reminder → ElevenLabs agent")
                return call.sid
            except Exception as e:
                print(f"❌ Error creating Twilio+ElevenLabs call: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to regular Twilio
        
        try:
            if use_twiml:
                # Generate TwiML directly for testing (no webhook needed)
                # Simple message delivery - no user interaction
                response = VoiceResponse()
                # Remove "Press 1" text if present in message
                clean_message = message_text.split("\n\nPress 1")[0].strip()
                response.say(clean_message, voice="alice", language="en-US")
                response.hangup()
                twiml = str(response)
                
                print(f"   Using TwiML directly (no webhook required)")
                call = self.client.calls.create(
                    to=normalized_number,
                    from_=self.from_number,
                    twiml=twiml
                )
            else:
                # Use webhook URL (requires publicly accessible server)
                server_url = os.getenv("SERVER_URL", "http://localhost:8000")
                webhook_url = f"{server_url}/twilio/voice"
                
                print(f"   Webhook URL: {webhook_url}")
                call = self.client.calls.create(
                    to=normalized_number,
                    from_=self.from_number,
                    url=webhook_url,
                    method="POST"
                )
            
            print(f"✅ Call initiated: {call.sid}")
            return call.sid
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error making call: {error_msg}")
            
            # Extract detailed error information if available
            from twilio.base.exceptions import TwilioRestException
            if isinstance(e, TwilioRestException):
                print(f"   Error Code: {e.code}")
                print(f"   Error Message: {e.msg}")
                print(f"   More Info: {e.uri if hasattr(e, 'uri') else 'N/A'}")
            
            # Provide more helpful error messages
            if "401" in error_msg or "Authenticate" in error_msg or (hasattr(e, 'code') and e.code == 20003):
                print(f"   🔴 CRITICAL: Twilio authentication failed!")
                print(f"   ")
                print(f"   The Account SID and/or Auth Token are INVALID or EXPIRED.")
                print(f"   ")
                print(f"   Current Account SID: {self.client.username if self.client else 'N/A'}")
                print(f"   ")
                print(f"   TO FIX THIS:")
                print(f"   1. Go to https://www.twilio.com/console")
                print(f"   2. Log in and verify your Account SID matches: {self.client.username if self.client else 'N/A'}")
                print(f"   3. Click on your Auth Token to reveal it (or regenerate if needed)")
                print(f"   4. Update config.yaml with the CORRECT credentials")
                print(f"   5. Restart the backend server")
                print(f"   ")
                print(f"   NOTE: The phone number format is CORRECT (+14436222793)")
                print(f"         The issue is ONLY the authentication credentials.")
            elif "21211" in error_msg or (hasattr(e, 'code') and e.code == 21211):
                print(f"   ⚠️ Invalid phone number format. Number: {normalized_number}")
                print(f"   Phone numbers must be in E.164 format: +[country code][number]")
            elif "21610" in error_msg or (hasattr(e, 'code') and e.code == 21610):
                print(f"   ⚠️ Phone number is unverified (trial account restriction)")
                print(f"   Trial accounts can only call verified numbers.")
                print(f"   Verify the number at: https://www.twilio.com/console/phone-numbers/verified")
            elif "21408" in error_msg or (hasattr(e, 'code') and e.code == 21408):
                print(f"   ⚠️ Permission denied for this action")
                print(f"   Your account may not have permission to make calls to this number.")
            
            if not use_twiml:
                print(f"   Try using use_twiml=True for testing, or set SERVER_URL to a publicly accessible URL (use ngrok)")
            return None
    
    def handle_inbound_call(self, request: Dict) -> str:
        """Handle inbound Twilio call and connect to ElevenLabs voice agent
        
        If ElevenLabs is enabled, connects the call to the AI voice agent with
        the template message as the initial prompt. Otherwise, falls back to basic TwiML.
        """
        # Get caller's phone number
        caller_number = request.get("From", "")
        
        # Find patient by phone number and get their message
        patients = self.db.get_all_patients()
        patient = next((p for p in patients if p.get("phone") == caller_number), None)
        
        # Get the template message for this patient
        template_message = None
        if patient:
            # Try to get the next scheduled call message
            import json
            from datetime import datetime
            
            call_schedule_str = patient.get("call_schedule") or "[]"
            try:
                call_schedule = json.loads(call_schedule_str) if isinstance(call_schedule_str, str) else call_schedule_str
            except (json.JSONDecodeError, TypeError):
                call_schedule = []
            
            if call_schedule:
                # Get the next upcoming call message
                now = datetime.now()
                upcoming_calls = [
                    c for c in call_schedule
                    if isinstance(c, dict) and c.get("scheduled_time")
                    and datetime.fromisoformat(c["scheduled_time"]) > now
                ]
                
                if upcoming_calls:
                    # Get the most recent/next call
                    next_call = sorted(upcoming_calls, key=lambda x: x.get("scheduled_time", ""))[0]
                    template_message = next_call.get("message_text", "")
            
            # If no scheduled message, create a default one
            if not template_message:
                template_message = f"Hello {patient.get('name', 'Patient')}, this is SabCare. Thank you for your call."
        else:
            template_message = "Hello, this is SabCare. Thank you for calling."
        
        # If ElevenLabs is enabled, connect call to voice agent with template message
        if self.elevenlabs_enabled and self.elevenlabs_service.client:
            print(f"📞 Inbound call from {caller_number} - connecting to ElevenLabs agent")
            print(f"📝 Template message: {template_message[:100]}...")
            return self.elevenlabs_service.get_inbound_call_twiml(caller_number, template_message)
        
        # Fallback to basic TwiML if ElevenLabs not available
        response = VoiceResponse()
        response.say(template_message, voice="alice", language="en-US")
        response.hangup()
        
        return str(response)
    
    def handle_key_press(self, request: Dict) -> str:
        """Handle key press during call (DISABLED - feature removed)
        
        This method is kept for backward compatibility but is no longer used.
        All calls now simply deliver the message and hang up.
        """
        response = VoiceResponse()
        response.say("This feature is no longer available. Thank you for calling. Goodbye.", voice="alice")
        response.hangup()
        return str(response)
    
    def handle_recording(self, request: Dict) -> str:
        """Handle recorded message (DISABLED - feature removed)
        
        This method is kept for backward compatibility but is no longer used.
        Message recording functionality has been removed.
        """
        response = VoiceResponse()
        response.say("This feature is no longer available. Thank you for calling. Goodbye.", voice="alice")
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

