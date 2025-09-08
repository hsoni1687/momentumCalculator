<<<<<<< HEAD
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
=======
# Indian Stock Momentum Calculator

A comprehensive momentum calculator for Indian stocks listed on NSE and BSE, implementing the "Frog in the Pan" methodology from Alpha Architect. This production-ready application includes a SQLite database for efficient data storage and retrieval.

## 🚀 Features

### **Data Management**
- **SQLite Database**: Local storage with `tickerPrice` table for OHLC data
- **127+ Stocks**: Comprehensive coverage of NSE and BSE stocks
- **Smart Caching**: Database-first approach with API fallback
- **Automatic Updates**: Tracks data freshness and updates as needed

### **Momentum Analysis**
- **"Frog in the Pan" Methodology**: Quality momentum over raw momentum
- **Multi-factor Scoring**: Combines 6 different momentum indicators
- **Risk Adjustment**: Volatility-adjusted returns for better quality
- **Consistency Analysis**: Tracks smooth price movements

### **User Interface**
- **Interactive Web App**: Beautiful Streamlit interface
- **Real-time Charts**: Plotly visualizations and analytics
- **Database Stats**: Live monitoring of data storage
- **Configurable Settings**: Customizable analysis parameters

## 📊 Database Schema

### `tickerPrice` Table
```sql
CREATE TABLE tickerPrice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock, date)
);
```

### `stockMetadata` Table
```sql
CREATE TABLE stockMetadata (
    stock TEXT PRIMARY KEY,
    company_name TEXT,
    market_cap REAL,
    sector TEXT,
    exchange TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Conda (recommended)

### Setup
```bash
# Create conda environment
conda create -n py39 python=3.9 -y
conda activate py39

# Install dependencies
pip install -r requirements.txt

# Initialize database (optional - will auto-initialize on first run)
python init_database.py init
```

## 🎯 Usage

### Web Application
```bash
conda activate py39
streamlit run app.py
```
Access at: `http://localhost:8501`

### Command Line Tools
```bash
# Initialize database with stock data
python init_database.py init

# Update existing database
python init_database.py update

# Show database statistics
python init_database.py stats

# Run tests
python test_momentum.py
```

## 📈 Methodology

### Momentum Calculation Factors
1. **Raw Momentum (6M)**: 30% weight - Long-term price performance
2. **Raw Momentum (3M)**: 20% weight - Medium-term performance  
3. **Smooth Momentum**: 25% weight - "Frog in the Pan" consistency
4. **Volatility-Adjusted**: 15% weight - Risk-adjusted returns
5. **Consistency Score**: 5% weight - Percentage of positive days
6. **Trend Strength**: 5% weight - Moving average alignment

### "Frog in the Pan" Approach
- **Smooth Price Paths**: Prefers gradual over volatile movements
- **Consistency**: Higher percentage of positive return days
- **Quality over Quantity**: Better risk-adjusted returns
- **Trend Persistence**: Alignment with longer-term trends

## 🗄️ Database Management

### Current Stats
- **Total Records**: 12,000+ price records
- **Unique Stocks**: 50+ major stocks
- **Date Range**: 1 year of historical data
- **Database Size**: ~2.4 MB

### Data Sources
- **NSE Stocks**: 131 major companies
- **BSE Stocks**: 20 major companies
- **API**: yfinance for real-time data
- **Storage**: Local SQLite for performance

## 🔧 Configuration

### Customization Options
- **Stock Universe**: Modify `stock_lists.py` to add/remove stocks
- **Momentum Weights**: Adjust in `config.py`
- **Time Periods**: Change lookback periods in configuration
- **Database Path**: Specify custom database location

### Performance Optimization
- **Caching**: Database-first approach reduces API calls
- **Indexing**: Optimized database indexes for fast queries
- **Rate Limiting**: Built-in delays to respect API limits
- **Batch Processing**: Efficient bulk data operations

## 📊 Sample Results

Top momentum stocks typically show:
- **High Consistency**: 60%+ positive return days
- **Smooth Trends**: Gradual price appreciation
- **Low Volatility**: Risk-adjusted performance
- **Strong Fundamentals**: Large-cap, liquid stocks

## 🚨 Important Notes

### Data Limitations
- Historical data depends on yfinance availability
- Some stocks may have incomplete data
- Market cap data is estimated for demonstration

### Investment Disclaimer
This tool is for educational and research purposes only. It should not be used as the sole basis for investment decisions. Always consult with financial advisors and conduct your own research.

## 🔄 Maintenance

### Regular Updates
```bash
# Update database with fresh data
python init_database.py update

# Check database health
python init_database.py stats
```

### Database Cleanup
The system automatically manages data freshness and can clean up old records as needed.

## 📁 Project Structure
```
momentumCalc/
├── app.py                 # Streamlit web application
├── main.py               # Main application logic
├── data_fetcher.py       # Data fetching and database integration
├── momentum_calculator.py # Momentum calculation engine
├── database.py           # SQLite database management
├── stock_lists.py        # Comprehensive stock universe
├── config.py             # Configuration settings
├── init_database.py      # Database initialization script
├── test_momentum.py      # Test suite
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

>>>>>>> b4287d347bb9491e8b0d684c094c4cf22bb96779
