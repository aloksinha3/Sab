# Testing Regular Twilio IVR Fallback

## ✅ Yes, Regular IVR Still Works!

The system has **automatic fallback** to regular Twilio IVR when:
1. ElevenLabs is disabled in `config.yaml` (set `enabled: false`)
2. ElevenLabs service fails to initialize
3. ElevenLabs API call fails

## How It Works

### When ElevenLabs is Enabled (Current):
- Inbound calls → Connected to ElevenLabs AI agent
- Outbound calls → Made through ElevenLabs API

### When ElevenLabs is Disabled (Fallback):
- Inbound calls → Regular Twilio TwiML response
  - Says: "Hello, this is SabCare. Thank you for calling."
  - Hangs up
- Outbound calls → Standard Twilio TwiML
  - Uses text-to-speech (Alice voice)
  - Delivers the message
  - Hangs up

## Testing the Fallback

### Option 1: Disable ElevenLabs in config.yaml

```yaml
elevenlabs:
  enabled: false  # Change this to false
```

Then restart the server and test a call.

### Option 2: Test with a Mock Request

```bash
curl -X POST http://localhost:8000/twilio/voice \
  -d "From=%2B1234567890" \
  -d "To=%2B19199180358"
```

This will show you the TwiML response.

## Current Server Status

- ✅ Server is running on http://localhost:8000
- ✅ ElevenLabs is enabled (will use AI agent)
- ✅ Fallback is ready (will use regular IVR if ElevenLabs disabled)

## Test Endpoints

- **Webhook endpoint**: `http://localhost:8000/twilio/voice`
- **API docs**: `http://localhost:8000/docs`
- **Health check**: `http://localhost:8000/docs` (FastAPI auto-generated)

## To Test Regular IVR

1. **Temporarily disable ElevenLabs:**
   ```bash
   # Edit config.yaml
   # Change: enabled: true → enabled: false
   ```

2. **Restart server:**
   ```bash
   kill $(cat server.pid)  # or kill the process
   ./start_server.sh
   ```

3. **Test call:**
   - Call +19199180358
   - You should hear the regular Twilio IVR message

4. **Re-enable ElevenLabs:**
   ```bash
   # Edit config.yaml
   # Change: enabled: false → enabled: true
   # Restart server
   ```

