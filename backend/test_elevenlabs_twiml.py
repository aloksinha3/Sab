"""Test ElevenLabs TwiML generation"""
from elevenlabs_service import ElevenLabsService

service = ElevenLabsService()
if service.enabled:
    twiml = service.get_inbound_call_twiml("+1234567890")
    print("Generated TwiML:")
    print(twiml)
else:
    print("ElevenLabs not enabled")
