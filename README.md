# 📈 Indian Stock Momentum Calculator

A professional Streamlit web application for analyzing momentum in Indian stocks using the "Frog in the Pan" methodology from Alpha Architect.

## 🚀 Features

- **2,395+ Indian Stocks** with real market data
- **Advanced Momentum Analysis** with multiple timeframes (1M, 3M, 6M)
- **Volatility-Adjusted Scoring** for better risk assessment
- **Professional UI** with interactive charts and filters
- **Real-time Data** from Supabase database
- **Industry & Sector Filtering** for targeted analysis

## 🏗️ Architecture

- **Frontend**: Streamlit (Python web framework)
- **Database**: Supabase (PostgreSQL cloud database)
- **Data**: 1.25M+ price records across 2,395 stocks
- **Deployment**: Ready for Streamlit Cloud

## 📊 Database Schema

### Tables
- **stockmetadata**: Stock information (name, sector, industry, market cap)
- **tickerprice**: Historical price data (OHLCV)
- **momentumscores**: Calculated momentum metrics

### Key Metrics
- Raw Momentum (1M, 3M, 6M)
- Volatility-Adjusted Momentum
- Relative Strength Index
- Trend Score
- Volume Score
- Total Composite Score

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Supabase account (free)

### Setup
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd momentumCalc/web_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Supabase**
   ```bash
   python setup_supabase_credentials.py
   ```

4. **Load data**
   ```bash
   python complete_setup.py
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
web_app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (Supabase credentials)
├── data/                  # CSV data files
│   ├── stock_metadata.csv
│   ├── ticker_price.csv
│   └── momentum_scores.csv
├── src/                   # Source code
│   ├── database_supabase.py
│   ├── momentum_calculator.py
│   └── data_fetcher.py
├── config/                # Configuration files
└── setup scripts/         # Database setup and data loading
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with your Supabase credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### Supabase Setup
1. Create a new project at [supabase.com](https://supabase.com)
2. Get your project URL and anon key from Settings → API
3. Run the setup scripts to create tables and load data

## 📈 Usage

1. **Select Analysis Parameters**
   - Number of stocks to analyze
   - Industry/Sector filters
   - Timeframe preferences

2. **Calculate Momentum Scores**
   - Click "Calculate Momentum Scores"
   - View results with interactive charts

3. **Analyze Results**
   - Top performers by total score
   - Sector-wise analysis
   - Historical performance trends

## 🎯 Key Features

### Momentum Calculation
- **Raw Momentum**: Simple price change over time
- **Volatility-Adjusted**: Risk-adjusted momentum scores
- **Relative Strength**: Performance vs. market
- **Trend Analysis**: Directional momentum
- **Volume Confirmation**: Volume-based validation

### Data Quality
- **2+ Years** of historical data
- **Daily OHLCV** data for all stocks
- **Real-time Updates** capability
- **Data Validation** and error handling

## 🚀 Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud
4. Deploy!

### Local Development
```bash
streamlit run app.py --server.port=8501
```

## 💰 Cost
- **Supabase**: Free tier (500MB database)
- **Streamlit Cloud**: Free hosting
- **Total**: $0/month

## 📊 Sample Data
- **2,395 stocks** from NSE/BSE
- **1.25M+ price records**
- **2+ years** of historical data
- **Multiple sectors**: IT, Banking, Pharma, Auto, etc.

## 🔍 Troubleshooting

### Common Issues
1. **Database connection failed**: Check Supabase credentials
2. **No data found**: Run `complete_setup.py` to load data
3. **Environment variables**: Ensure `.env` file is in project root

### Support
- Check the setup guides in the project
- Verify Supabase project is active
- Ensure all dependencies are installed

## 📝 License
This project is for educational and research purposes.

## 🤝 Contributing
Feel free to submit issues and enhancement requests!

---

**Built with ❤️ using Streamlit and Supabase**