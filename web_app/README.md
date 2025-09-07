# Indian Stock Momentum Calculator - Web Application

A web-based application for analyzing momentum in Indian stocks using the "Frog in the Pan" methodology from Alpha Architect.

## Features

- 📊 **Momentum Analysis**: Calculate momentum scores using multiple timeframes
- 🔍 **Industry/Sector Filtering**: Filter stocks by industry or sector
- 📈 **Interactive Charts**: Visualize momentum data with Plotly charts
- 💾 **Smart Caching**: Efficient data caching and database storage
- 🚀 **Real-time Updates**: Automatic data refresh during analysis

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run app.py
   ```

3. **Access the App**
   Open your browser to `http://localhost:8501`

### Docker Deployment

1. **Build and Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the App**
   Open your browser to `http://localhost:8501`

### Cloud Deployment

#### Heroku
1. Create a Heroku app
2. Deploy using the Procfile
3. Set environment variables if needed

#### Other Platforms
- Use the Dockerfile for containerized deployment
- Ensure port 8501 is exposed
- Mount the `data` directory for persistent storage

## Project Structure

```
web_app/
├── app.py                 # Main Streamlit application
├── src/                   # Source code modules
│   ├── data_fetcher.py   # Data fetching and database operations
│   ├── momentum_calculator.py  # Momentum calculation logic
│   └── database.py       # Database management
├── config/               # Configuration files
│   └── config.py        # Application settings
├── data/                 # Database and data files
│   └── stock_data.db    # SQLite database
├── static/              # Static web assets
├── templates/           # HTML templates (if needed)
├── logs/               # Application logs
├── requirements.txt    # Python dependencies
├── Procfile           # Heroku deployment
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose setup
└── README.md          # This file
```

## Configuration

### Environment Variables
- `PORT`: Server port (default: 8501)
- `DATABASE_URL`: Database connection string (optional)

### Database
The application uses SQLite by default. The database file is stored in the `data/` directory.

## Usage

1. **Select Filters**: Choose industry/sector filters in the sidebar
2. **Set Parameters**: Configure number of stocks to analyze
3. **Calculate**: Click "Calculate Momentum Scores" to run analysis
4. **View Results**: Review top momentum stocks and charts

## API Endpoints

The application provides a Streamlit web interface. For API access, consider adding FastAPI endpoints.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository.
