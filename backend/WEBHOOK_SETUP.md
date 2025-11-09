# Twilio Webhook Setup Guide

## Step 1: Make Your Server Publicly Accessible

For local development, you need to expose your local server to the internet so Twilio can send webhooks to it.

### Option A: Using ngrok (Recommended for Testing)

1. **Install ngrok:**
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start your backend server:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **In a new terminal, start ngrok:**
   ```bash
   ngrok http 8000
   ```

4. **Copy the HTTPS URL** (looks like `https://abc123.ngrok.io`)

### Option B: Deploy to a Server

If you have a server with a public IP, deploy the application there and use that URL.

## Step 2: Configure Twilio Webhook

1. **Go to Twilio Console:**
   - Visit: https://console.twilio.com/
   - Log in with your Twilio account

2. **Navigate to Phone Numbers:**
   - Click on "Phone Numbers" in the left sidebar
   - Click on "Manage" → "Active numbers"
   - Click on your phone number: `+19199180358`

3. **Set the Voice Webhook:**
   - Scroll down to "Voice & Fax" section
   - Under "A CALL COMES IN", select "Webhook"
   - Enter your webhook URL:
     ```
     https://your-ngrok-url.ngrok.io/twilio/voice
     ```
     (Replace `your-ngrok-url` with your actual ngrok URL)
   - Select "HTTP POST" as the method
   - Click "Save"

4. **Optional - Configure Status Callback:**
   - Under "STATUS CALLBACK URL", enter:
     ```
     https://your-ngrok-url.ngrok.io/twilio/status
     ```
   - Select "HTTP POST" as the method

## Step 3: Test the Webhook

1. **Call your Twilio number:** `+19199180358`
2. **You should be connected to the ElevenLabs voice agent**
3. **Check your server logs** to see the webhook being received

## Troubleshooting

### Webhook not receiving calls:
- Make sure ngrok is running and the URL is correct
- Check that your backend server is running on port 8000
- Verify the webhook URL in Twilio console matches your ngrok URL
- Check Twilio logs in the console for any errors

### Calls not connecting to ElevenLabs:
- Verify `enabled: true` in `config.yaml`
- Check that your ElevenLabs API key is correct
- Check server logs for any errors

### ngrok URL changes:
- If you restart ngrok, you'll get a new URL
- Update the webhook URL in Twilio console with the new ngrok URL
- Or use ngrok's paid plan for a static URL

## Quick Test Command

```bash
# Start server
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL and update Twilio webhook
```

## Production Setup

For production, you should:
1. Deploy your application to a server (AWS, Heroku, DigitalOcean, etc.)
2. Use that server's public URL for the webhook
3. Set up SSL/TLS (HTTPS) - required by Twilio
4. Use environment variables for sensitive credentials

