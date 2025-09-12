import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Loader2, AlertCircle, TrendingUp, BarChart3, Shield, RotateCcw } from 'lucide-react';

interface StrategyScore {
  stock: string;
  name: string;
  sector: string;
  industry: string;
  score: number;
  insufficient_data: boolean;
  // Strategy-specific fields
  current_price?: number;
  week52_high?: number;
  week52_low?: number;
  breakout_ratio?: number;
  ma_50?: number;
  ma_200?: number;
  crossover_ratio?: number;
  daily_volatility?: number;
  annual_volatility?: number;
  z_score?: number;
  price_deviation_pct?: number;
}

interface Strategy {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  color: string;
}

interface StrategyTabsProps {
  nStocks: number;
  industry: string;
  sector: string;
  topN: number;
  isBackendConnected: boolean;
}

const StrategyTabs: React.FC<StrategyTabsProps> = ({
  nStocks,
  industry,
  sector,
  topN,
  isBackendConnected
}) => {
  const [activeTab, setActiveTab] = useState('momentum');
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [strategyScores, setStrategyScores] = useState<StrategyScore[]>([]);
  const [topStocks, setTopStocks] = useState<StrategyScore[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Debouncing and request management
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentRequestRef = useRef<AbortController | null>(null);

  // Load available strategies on mount
  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/strategies`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Loaded strategies:', data);
      setStrategies(data.strategies || []);
    } catch (err) {
      console.error('Error loading strategies:', err);
      setStrategies([]);
    }
  };

  const loadStrategyData = useCallback(async (strategyName: string, immediate = false) => {
    if (!isBackendConnected) return;

    // Cancel any existing request
    if (currentRequestRef.current) {
      currentRequestRef.current.abort();
    }

    // Clear any existing debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    const executeRequest = async () => {
      if (!isBackendConnected) return;
      
      setIsLoading(true);
      setError(null);

      const abortController = new AbortController();
      currentRequestRef.current = abortController;

      try {
        console.log(`Loading ${strategyName} data...`);
        
        let url = '';
        if (strategyName === 'momentum') {
          url = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/momentum?limit=${nStocks}&top_n=${topN}`;
          if (industry) url += `&industry=${encodeURIComponent(industry)}`;
          if (sector) url += `&sector=${encodeURIComponent(sector)}`;
        } else {
          // Use v2 endpoint to avoid interfering with legacy behavior and guard against undefined keys
          const safeKey = strategyName && strategyName !== 'undefined' ? strategyName : 'momentum';
          url = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/strategy/v2/${safeKey}?limit=${nStocks}&top_n=${topN}`;
          if (industry) url += `&industry=${encodeURIComponent(industry)}`;
          if (sector) url += `&sector=${encodeURIComponent(sector)}`;
        }

        const response = await fetch(url, {
          signal: abortController.signal
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (abortController.signal.aborted) {
          console.log('Request was cancelled');
          return;
        }

        console.log(`${strategyName} data loaded:`, data);
        
        if (strategyName === 'momentum') {
          // Map momentum_score to score for consistency with other strategies
          const mappedMomentumScores = (data.momentum_scores || []).map((stock: any) => ({
            ...stock,
            score: stock.momentum_score
          }));
          const mappedTopStocks = (data.top_stocks || []).map((stock: any) => ({
            ...stock,
            score: stock.momentum_score
          }));
          setStrategyScores(mappedMomentumScores);
          setTopStocks(mappedTopStocks);
        } else {
          setStrategyScores(data.strategy_scores || []);
          setTopStocks(data.top_stocks || []);
        }
      } catch (err: any) {
        if (err.name === 'AbortError' || abortController.signal.aborted) {
          console.log('Request was cancelled');
          return;
        }
        
        console.error(`Error loading ${strategyName} data:`, err);
        setError(err.message || `Failed to load ${strategyName} data`);
        setStrategyScores([]);
        setTopStocks([]);
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
        currentRequestRef.current = null;
      }
    };

    if (immediate) {
      await executeRequest();
    } else {
      debounceTimeoutRef.current = setTimeout(executeRequest, 1000);
    }
  }, [isBackendConnected, nStocks, industry, sector, topN]);

  // Load data when filters change or tab changes
  useEffect(() => {
    if (!isBackendConnected) return;
    
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    
    debounceTimeoutRef.current = setTimeout(() => {
      loadStrategyData(activeTab, true);
      debounceTimeoutRef.current = null;
    }, 1500);
    
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
    };
  }, [nStocks, industry, sector, topN, isBackendConnected, activeTab, loadStrategyData]);

  // Cleanup function
  useEffect(() => {
    return () => {
      if (currentRequestRef.current) {
        currentRequestRef.current.abort();
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  const getTabIcon = (strategyKey: string) => {
    switch (strategyKey) {
      case 'momentum':
        return <TrendingUp className="h-4 w-4" />;
      case 'week52_breakout':
        return <BarChart3 className="h-4 w-4" />;
      case 'ma_crossover':
        return <TrendingUp className="h-4 w-4" />;
      case 'low_volatility':
        return <Shield className="h-4 w-4" />;
      case 'mean_reversion':
        return <RotateCcw className="h-4 w-4" />;
      default:
        return <BarChart3 className="h-4 w-4" />;
    }
  };

  const formatScore = (score: number, strategyKey: string) => {
    if (!score && score !== 0) return 'N/A';
    
    if (strategyKey === 'low_volatility') {
      return `${(score * 100).toFixed(2)}%`;
    } else if (strategyKey === 'ma_crossover') {
      return `${(score * 100).toFixed(2)}%`;
    } else if (strategyKey === 'mean_reversion') {
      return score.toFixed(3);
    } else {
      return score.toFixed(3);
    }
  };

  const getScoreLabel = (strategyKey: string) => {
    switch (strategyKey) {
      case 'momentum':
        return 'Momentum Score';
      case 'week52_breakout':
        return 'Breakout Ratio';
      case 'ma_crossover':
        return 'Crossover Ratio';
      case 'low_volatility':
        return 'Volatility';
      case 'mean_reversion':
        return 'Z-Score';
      default:
        return 'Score';
    }
  };

  return (
    <div className="space-y-6">
      {/* Strategy Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-6">
          {/* All Strategy Tabs from backend */}
          {strategies.map((strategy) => (
            <button
              key={strategy.id}
              onClick={() => setActiveTab(strategy.id)}
              className={`py-2 px-1 font-medium text-sm inline-flex items-center space-x-2 shrink-0 ${
                activeTab === strategy.id
                  ? 'border-b-2 border-primary-500 text-primary-600'
                  : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {getTabIcon(strategy.id)}
              <span>{strategy.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Strategy Description */}
      {strategies
        .filter(s => s.id === activeTab)
        .map(strategy => (
          <div key={strategy.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-blue-900 mb-2 flex items-center gap-2">
              {getTabIcon(strategy.id)} <span>{strategy.name}</span>
            </h3>
            <p className="text-blue-800 mb-2">{strategy.description}</p>
          </div>
        ))
      }

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="card text-center py-12">
          <Loader2 className="h-8 w-8 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Calculating {activeTab} scores...</p>
        </div>
      )}

      {/* Results */}
      {!isLoading && !error && (
        <div className="space-y-6">
          {/* Top Stocks */}
          {topStocks.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">🏆 Top {topN} Stocks - {strategies.find(s => s.id === activeTab)?.name}</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{getScoreLabel(activeTab)}</th>
                      {activeTab === 'week52_breakout' && (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">52W High</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">52W Low</th>
                        </>
                      )}
                      {activeTab === 'ma_crossover' && (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">50-day MA</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">200-day MA</th>
                        </>
                      )}
                      {activeTab === 'low_volatility' && (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Daily Volatility</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Annual Volatility</th>
                        </>
                      )}
                      {activeTab === 'mean_reversion' && (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">200-day MA</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deviation %</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {topStocks.map((stock, index) => (
                      <tr key={stock.stock} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {stock.stock}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {stock.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {stock.sector}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {stock.insufficient_data ? (
                            <span className="text-red-600">Insufficient Data</span>
                          ) : (
                            formatScore(stock.score, activeTab)
                          )}
                        </td>
                        {activeTab === 'week52_breakout' && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.current_price ? `₹${Number(stock.current_price).toFixed(2)}` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.week52_high ? `₹${Number(stock.week52_high).toFixed(2)}` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.week52_low ? `₹${Number(stock.week52_low).toFixed(2)}` : '-'}
                            </td>
                          </>
                        )}
                        {activeTab === 'ma_crossover' && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.ma_50 ? `₹${Number(stock.ma_50).toFixed(2)}` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.ma_200 ? `₹${Number(stock.ma_200).toFixed(2)}` : '-'}
                            </td>
                          </>
                        )}
                        {activeTab === 'low_volatility' && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.daily_volatility ? `${(Number(stock.daily_volatility) * 100).toFixed(2)}%` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.annual_volatility ? `${(Number(stock.annual_volatility) * 100).toFixed(2)}%` : '-'}
                            </td>
                          </>
                        )}
                        {activeTab === 'mean_reversion' && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.current_price ? `₹${Number(stock.current_price).toFixed(2)}` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.ma_200 ? `₹${Number(stock.ma_200).toFixed(2)}` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {stock.price_deviation_pct ? `${Number(stock.price_deviation_pct).toFixed(2)}%` : '-'}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Summary Stats */}
          {strategyScores.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card text-center">
                <div className="text-2xl font-bold text-primary-600">{strategyScores.length}</div>
                <div className="text-sm text-gray-600">Total Stocks Analyzed</div>
              </div>
              <div className="card text-center">
                <div className="text-2xl font-bold text-green-600">
                  {strategyScores.filter(s => !s.insufficient_data).length}
                </div>
                <div className="text-sm text-gray-600">Stocks with Sufficient Data</div>
              </div>
              <div className="card text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {strategyScores.filter(s => s.insufficient_data).length}
                </div>
                <div className="text-sm text-gray-600">Insufficient Data</div>
              </div>
            </div>
          )}

          {/* No Data Message */}
          {strategyScores.length === 0 && !isLoading && (
            <div className="card text-center py-12">
              <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No Data Available</h2>
              <p className="text-gray-600">
                No stocks found matching the current filters for {activeTab} strategy.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StrategyTabs;
