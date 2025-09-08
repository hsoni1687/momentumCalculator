# 🚀 Streamlit Cloud Deployment Guide

## 📋 **Step-by-Step Deployment**

### **Step 1: Push to GitHub**
```bash
# Add your GitHub remote (if not already added)
git remote add origin https://github.com/yourusername/your-repo.git

# Push to GitHub
git push -u origin main
```

### **Step 2: Deploy to Streamlit Cloud**

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Sign in with GitHub**
3. **Click "New app"**
4. **Select your repository**
5. **Set the main file path**: `web_app/app.py`
6. **Click "Deploy"**

### **Step 3: Configure Environment Variables**

In your Streamlit Cloud app dashboard:

1. **Go to Settings → Secrets**
2. **Add the following secrets**:

```toml
[supabase]
url = "https://krlwufpvrdbehqwcngxi.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtybHd1ZnB2cmRiZWhxd2NuZ3hpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyODM0MTYsImV4cCI6MjA3Mjg1OTQxNn0.UQay88oKFRjwe3HjaCyW1CnyVOWwY2i7RU3Lx5uKx6o"
```

### **Step 4: Redeploy**

After adding secrets:
1. **Click "Redeploy"** in your app dashboard
2. **Wait for deployment** to complete
3. **Test your app**

## 🔧 **Troubleshooting**

### **If you get "Database connection failed":**

1. **Check secrets are set correctly**
2. **Verify Supabase project is active**
3. **Check the app logs** in Streamlit Cloud dashboard

### **If you get "No data found":**

1. **Verify your Supabase database has data**
2. **Check table names are correct** (lowercase)
3. **Run the setup scripts locally** to ensure data is loaded

### **If deployment fails:**

1. **Check requirements.txt** has all dependencies
2. **Verify app.py is in the correct path**
3. **Check GitHub repository** is public

## 📊 **Expected Result**

After successful deployment, you should see:
- ✅ **"Database connected successfully"** message
- ✅ **Database stats** showing 2,395 stocks
- ✅ **Interactive momentum calculator** interface
- ✅ **Charts and filters** working properly

## 🎯 **Your App URL**

Once deployed, your app will be available at:
`https://your-app-name.streamlit.app`

## 💰 **Cost: FREE**

- **Streamlit Cloud**: Free hosting
- **Supabase**: Free database (500MB)
- **Total**: $0/month

## 🚀 **Ready to Deploy?**

1. Push your code to GitHub
2. Deploy to Streamlit Cloud
3. Add the secrets
4. Enjoy your live app!

---

**Need help? Check the app logs in Streamlit Cloud dashboard for detailed error messages.**
