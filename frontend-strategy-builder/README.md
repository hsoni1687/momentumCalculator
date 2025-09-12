# Strategy Builder UI

A gamified drag-and-drop interface for building custom stock trading strategy pipelines. This UI runs on port 3001 and provides a mobile-friendly, engaging experience for creating and executing multi-strategy trading pipelines.

## Features

### 🎮 Gamified Interface
- Drag-and-drop strategy sequencing
- Visual pipeline builder with smooth animations
- Real-time feedback and progress indicators
- Mobile-responsive design

### 🔧 Strategy Configuration
- Market cap limit configuration for each strategy
- Output count settings (how many stocks to pass to next strategy)
- Industry and sector filtering options
- Real-time parameter validation

### 📊 Pipeline Execution
- Sequential strategy execution
- Detailed execution metrics and timing
- Stock flow visualization through pipeline
- Performance analytics for each strategy

### 📱 Mobile & Web Support
- Responsive design for all screen sizes
- Touch-friendly drag and drop
- Optimized for mobile trading workflows
- Progressive Web App capabilities

## Available Strategies

1. **Momentum Strategy** - Identifies stocks with strong price momentum using the Frog in the Pan methodology
2. **52-Week Breakout** - Finds stocks breaking out to new 52-week highs with strong volume
3. **Mean Reversion** - Identifies oversold stocks that may bounce back to their mean
4. **Low Volatility** - Finds stocks with low price volatility for stable returns

## How It Works

1. **Build Pipeline**: Drag strategies from the available list to create your custom pipeline
2. **Configure Strategies**: Set market cap limits, output counts, and filters for each strategy
3. **Execute Pipeline**: Run the pipeline to see how stocks flow through each strategy
4. **Analyze Results**: View detailed execution metrics and final stock portfolio

## Pipeline Flow

```
Market Cap Universe → Strategy 1 → Strategy 2 → Strategy 3 → Final Portfolio
     (1000 stocks)    (500 stocks)  (100 stocks)  (20 stocks)   (20 stocks)
```

Each strategy:
- Takes input stocks from the previous strategy (or market cap universe for first strategy)
- Applies its specific logic and scoring
- Outputs the top N stocks based on its criteria
- Passes results to the next strategy in the pipeline

## API Endpoints

The UI communicates with the backend through these endpoints:

- `GET /strategies` - Get available strategies
- `POST /pipeline/execute` - Execute a strategy pipeline
- `GET /pipeline/{id}` - Get pipeline execution results
- `POST /pipeline/save` - Save pipeline configuration
- `GET /pipeline/saved` - Get saved pipelines
- `GET /industries` - Get available industries
- `GET /sectors` - Get available sectors

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
cd frontend-strategy-builder
npm install
```

### Development Server
```bash
npm run dev
```
The UI will be available at http://localhost:3001

### Build for Production
```bash
npm run build
npm start
```

## Docker Deployment

The UI is containerized and runs on port 3001:

```bash
# Build and run with docker-compose
docker-compose -f docker-compose-microservices.yml up --build strategy-builder

# Or run standalone
docker build -t strategy-builder .
docker run -p 3001:3001 strategy-builder
```

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API base URL (default: http://localhost:80)

## Mobile Optimization

- Touch-friendly drag and drop with haptic feedback
- Responsive grid layouts that adapt to screen size
- Optimized animations for mobile performance
- Progressive Web App manifest for app-like experience
- Offline capability for saved pipelines

## Gamification Elements

- **Visual Feedback**: Smooth animations and transitions
- **Progress Indicators**: Real-time execution progress
- **Achievement System**: Pipeline completion rewards
- **Visual Hierarchy**: Color-coded strategies and results
- **Interactive Elements**: Hover effects and micro-interactions

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Optimized bundle size with code splitting
- Lazy loading of components
- Efficient re-rendering with React.memo
- Smooth 60fps animations
- Fast API response handling

## Security

- CORS-enabled API communication
- Input validation and sanitization
- Secure environment variable handling
- No sensitive data stored in browser

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple devices
5. Submit a pull request

## License

This project is part of the Momentum Calculator suite and follows the same licensing terms.
