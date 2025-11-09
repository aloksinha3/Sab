# Fix Twilio Authentication Error

## Problem
Calls are failing with error: `HTTP 401 error: Unable to create record: Authenticate`

**This is NOT a phone number issue** - the phone number format is correct (`+14436222793`).

The problem is that your Twilio Account SID and/or Auth Token in `config.yaml` are **invalid or expired**.

## Solution

### Step 1: Get Your Correct Twilio Credentials

1. Go to https://www.twilio.com/console
2. Log in to your Twilio account
3. On the dashboard, you'll see:
   - **Account SID**: Copy this value (starts with `AC`)
   - **Auth Token**: Click the eye icon to reveal it, then copy it

### Step 2: Update config.yaml

Open `/Users/aloksinha/SabCare/backend/config.yaml` and update the credentials:

```yaml
twilio:
  account_sid: "YOUR_ACTUAL_ACCOUNT_SID_HERE"  # Replace with your real Account SID
  auth_token: "YOUR_ACTUAL_AUTH_TOKEN_HERE"    # Replace with your real Auth Token
  from_number: "+19199180358"                   # This should be correct
```

### Step 3: Verify the Credentials

Run the verification script:
```bash
cd /Users/aloksinha/SabCare/backend
python verify_twilio.py
```

You should see:
```
✅ Authentication successful!
```

### Step 4: Restart the Backend Server

After updating the credentials, restart the backend server so it picks up the new values.

### Step 5: Test a Call

The scheduler will automatically attempt to make calls every 30 seconds. You should see:
```
✅ Call initiated: CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Common Issues

### "Account SID is correct but Auth Token is wrong"
- The Auth Token might have been regenerated
- Click the "Regenerate" button in Twilio Console to get a new one
- Update `config.yaml` with the new token

### "Account is suspended"
- Check your Twilio account status in the console
- You may need to add payment information or resolve account issues

### "Trial account restrictions"
- Trial accounts can only call verified phone numbers
- Verify the number at: https://www.twilio.com/console/phone-numbers/verified
- Or upgrade your account: https://www.twilio.com/console/billing/upgrade

## Verification

After fixing, you should see in the backend logs:
- ✅ Call scheduler started
- ✅ Call initiated: CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
- (No more 401 errors)

The phone number format is already correct - no changes needed there!

