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

