import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Target, 
  BarChart3, 
  Clock, 
  CheckCircle, 
  Download,
  Eye,
  EyeOff,
  ArrowRight,
  Zap
} from 'lucide-react';
import { PipelineResult, StrategyExecutionResult, StockResult } from '@/services/api';

interface ResultsAnalysisProps {
  result: PipelineResult;
  onBack: () => void;
}

const ResultsAnalysis: React.FC<ResultsAnalysisProps> = ({ result, onBack }) => {
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null);
  const [showAllByStrategy, setShowAllByStrategy] = useState<Record<number, boolean>>({});

  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const exportResults = () => {
    const data = {
      pipeline: result,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline-results-${result.pipelineId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Pipeline Results</h2>
          <p className="text-gray-600">Analysis of your strategy pipeline execution</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={exportResults}
            className="btn-secondary flex items-center space-x-2"
          >
            <Download size={16} />
            <span>Export Results</span>
          </button>
          <button
            onClick={onBack}
            className="btn-primary"
          >
            Build New Pipeline
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Target size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Strategies</p>
              <p className="text-2xl font-bold text-gray-900">{result.strategies.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <BarChart3 size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Final Stocks</p>
              <p className="text-2xl font-bold text-gray-900">{result.finalStocks.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp size={20} className="text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Processed</p>
              <p className="text-2xl font-bold text-gray-900">{result.totalStocksProcessed}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Clock size={20} className="text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Execution Time</p>
              <p className="text-2xl font-bold text-gray-900">{formatTime(result.executionTime)}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Strategy Execution Timeline */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution Timeline</h3>
        <div className="space-y-4">
          {result.results.map((strategyResult, index) => (
            <motion.div
              key={strategyResult.strategyId}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`
                p-4 rounded-lg border-2 transition-all duration-200 cursor-pointer
                ${selectedStrategy === index 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
              onClick={(e) => {
                // Don't toggle if clicking on the show more button
                if ((e.target as HTMLElement).closest('[data-toggle-button]')) {
                  return;
                }
                setSelectedStrategy(selectedStrategy === index ? null : index);
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary-600">{index + 1}</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{strategyResult.strategyName}</h4>
                      <p className="text-sm text-gray-600">
                        {strategyResult.inputCount} → {strategyResult.outputCount} stocks
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Execution Time</p>
                    <p className="font-semibold">{formatTime(strategyResult.executionTime)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Avg Score</p>
                    <p className="font-semibold">{strategyResult.metrics.averageScore.toFixed(3)}</p>
                  </div>
                  <ArrowRight size={20} className="text-gray-400" />
                </div>
              </div>

              {/* Expanded Details */}
              {selectedStrategy === index && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-gray-200"
                >
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">Top Score</p>
                      <p className="text-lg font-semibold text-green-600">
                        {strategyResult.metrics.topScore.toFixed(3)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">Bottom Score</p>
                      <p className="text-lg font-semibold text-red-600">
                        {strategyResult.metrics.bottomScore.toFixed(3)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">Efficiency</p>
                      <p className="text-lg font-semibold text-blue-600">
                        {((strategyResult.outputCount / strategyResult.inputCount) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {/* Stock List */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h5 className="font-medium text-gray-900">Output Stocks ({strategyResult.stocks?.length || 0})</h5>
                      {(strategyResult.stocks?.length || 0) > 12 && (
                        <div 
                          className="relative z-10" 
                          data-toggle-button="true"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('Toggle button clicked for strategy', index, 'current state:', showAllByStrategy[index]);
                            setShowAllByStrategy(s => ({...s, [index]: !s[index]}));
                          }}
                        >
                          <button
                            className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg border border-blue-600 transition-colors duration-200 cursor-pointer flex items-center space-x-1 text-sm font-medium shadow-md hover:shadow-lg"
                            type="button"
                            style={{ position: 'relative', zIndex: 1000 }}
                          >
                            {showAllByStrategy[index] ? <EyeOff size={16} /> : <Eye size={16} />}
                            <span>
                              {showAllByStrategy[index]
                                ? 'Show Less'
                                : `+${Math.max(0, (strategyResult.stocks?.length || 0) - 12)} more`}
                            </span>
                          </button>
                        </div>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {(showAllByStrategy[index] 
                        ? (strategyResult.stocks || [])
                        : (strategyResult.stocks || []).slice(0, 12)
                      ).map((stock, stockIndex) => (
                        <div key={stock.stock} className="p-3 bg-white border border-gray-200 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h6 className="font-medium text-gray-900">{stock.stock}</h6>
                            <span className="text-sm font-semibold text-primary-600">
                              {stock.score.toFixed(3)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">{stock.name}</p>
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>₹{stock.currentPrice.toFixed(2)}</span>
                            <span>{formatNumber(stock.marketCap)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Final Results */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Final Stock Portfolio</h3>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <CheckCircle size={16} className="text-green-500" />
            <span>{result.finalStocks.length} stocks selected</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {result.finalStocks.map((stock, index) => (
            <motion.div
              key={stock.stock}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="p-4 bg-gradient-to-br from-primary-50 to-purple-50 border border-primary-200 rounded-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <h6 className="font-semibold text-gray-900">{stock.stock}</h6>
                <div className="flex items-center space-x-1">
                  <Zap size={14} className="text-yellow-500" />
                  <span className="text-sm font-semibold text-primary-600">
                    {stock.score.toFixed(3)}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2 line-clamp-2">{stock.name}</p>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Price:</span>
                  <span className="font-medium">₹{stock.currentPrice.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Market Cap:</span>
                  <span className="font-medium">{formatNumber(stock.marketCap)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Sector:</span>
                  <span className="font-medium">{stock.sector}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ResultsAnalysis;
