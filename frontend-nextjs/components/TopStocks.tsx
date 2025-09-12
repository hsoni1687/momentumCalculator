import React from 'react';
import { TrendingUp, Building2, Factory, ChevronDown, ChevronUp } from 'lucide-react';
import { MomentumScore } from '@/services/api';

interface TopStocksProps {
  topStocks: MomentumScore[];
}

const TopStocks: React.FC<TopStocksProps> = ({ topStocks }) => {
  const [expandedStocks, setExpandedStocks] = React.useState<Set<string>>(new Set());

  const toggleExpanded = (stock: string) => {
    const newExpanded = new Set(expandedStocks);
    if (newExpanded.has(stock)) {
      newExpanded.delete(stock);
    } else {
      newExpanded.add(stock);
    }
    setExpandedStocks(newExpanded);
  };

  const formatPercentage = (value: number | undefined) => {
    if (value === undefined || value === null || (!value && value !== 0)) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  const getScoreColor = (score: number) => {
    if (!score && score !== 0) return 'text-gray-500';
    if (score >= 0.7) return 'text-success-600';
    if (score >= 0.4) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getMomentumColor = (value: number | undefined) => {
    if (value === undefined || value === null || (!value && value !== 0)) return 'text-gray-500';
    if (value > 0.1) return 'text-success-600';  // >10% positive momentum
    if (value > 0) return 'text-warning-600';    // 0-10% positive momentum
    if (value === 0) return 'text-gray-600';     // Zero momentum (neutral)
    return 'text-danger-600';                    // Negative momentum
  };

  const getScoreBadgeColor = (score: number) => {
    if (!score && score !== 0) return 'badge-secondary';
    if (score >= 0.7) return 'badge-success';
    if (score >= 0.4) return 'badge-warning';
    return 'badge-danger';
  };

  if (!topStocks || topStocks.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Top Momentum Stocks</h2>
        </div>
        <div className="text-center py-8">
          <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No momentum data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-6">
        <TrendingUp className="h-5 w-5 text-primary-600" />
        <h2 className="text-lg font-semibold text-gray-900">
          Top {topStocks.length} Momentum Stocks
        </h2>
      </div>

      <div className="space-y-3">
        {topStocks.map((stock, index) => {
          const isExpanded = expandedStocks.has(stock.stock);
          
          return (
            <div
              key={stock.stock}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-200"
            >
              <div
                className="p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors duration-200"
                onClick={() => toggleExpanded(stock.stock)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-600 rounded-full font-semibold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{stock.stock}</h3>
                      <p className="text-sm text-gray-600">{stock.name}</p>
                      {stock.calculation_date && (
                        <p className="text-xs text-gray-500">
                          📅 Calculated: {new Date(stock.calculation_date).toLocaleDateString('en-IN', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className={`badge ${getScoreBadgeColor(stock.momentum_score)}`}>
                      Score: {stock.momentum_score !== null && stock.momentum_score !== undefined ? stock.momentum_score.toFixed(2) : 'N/A'}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="p-4 bg-white border-t border-gray-200 animate-slide-up">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                        <Building2 className="h-4 w-4" />
                        <span>Company Info</span>
                      </h4>
                      <div className="space-y-2">
                        <div>
                          <span className="text-sm font-medium text-gray-500">Sector:</span>
                          <span className="ml-2 text-sm text-gray-900">{stock.sector}</span>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Industry:</span>
                          <span className="ml-2 text-sm text-gray-900">{stock.industry}</span>
                        </div>
                        {stock.last_price_date && (
                          <div>
                            <span className="text-sm font-medium text-gray-500">Last Price Pulled On:</span>
                            <span className="ml-2 text-sm text-gray-900">{stock.last_price_date}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                        <Factory className="h-4 w-4" />
                        <span>Momentum Breakdown</span>
                      </h4>
                      <div className="space-y-3">
                        <div className="space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">12-2 Month Momentum:</span>
                            <span className={`text-sm font-medium ${getMomentumColor(stock.raw_momentum_12_2)}`}>
                              {formatPercentage(stock.raw_momentum_12_2)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">FIP Quality:</span>
                            <span className="text-xs text-gray-600">
                              {stock.fip_quality ? stock.fip_quality.toFixed(3) : 'N/A'}
                            </span>
                          </div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">6 Month Momentum:</span>
                            <span className={`text-sm font-medium ${getMomentumColor(stock.true_momentum_6m)}`}>
                              {formatPercentage(stock.true_momentum_6m)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Return (ref):</span>
                            <span className="text-xs text-gray-600">
                              {formatPercentage(stock.raw_return_6m)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">3 Month Momentum:</span>
                            <span className={`text-sm font-medium ${getMomentumColor(stock.true_momentum_3m)}`}>
                              {formatPercentage(stock.true_momentum_3m)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Return (ref):</span>
                            <span className="text-xs text-gray-600">
                              {formatPercentage(stock.raw_return_3m)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">1 Month Momentum:</span>
                            <span className={`text-sm font-medium ${getMomentumColor(stock.true_momentum_1m)}`}>
                              {formatPercentage(stock.true_momentum_1m)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-500">Return (ref):</span>
                            <span className="text-xs text-gray-600">
                              {formatPercentage(stock.raw_return_1m)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TopStocks;
