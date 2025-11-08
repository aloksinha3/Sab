#!/usr/bin/env python3
"""Test Twilio connection and configuration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twilio_integration import TwilioService

def test_twilio_connection():
    """Test Twilio service initialization"""
    print("🧪 Testing Twilio Connection...")
    print("-" * 50)
    
    try:
        ts = TwilioService()
        
        if ts.client:
            print("✅ Twilio client initialized successfully!")
            print(f"✅ Phone Number: {ts.from_number}")
            print("\n📋 Configuration:")
            print(f"   Account SID: {ts.config.get('twilio', {}).get('account_sid', 'Not set')[:10]}...")
            print(f"   From Number: {ts.from_number}")
            print("\n🎉 Twilio is ready to use!")
            print("\n💡 Next steps:")
            print("   1. Configure webhooks in Twilio dashboard")
            print("   2. Set up ngrok for local testing (if needed)")
            print("   3. Test making a call or sending an SMS")
            return True
        else:
            print("❌ Twilio client not initialized")
            print("   Check your config.yaml file for credentials")
            return False
    except Exception as e:
        print(f"❌ Error testing Twilio: {e}")
        return False

if __name__ == "__main__":
    success = test_twilio_connection()
    sys.exit(0 if success else 1)

