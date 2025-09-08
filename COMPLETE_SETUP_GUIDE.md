# 🚀 Complete Setup Guide - Momentum Calculator

## 🎯 What This Does
This guide will set up your complete momentum calculator app with:
- ✅ **Supabase Database** (free, with your data)
- ✅ **Vercel Hosting** (free, automatic deployments)
- ✅ **2,395 stocks** with 1.25M+ price records
- ✅ **Momentum calculations** ready to use

## 📋 Prerequisites
- Python 3.8+ installed
- GitHub account
- 30 minutes of time

## 🚀 Step-by-Step Setup

### Step 1: Set Up Supabase Database
```bash
# Run the credentials setup
python setup_supabase_credentials.py
```

**What this does:**
- Guides you through creating a Supabase project
- Helps you get your credentials
- Creates a `.env` file with your credentials

### Step 2: Load Data into Database
```bash
# Load all your data into Supabase
python complete_setup.py
```

**What this does:**
- Creates database tables
- Loads 2,395 stocks with metadata
- Loads 1.25M+ price records
- Loads momentum scores
- Tests everything

### Step 3: Test Locally
```bash
# Test your app locally
streamlit run app_supabase.py
```

**What this does:**
- Runs your app locally
- Shows you it's working
- Displays your data

### Step 4: Deploy to Vercel
```bash
# Deploy everything
python deploy_everything.py
```

**What this does:**
- Pushes code to GitHub
- Guides you through Vercel setup
- Sets up automatic deployments

## 🎉 You're Done!

Your app will be live at: `https://your-project-name.vercel.app`

## 💰 Cost: $0/month
- **Vercel**: Free hosting
- **Supabase**: Free database (500MB)
- **Total**: $0/month

## 🔧 Troubleshooting

### If Supabase setup fails:
- Check your internet connection
- Verify your credentials are correct
- Make sure your Supabase project is active

### If data loading fails:
- Check that CSV files exist in `data/` folder
- Verify your Supabase project has enough space
- Try running `complete_setup.py` again

### If deployment fails:
- Check that you have a GitHub repository
- Verify your GitHub remote is set up
- Make sure all files are committed

## 📞 Need Help?

If you get stuck at any step:
1. Check the error messages
2. Try running the script again
3. Make sure all prerequisites are met

## 🎯 What You'll Have

After setup, you'll have:
- ✅ **Live web app** with momentum calculations
- ✅ **2,395 Indian stocks** with real data
- ✅ **Professional UI** with charts and filters
- ✅ **Automatic deployments** when you update code
- ✅ **Free hosting** forever

## 🚀 Ready to Start?

Run this command to begin:
```bash
python setup_supabase_credentials.py
```
