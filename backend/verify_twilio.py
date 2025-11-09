#!/usr/bin/env python3
"""
Twilio Credentials Verification Script

This script helps diagnose Twilio authentication issues.
"""

import yaml
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def load_config():
    """Load Twilio configuration from config.yaml"""
    config_path = "config.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('twilio', {})
    return {}

def verify_twilio_credentials():
    """Verify Twilio credentials and account status"""
    print("=" * 70)
    print("Twilio Credentials Verification")
    print("=" * 70)
    print()
    
    # Load credentials
    twilio_config = load_config()
    account_sid = os.getenv("TWILIO_ACCOUNT_SID") or twilio_config.get("account_sid")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") or twilio_config.get("auth_token")
    from_number = os.getenv("TWILIO_FROM_NUMBER") or twilio_config.get("from_number")
    
    if not account_sid or not auth_token:
        print("❌ ERROR: Twilio credentials not found!")
        print()
        print("Please set one of the following:")
        print("  1. Environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER")
        print("  2. Or configure in config.yaml:")
        print("     twilio:")
        print("       account_sid: 'your_account_sid'")
        print("       auth_token: 'your_auth_token'")
        print("       from_number: '+1234567890'")
        return False
    
    print(f"✅ Credentials found:")
    print(f"   Account SID: {account_sid}")
    print(f"   Auth Token: {'*' * 10}...{auth_token[-5:]}")
    print(f"   From Number: {from_number}")
    print()
    
    # Test authentication
    print("Testing authentication...")
    try:
        client = Client(account_sid, auth_token)
        
        # Try to fetch account info
        try:
            account = client.api.accounts(account_sid).fetch()
            print(f"✅ Authentication successful!")
            print(f"   Account Name: {account.friendly_name}")
            print(f"   Account Status: {account.status}")
            print(f"   Account Type: {account.type}")
            print()
            
            # Check if account is suspended
            if account.status != "active":
                print(f"⚠️  WARNING: Account status is '{account.status}', not 'active'")
                print(f"   This may prevent calls from being made.")
                print()
            
            # Check if trial account
            if account.type == "Trial":
                print("⚠️  WARNING: This is a Trial account")
                print("   Trial accounts have restrictions:")
                print("   - Can only call verified phone numbers")
                print("   - Limited call volume")
                print("   - May have other restrictions")
                print()
                print("   To remove restrictions, upgrade your account:")
                print("   https://www.twilio.com/console/billing/upgrade")
                print()
            
        except TwilioRestException as e:
            if e.code == 20003:
                print("❌ Authentication FAILED!")
                print()
                print("Error Code: 20003 - Unable to authenticate")
                print("This usually means:")
                print("  1. Account SID is incorrect")
                print("  2. Auth Token is incorrect or expired")
                print("  3. Account has been suspended")
                print()
                print("Solutions:")
                print("  1. Log into Twilio Console: https://www.twilio.com/console")
                print("  2. Verify your Account SID and Auth Token")
                print("  3. Check if your account is active")
                print("  4. Regenerate your Auth Token if needed")
                return False
            else:
                print(f"❌ Error: {e}")
                return False
        
        # Check phone numbers
        print("Checking phone numbers...")
        try:
            incoming_phone_numbers = client.incoming_phone_numbers.list(limit=10)
            if incoming_phone_numbers:
                print(f"✅ Found {len(incoming_phone_numbers)} phone number(s):")
                for number in incoming_phone_numbers:
                    print(f"   - {number.phone_number} ({number.friendly_name})")
                print()
                
                # Check if from_number is in the list
                if from_number:
                    from_number_normalized = from_number.replace(" ", "").replace("-", "")
                    found = False
                    for number in incoming_phone_numbers:
                        if number.phone_number.replace(" ", "").replace("-", "") == from_number_normalized:
                            found = True
                            break
                    if not found:
                        print(f"⚠️  WARNING: From number '{from_number}' not found in your account")
                        print(f"   Using a number not in your account will cause calls to fail")
                        print()
            else:
                print("⚠️  No phone numbers found in your account")
                print("   You need at least one phone number to make calls")
                print()
        except TwilioRestException as e:
            print(f"⚠️  Could not list phone numbers: {e}")
            print()
        
        # Test making a call (dry run - we won't actually make it)
        print("=" * 70)
        print("Next Steps:")
        print("=" * 70)
        print()
        print("If authentication is successful but calls are still failing:")
        print("  1. Verify the 'to' phone number is in E.164 format (+1234567890)")
        print("  2. If using a Trial account, verify the 'to' number is verified")
        print("  3. Check Twilio Console logs: https://www.twilio.com/console/monitor/logs")
        print("  4. Ensure your account has sufficient balance (for paid accounts)")
        print()
        print("To test a call manually, use:")
        print("  python -c \"from twilio_integration import TwilioService; ts = TwilioService(); ts.make_call('+1234567890', 'Test message', use_twiml=True)\"")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_twilio_credentials()

