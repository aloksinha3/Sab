# Setting Up Mada for Your Friend

## Where are the Twilio Credentials?

### Current Status:
- **Your credentials are stored locally** in: `backend/config.yaml`
- **This file is NOT in the GitHub repository** (it's protected by `.gitignore`)
- **Your friend needs to create their own** `backend/config.yaml` file

## How Your Friend Can Set It Up:

### Step 1: Clone the Repository
```bash
git clone https://github.com/aloksinha3/Mada.git
cd Mada
```

### Step 2: Create Config File with Their Own Credentials

Your friend needs to:
1. Copy the example config file:
   ```bash
   cd backend
   cp config.yaml.example config.yaml
   ```

2. Edit `backend/config.yaml` with their own Twilio credentials:
   ```yaml
   twilio:
     account_sid: "THEIR_TWILIO_ACCOUNT_SID"
     auth_token: "THEIR_TWILIO_AUTH_TOKEN"
     from_number: "THEIR_TWILIO_PHONE_NUMBER"
   
   database:
     path: "patients.db"
   
   ai:
     model_name: "google/gemma-2b-it"
     use_cpu: true
     max_length: 512
   ```

### Step 3: Get Twilio Credentials

Your friend needs to:
1. Sign up for a Twilio account at https://www.twilio.com
2. Get their Account SID and Auth Token from the Twilio Console
3. Purchase a phone number (or use a trial number)
4. Add these credentials to `backend/config.yaml`

### Step 4: Install and Run

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Initialize database
python init_db.py

# Install frontend dependencies
cd ..
npm install

# Start backend (Terminal 1)
cd backend
export KMP_DUPLICATE_LIB_OK=TRUE
python -c "import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"

# Start frontend (Terminal 2)
npm run dev
```

## Important Notes:

1. **Each person needs their own Twilio account** - credentials cannot be shared
2. **The `config.yaml` file is never pushed to GitHub** - it stays local on each computer
3. **Your friend's credentials will be different** - they need their own Twilio account
4. **For local testing**, they'll need to use ngrok to expose their server to Twilio

## For Local Testing (Required for Calls):

1. Install ngrok: https://ngrok.com/
2. Start ngrok: `ngrok http 8000`
3. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
4. Set environment variable: `export SERVER_URL=https://abc123.ngrok.io`
5. Configure Twilio webhook to point to: `https://abc123.ngrok.io/twilio/voice`

## Summary:

- **Your credentials**: Stored locally in `backend/config.yaml` (not in GitHub)
- **Your friend's setup**: They create their own `config.yaml` with their own Twilio credentials
- **Security**: Credentials are never shared or pushed to GitHub
- **Requirements**: Each person needs their own Twilio account

---

**Your friend can absolutely run this on their computer!** They just need:
1. Their own Twilio account
2. To create `backend/config.yaml` with their credentials
3. To follow the setup instructions

