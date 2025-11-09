# Quick Webhook Setup Guide

## ✅ Dependencies Installed

All dependencies have been installed successfully, including:
- ✅ ElevenLabs SDK
- ✅ Twilio SDK
- ✅ FastAPI and all other requirements

## 🚀 Quick Setup (2 Steps)

### Step 1: Start the Server

```bash
cd backend
source venv/bin/activate
./start_server.sh
```

Or manually:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 2: Set Up Webhook (Choose One Method)

#### Method A: Use the Setup Script (Easiest)

```bash
cd backend
./setup_webhook.sh
```

This will:
- Start ngrok automatically
- Show you the webhook URL
- Give you step-by-step instructions

#### Method B: Manual Setup

1. **Start ngrok** (in a new terminal):
   ```bash
   ngrok http 8000
   ```

2. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

3. **Configure Twilio:**
   - Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
   - Click on your number: **+19199180358**
   - Scroll to **"Voice & Fax"** section
   - Under **"A CALL COMES IN"**, set:
     - Webhook: `https://your-ngrok-url.ngrok.io/twilio/voice`
     - Method: **HTTP POST**
   - Click **"Save"**

## 🧪 Test It

1. Call your Twilio number: **+19199180358**
2. You should be connected to the ElevenLabs voice agent!
3. Check your server logs to see the webhook being received

## 📝 What Happens When Someone Calls

1. Caller dials **+19199180358**
2. Twilio receives the call
3. Twilio sends a webhook to your server: `https://your-url/twilio/voice`
4. Your server returns TwiML that connects to ElevenLabs
5. Caller is connected to your ElevenLabs AI agent
6. The agent handles the conversation

## 🔍 Troubleshooting

### Webhook not working?
- Make sure your server is running on port 8000
- Make sure ngrok is running and shows the URL
- Check that the webhook URL in Twilio matches your ngrok URL
- Check server logs for errors

### Calls not connecting to agent?
- Verify `enabled: true` in `config.yaml`
- Check that ElevenLabs credentials are correct
- Check server logs for ElevenLabs errors

### ngrok URL changes?
- If you restart ngrok, you get a new URL
- Update the webhook URL in Twilio console
- Or use ngrok paid plan for a static URL

## 📚 More Info

See `WEBHOOK_SETUP.md` for detailed instructions and troubleshooting.

