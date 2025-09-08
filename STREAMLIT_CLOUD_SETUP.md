# Streamlit Cloud Deployment Setup

## 🚀 Quick Setup Guide

### 1. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set the app path to: `web_app/app.py`
4. Click "Deploy"

### 2. Configure Supabase Secrets
After deployment, you need to add your Supabase credentials:

1. **Go to your Streamlit Cloud dashboard**
2. **Click on your deployed app**
3. **Go to "Settings" > "Secrets"**
4. **Add these secrets:**

```toml
[supabase]
url = "https://krlwufpvrdbehqwcngxi.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtybHd1ZnB2cmRiZWhxd2NuZ3hpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyODM0MTYsImV4cCI6MjA3Mjg1OTQxNn0.UQay88oKFRjwe3HjaCyW1CnyVOWwY2i7RU3Lx5uKx6o"
```

### 3. Redeploy
After adding the secrets:
1. **Click "Redeploy"** in your Streamlit Cloud dashboard
2. **Wait for deployment** (2-3 minutes)
3. **Test your app** - it should now connect to Supabase

## 🔧 Local Development Setup

If you want to run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Setup secrets (optional - will use .env file if available)
python setup_secrets.py

# Run the app
streamlit run app.py
```

## 📊 Expected Results

After successful deployment, you should see:
- ✅ **"Database connected successfully"**
- ✅ **Database stats showing 2,395 stocks**
- ✅ **Momentum calculation working**
- ✅ **No error messages**

## 🆘 Troubleshooting

### "Missing Supabase credentials" Error
- Make sure you added the secrets in Streamlit Cloud
- Check that the secrets are in the correct format
- Redeploy after adding secrets

### "ModuleNotFoundError" Error
- Make sure all dependencies are in requirements.txt
- Redeploy to install missing packages

### "Database connection failed" Error
- Check your Supabase credentials
- Verify your Supabase project is active
- Check that data is loaded in your Supabase database

## 📞 Support

If you're still having issues:
1. Check the Streamlit Cloud logs
2. Verify your GitHub repository has the latest code
3. Make sure the app path is set to `web_app/app.py`
