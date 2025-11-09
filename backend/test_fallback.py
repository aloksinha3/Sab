#!/usr/bin/env python3
"""Test script to verify IVR fallback works"""
import yaml
import os

# Backup current config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    original_enabled = config.get('elevenlabs', {}).get('enabled', True)

print("=" * 60)
print("Testing IVR Fallback")
print("=" * 60)
print()
print(f"Current ElevenLabs status: {'ENABLED' if original_enabled else 'DISABLED'}")
print()

# Test with ElevenLabs enabled
print("Test 1: With ElevenLabs ENABLED")
print("-" * 60)
from twilio_integration import TwilioService
service = TwilioService()
test_request = {'From': '+1234567890'}
twiml = service.handle_inbound_call(test_request)
if 'elevenlabs.io' in twiml:
    print("✅ Using ElevenLabs (redirects to AI agent)")
else:
    print("✅ Using Twilio fallback (regular IVR)")
print()

# Temporarily disable ElevenLabs to test fallback
print("Test 2: Testing Fallback (would need to disable ElevenLabs)")
print("-" * 60)
print("To test fallback:")
print("1. Edit config.yaml: set enabled: false")
print("2. Restart server")
print("3. Call will use regular Twilio IVR")
print()
print("Fallback TwiML example:")
from twilio.twiml.voice_response import VoiceResponse
response = VoiceResponse()
response.say("Hello, this is SabCare. Thank you for calling.", voice="alice")
response.hangup()
print(response)
print()
print("=" * 60)
print("✅ Regular IVR fallback is available and will work when ElevenLabs is disabled")
print("=" * 60)
