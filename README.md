# Momentum Calculator - Ultra-Optimized Microservices

A high-performance stock momentum analysis system built with microservices architecture, featuring ultra-optimized momentum calculations with intelligent caching.

## 🚀 Features

- **Ultra-Optimized Momentum Calculations**: Pre-calculated momentum scores with intelligent caching
- **Microservices Architecture**: Separate Data Service and Momentum Service
- **Real-time Data Updates**: Automated stock data polling with Yahoo Finance
- **Market Cap Prioritization**: Stocks selected by market cap (highest first)
- **Modern Frontend**: React + Next.js with Tailwind CSS
- **PostgreSQL Database**: Robust data storage with optimized indexes
- **Docker Containerization**: Full stack deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Data Service   │    │ Momentum Service│
│  (Next.js)      │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│                 │    │                 │    │                 │
│ • React UI      │    │ • Stock Data    │    │ • Momentum Calc │
│ • Tailwind CSS  │    │ • Yahoo Finance │    │ • Smart Caching │
│ • TypeScript    │    │ • Auto Updates  │    │ • Market Cap    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Database      │
                    │                 │
                    │ • Stock Metadata│
                    │ • Price Data    │
                    │ • Momentum Scores│
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd momentumCalc
   ```

2. **Start the services**
   ```bash
   docker-compose -f docker-compose-microservices.yml up --build -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Data Service: http://localhost:8001
   - Momentum Service: http://localhost:8002
   - Main API (via Nginx): http://localhost:8000

## 📊 Performance

The system features ultra-optimized momentum calculations:

- **First Request**: Calculates momentum for stocks that need it
- **Subsequent Requests**: Uses pre-calculated scores (instant response)
- **Market Cap Ordering**: Highest market cap stocks get priority
- **Smart Caching**: No redundant calculations for the same day

| Request Type | Response Time | Description |
|-------------|---------------|-------------|
| First (5 stocks) | ~0.17s | Calculates and stores momentum |
| Second (5 stocks) | ~0.17s | Uses pre-calculated scores |
| First (10 stocks) | ~0.26s | Calculates and stores momentum |
| Second (10 stocks) | ~0.17s | Uses pre-calculated scores |

## 🔧 Services

### Data Service (Port 8001)
- **Stock Data Management**: Fetches and stores stock price data
- **Yahoo Finance Integration**: Real-time data from Yahoo Finance
- **Automated Polling**: Background service for data updates
- **Momentum Calculation**: Calculates momentum after data updates

### Momentum Service (Port 8002)
- **Ultra-Optimized Calculations**: Smart momentum calculation with caching
- **Market Cap Prioritization**: Selects stocks by market cap
- **Pre-calculated Scores**: Uses stored momentum scores for instant responses
- **Configurable Weights**: Customizable momentum calculation parameters

### Frontend (Port 3000)
- **Modern UI**: React + Next.js with Tailwind CSS
- **Real-time Updates**: Live momentum scores and stock data
- **Interactive Controls**: Filter by industry, sector, and number of stocks
- **Educational Content**: Momentum analysis explanations

## 🗄️ Database Schema

### Key Tables
- **stockmetadata**: Stock information and metadata
- **tickerPrice**: Historical price data
- **momentum_scores**: Pre-calculated momentum scores (NEW)
- **stock_update_tracker**: Data update tracking

### Optimizations
- **Indexes**: Optimized queries on stock, date, and market cap
- **Pre-calculated Scores**: Momentum scores stored for instant retrieval
- **Smart Updates**: Only updates stocks that need new data

## 🛠️ Development

### Project Structure
```
momentumCalc/
├── backend/                 # Shared backend code
│   ├── models/             # Database models and business logic
│   ├── config/             # Configuration files
│   └── api/                # API definitions
├── services/               # Microservices
│   ├── data-service/       # Data management service
│   └── momentum-service/   # Momentum calculation service
├── frontend-nextjs/        # React + Next.js frontend
├── data/                   # Sample data files
└── docker-compose-microservices.yml
```

### Key Features
- **Microservices**: Independent, scalable services
- **Ultra-Optimization**: Pre-calculated momentum scores
- **Smart Caching**: No redundant calculations
- **Market Cap Priority**: Highest market cap stocks first
- **Real-time Updates**: Automated data polling

## 📈 Momentum Calculation

The system implements Alpha Architect's "Frog in the Pan" methodology:

- **12-2 Month Momentum**: Primary momentum measure
- **True Momentum**: Considers trend consistency and quality
- **Volatility Adjustment**: Risk-adjusted momentum scores
- **FIP Quality**: Momentum quality assessment
- **Configurable Weights**: Customizable calculation parameters

## 🔄 Workflow

1. **Data Service** pulls stock data from Yahoo Finance
2. **Automatic Calculation** of momentum scores after data updates
3. **Storage** of pre-calculated scores in database
4. **Momentum Service** checks for existing scores
5. **Smart Calculation** only for stocks that need it
6. **Instant Response** using pre-calculated scores

## 🚀 Deployment

The system is fully containerized and ready for production deployment:

```bash
# Start all services
docker-compose -f docker-compose-microservices.yml up -d

# View logs
docker-compose -f docker-compose-microservices.yml logs -f

# Stop services
docker-compose -f docker-compose-microservices.yml down
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
