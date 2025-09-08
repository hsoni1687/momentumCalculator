#!/usr/bin/env python3
"""
Quick Deployment Helper for Streamlit Cloud + Supabase
This script helps you deploy your app quickly and easily
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_git_status():
    """Check if we're in a git repository and if there are uncommitted changes"""
    try:
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️  You have uncommitted changes:")
            print(result.stdout)
            response = input("Do you want to commit these changes? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                commit_message = input("Enter commit message: ").strip()
                if not commit_message:
                    commit_message = "Update for deployment"
                
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                print("✅ Changes committed")
            else:
                print("❌ Please commit your changes before deploying")
                return False
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository. Please initialize git first:")
        print("   git init")
        print("   git add .")
        print("   git commit -m 'Initial commit'")
        return False
    except FileNotFoundError:
        print("❌ Git not found. Please install git first.")
        return False

def check_streamlit_cloud_requirements():
    """Check if the app is ready for Streamlit Cloud deployment"""
    print("🔍 Checking Streamlit Cloud requirements...")
    
    # Check if app.py exists
    if not Path("app.py").exists():
        print("❌ app.py not found")
        return False
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    # Check if config system is in place
    if not Path("config").exists():
        print("❌ config directory not found")
        return False
    
    print("✅ All requirements met")
    return True

def show_deployment_instructions():
    """Show step-by-step deployment instructions"""
    print("\n🚀 Streamlit Cloud Deployment Instructions")
    print("=" * 50)
    
    print("\n1. 📝 Set up Supabase (if not done already):")
    print("   • Go to https://supabase.com")
    print("   • Create a new project")
    print("   • Copy your project URL and anon key")
    
    print("\n2. 🌐 Deploy to Streamlit Cloud:")
    print("   • Go to https://share.streamlit.io")
    print("   • Sign in with GitHub")
    print("   • Click 'New app'")
    print("   • Select your repository")
    print("   • Set main file path to: web_app/app.py")
    
    print("\n3. 🔐 Set up secrets:")
    print("   • In Streamlit Cloud, go to your app settings")
    print("   • Add these secrets:")
    print("     - SUPABASE_URL: your_supabase_url")
    print("     - SUPABASE_ANON_KEY: your_supabase_anon_key")
    
    print("\n4. 🗄️ Set up database:")
    print("   • Run the SQL from init.sql in your Supabase SQL editor")
    print("   • Upload your CSV files to Supabase")
    
    print("\n5. 🎉 Deploy!")
    print("   • Click 'Deploy' in Streamlit Cloud")
    print("   • Your app will be live in minutes!")

def show_current_config():
    """Show current configuration"""
    print("\n🔧 Current Configuration:")
    print("=" * 30)
    
    try:
        sys.path.append('config')
        from config.loader import get_config
        config_manager = get_config()
        summary = config_manager.get_config_summary()
        
        for key, value in summary.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"   ⚠️  Could not load configuration: {e}")

def main():
    """Main deployment helper function"""
    print("🚀 Momentum Calculator - Quick Deploy Helper")
    print("=" * 50)
    
    # Check git status
    if not check_git_status():
        return
    
    # Check requirements
    if not check_streamlit_cloud_requirements():
        return
    
    # Show current config
    show_current_config()
    
    # Show deployment instructions
    show_deployment_instructions()
    
    print("\n💡 Pro Tips:")
    print("   • Your app will automatically detect cloud environment")
    print("   • Configuration system handles everything automatically")
    print("   • No need to modify code for deployment")
    print("   • Database connection is handled by the smart adapter")
    
    print("\n🎯 Why This Setup is Better Than Railway:")
    print("   • FREE (Railway costs $5-20/month)")
    print("   • Purpose-built for Streamlit")
    print("   • Managed database (no maintenance)")
    print("   • Auto-scaling")
    print("   • Zero server management")

if __name__ == "__main__":
    main()
