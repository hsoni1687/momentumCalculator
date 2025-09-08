#!/usr/bin/env python3
"""
Setup environment variables for Supabase
This script helps you set up your Supabase credentials
"""

import os

def create_env_file():
    """Create .env file with Supabase credentials"""
    
    print("🚀 Supabase Environment Setup")
    print("=" * 50)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\nPlease enter your Supabase credentials:")
    print("(You can find these in your Supabase project → Settings → API)")
    print()
    
    # Get Supabase URL
    supabase_url = input("Enter your Supabase URL (e.g., https://your-project-id.supabase.co): ").strip()
    if not supabase_url:
        print("❌ Supabase URL is required!")
        return
    
    # Get Supabase Anon Key
    supabase_key = input("Enter your Supabase Anon Key (starts with eyJ...): ").strip()
    if not supabase_key:
        print("❌ Supabase Anon Key is required!")
        return
    
    # Create .env file
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_key}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        print("\nNext steps:")
        print("1. Run: python setup_supabase_tables.py")
        print("2. Run: python load_data_to_supabase.py")
        print("3. Run: streamlit run app_supabase.py")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()

