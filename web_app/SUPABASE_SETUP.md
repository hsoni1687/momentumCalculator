# 🚀 Supabase Setup Guide

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up/Login with your GitHub account
3. Click "New Project"
4. Choose your organization
5. Enter project details:
   - **Name**: `momentum-calculator`
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you
6. Click "Create new project"

## Step 2: Get Your Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **anon public** key (starts with `eyJ...`)

## Step 3: Set Environment Variables

Create a `.env` file in your project root:

```bash
# Create .env file
touch .env
```

Add your credentials to `.env`:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Step 4: Install Dependencies

```bash
pip install supabase
```

## Step 5: Setup Database Tables

Run the table creation script:

```bash
python setup_supabase_tables.py
```

## Step 6: Load Data

Run the data loading script:

```bash
python load_data_to_supabase.py
```

## Step 7: Test Your Setup

Run the Supabase app:

```bash
streamlit run app_supabase.py
```

## Troubleshooting

### If you get "Table not found" errors:
- Make sure you ran `setup_supabase_tables.py` first
- Check that your credentials are correct

### If you get "Permission denied" errors:
- Make sure you're using the `anon` key, not the `service_role` key
- Check that Row Level Security (RLS) is disabled for your tables

### If data loading fails:
- Check your internet connection
- Verify your Supabase project is active
- Make sure the CSV files exist in the `data/` directory

## Next Steps

Once everything is working:
1. Deploy to Streamlit Cloud
2. Set the same environment variables in Streamlit Cloud
3. Your app will be live! 🎉

