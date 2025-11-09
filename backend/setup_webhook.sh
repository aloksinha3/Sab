#!/bin/bash

# Webhook Setup Helper Script

echo "🔧 Twilio Webhook Setup Helper"
echo "================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo ""
    echo "Please install ngrok first:"
    echo "  brew install ngrok"
    echo "  OR download from: https://ngrok.com/download"
    echo ""
    exit 1
fi

echo "✅ ngrok is installed"
echo ""

# Check if server is running
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "⚠️  Backend server is not running on port 8000"
    echo ""
    echo "Please start the server first:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  ./start_server.sh"
    echo ""
    echo "Or in a separate terminal, run:"
    echo "  cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Press Enter to continue anyway (ngrok will start, but server needs to be running)..."
fi

echo "🚀 Starting ngrok tunnel..."
echo ""
echo "This will create a public URL that Twilio can use to send webhooks."
echo ""

# Start ngrok in the background and capture the URL
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Could not get ngrok URL. Please check ngrok is running."
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

echo "✅ ngrok tunnel created!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Your public webhook URL:"
echo "   $NGROK_URL/twilio/voice"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Go to Twilio Console: https://console.twilio.com/"
echo "2. Navigate to: Phone Numbers → Manage → Active numbers"
echo "3. Click on your number: +19199180358"
echo "4. Scroll to 'Voice & Fax' section"
echo "5. Under 'A CALL COMES IN', set:"
echo "   - Webhook: $NGROK_URL/twilio/voice"
echo "   - Method: HTTP POST"
echo "6. Click 'Save'"
echo ""
echo "🧪 To test:"
echo "   Call +19199180358 - you should be connected to the ElevenLabs agent!"
echo ""
echo "⚠️  Note: This ngrok URL will change if you restart ngrok."
echo "   For a permanent URL, use ngrok's paid plan or deploy to a server."
echo ""
echo "Press Ctrl+C to stop ngrok when done..."
echo ""

# Keep script running
wait $NGROK_PID

