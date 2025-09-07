# Deployment Guide - Indian Stock Momentum Calculator

## 🚀 Quick Deployment Options

### 1. Local Development
```bash
cd web_app
./start.sh
```
Access at: `http://localhost:8501`

### 2. Docker Deployment
```bash
cd web_app
docker-compose up --build
```
Access at: `http://localhost:8501`

### 3. Heroku Deployment
```bash
cd web_app
heroku create your-app-name
git add .
git commit -m "Deploy momentum calculator"
git push heroku main
```

### 4. Railway Deployment
```bash
cd web_app
railway login
railway init
railway up
```

## 📋 Prerequisites

### For Local Development:
- Python 3.9+
- pip
- Virtual environment (recommended)

### For Docker:
- Docker
- Docker Compose

### For Cloud Deployment:
- Git
- Cloud platform account (Heroku, Railway, etc.)

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 8501)
- `DATABASE_URL`: Database connection string (optional)

### Database Setup
1. Copy `stock_data.db` to `web_app/data/` directory
2. Ensure database has stock metadata and price data
3. Run data import scripts if needed

## 📁 Project Structure
```
web_app/
├── app.py                 # Main Streamlit application
├── src/                   # Source code modules
├── config/               # Configuration files
├── data/                 # Database and data files
├── static/              # Static web assets
├── templates/           # HTML templates
├── logs/               # Application logs
├── requirements.txt    # Python dependencies
├── Procfile           # Heroku deployment
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose setup
└── start.sh          # Startup script
```

## 🌐 Production Considerations

### Security
- Set up proper authentication if needed
- Use environment variables for sensitive data
- Enable HTTPS in production

### Performance
- Use a production WSGI server for better performance
- Consider database optimization
- Implement proper caching strategies

### Monitoring
- Set up logging
- Monitor application health
- Track usage metrics

## 🔍 Troubleshooting

### Common Issues
1. **Database not found**: Ensure `stock_data.db` is in `data/` directory
2. **Import errors**: Check Python path and dependencies
3. **Port conflicts**: Change port in configuration
4. **Memory issues**: Optimize data loading and caching

### Logs
Check logs in the `logs/` directory for detailed error information.

## 📞 Support
For deployment issues, check the main README.md or create an issue in the repository.
