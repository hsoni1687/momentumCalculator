import React, { useState, useEffect, useCallback, useRef } from 'react';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';
import StrategyTabs from '@/components/StrategyTabs';
import { apiClient, MomentumScore, HealthResponse } from '@/services/api';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const Home: React.FC = () => {
  // State management
  const [nStocks, setNStocks] = useState(50);
  const [industry, setIndustry] = useState('');
  const [sector, setSector] = useState('');
  const [topN, setTopN] = useState(10);
  
  const [marketStatus, setMarketStatus] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [isDatabaseConnected, setIsDatabaseConnected] = useState(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  
  const [industries, setIndustries] = useState<string[]>([]);
  const [sectors, setSectors] = useState<string[]>([]);

  // Check backend health on component mount
  useEffect(() => {
    // Load industries and sectors
    loadIndustries();
    loadSectors();
    
    // Check backend health
    checkBackendHealth();
  }, []);


  const checkBackendHealth = async () => {
    try {
      const health = await apiClient.healthCheck();
      setHealthData(health);
      setIsBackendConnected(health.status === 'healthy');
      setIsDatabaseConnected(health.database === 'connected');
      setError(null);
    } catch (err) {
      console.error('Health check failed:', err);
      setIsBackendConnected(false);
      setIsDatabaseConnected(false);
      setError('Cannot connect to backend API. Please ensure the backend is running.');
    }
  };


  const loadIndustries = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/industries`);
      const data = await response.json();
      setIndustries(data.industries || []);
    } catch (err) {
      console.error('Error loading industries:', err);
    }
  };

  const loadSectors = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/sectors`);
      const data = await response.json();
      setSectors(data.sectors || []);
    } catch (err) {
      console.error('Error loading sectors:', err);
    }
  };

  const handleRefresh = () => {
    checkBackendHealth();
  };

  return (
    <Layout title="Momentum Calculator - Indian Stock Analysis">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gradient mb-4">
            📈 Indian Stock Strategy Analyzer
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Advanced trading strategy analysis for Indian stocks. Analyze multiple strategies including
            momentum, breakout patterns, moving averages, volatility, and mean reversion with our
            modular microservices architecture.
          </p>
        </div>


        {/* Backend Status */}
        {!isBackendConnected && (
          <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-warning-600" />
              <span className="text-warning-800 font-medium">Backend Disconnected</span>
            </div>
            <p className="text-warning-700 mt-1">
              Please ensure the backend API is running at {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}
            </p>
          </div>
        )}

        {/* Main Content */}
        {isBackendConnected ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <Sidebar
                nStocks={nStocks}
                setNStocks={setNStocks}
                industry={industry}
                setIndustry={setIndustry}
                sector={sector}
                setSector={setSector}
                topN={topN}
                setTopN={setTopN}
                onRefresh={handleRefresh}
                isBackendConnected={isBackendConnected}
                isDatabaseConnected={isDatabaseConnected}
                industries={industries}
                sectors={sectors}
                isLoading={false}
              />
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
              <StrategyTabs
                nStocks={nStocks}
                industry={industry}
                sector={sector}
                topN={topN}
                isBackendConnected={isBackendConnected}
              />
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Backend Not Available</h2>
            <p className="text-gray-600 mb-4">
              Please start the backend API to use the strategy analyzer.
            </p>
            <button
              onClick={handleRefresh}
              className="btn btn-primary"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Health Info */}
        {healthData && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-success-600" />
                  <span className="text-sm text-gray-600">Backend v{healthData.version}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-success-600" />
                  <span className="text-sm text-gray-600">Status: {healthData.status}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-success-600" />
                  <span className="text-sm text-gray-600">Database: {healthData.database}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Home;
