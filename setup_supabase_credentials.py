#!/usr/bin/env python3
"""
Simple Supabase Credentials Setup
This script helps you set up your Supabase credentials quickly
"""

import os

def setup_credentials():
    """Set up Supabase credentials"""
    
    print("🚀 Supabase Credentials Setup")
    print("=" * 40)
    
    print("\n📋 Step-by-step instructions:")
    print("1. Go to https://supabase.com")
    print("2. Sign up/Login with GitHub")
    print("3. Click 'New Project'")
    print("4. Enter project name: 'momentum-calculator'")
    print("5. Choose a strong password (save it!)")
    print("6. Click 'Create new project'")
    print("7. Wait 2-3 minutes for setup to complete")
    
    print("\n🔑 Getting your credentials:")
    print("1. Go to Settings → API")
    print("2. Copy 'Project URL' (looks like: https://xxx.supabase.co)")
    print("3. Copy 'anon public' key (starts with eyJ...)")
    
    print("\n" + "="*40)
    
    # Get credentials
    supabase_url = input("\nEnter your Supabase URL: ").strip()
    if not supabase_url:
        print("❌ URL is required!")
        return False
    
    supabase_key = input("Enter your Supabase Anon Key: ").strip()
    if not supabase_key:
        print("❌ Anon Key is required!")
        return False
    
    # Create .env file
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_key}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        print("\n🚀 Now run: python complete_setup.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    setup_credentials()
