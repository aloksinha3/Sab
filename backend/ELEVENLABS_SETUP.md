# ElevenLabs Voice Agent Integration

## Overview

The Mada application now integrates with ElevenLabs Conversational AI to provide voice agent capabilities for both inbound and outbound calls.

## Configuration

All configuration is stored in `config.yaml`:

```yaml
elevenlabs:
  api_key: "sk_9df1d3ba1ec6abb3402458f7367f911c16dafb2c6b3668ed"
  key_id: "ffe9664a7288321121e2d60f708753be0ebcdc9b1b58bd9d6be1774cfe86de92"
  phone_number_id: "phnum_0801k9k4w2gye01bcy5nbmqekptc"
  agent_id: "agent_3501k9k4wv3wf2tbzswrsz93xkzn"
  enabled: true
```

## How It Works

### Inbound Calls

When someone calls your Twilio number:
1. Twilio receives the call and sends a webhook to `/twilio/voice`
2. The server checks if ElevenLabs is enabled
3. If enabled, returns TwiML that connects the call to the ElevenLabs voice agent
4. The caller is connected to the AI agent for conversation

### Outbound Calls

When the system makes outbound calls (scheduled calls, medication reminders):
1. The system checks if ElevenLabs is enabled
2. If enabled, uses ElevenLabs API to make the call with the voice agent
3. Otherwise, falls back to standard Twilio TwiML

## Setup Instructions

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure ElevenLabs**
   - Ensure `config.yaml` has the correct ElevenLabs credentials
   - Set `enabled: true` to activate ElevenLabs

3. **Configure Twilio Webhook**
   - In Twilio Console, set your phone number's Voice webhook to:
     `https://your-server.com/twilio/voice`
   - Or use ngrok for local testing:
     `ngrok http 8000`
     Then set webhook to: `https://your-ngrok-url.ngrok.io/twilio/voice`

4. **Start the Server**
   ```bash
   cd backend
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Testing

1. **Test Inbound Call**
   - Call your Twilio number
   - You should be connected to the ElevenLabs voice agent

2. **Test Outbound Call**
   - Register a patient with a phone number
   - Schedule a call
   - The call should use the ElevenLabs agent

## Troubleshooting

- **Calls not connecting to agent**: Check that `enabled: true` in config.yaml
- **API errors**: Verify your ElevenLabs API key is correct
- **Webhook issues**: Ensure your Twilio webhook URL is publicly accessible (use ngrok for local testing)

