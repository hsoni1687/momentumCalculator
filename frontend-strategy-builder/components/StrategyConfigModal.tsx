import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Info } from 'lucide-react';

interface StrategyConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: StrategyConfig) => void;
  strategy: {
    id: string;
    name: string;
    description: string;
    category: string;
  } | null;
  currentConfig?: StrategyConfig;
  isFirstStrategy?: boolean;
  previousOutputCount?: number;
}

interface StrategyConfig {
  strategyId: string;
  marketCapLimit: number;
  outputCount: number;
  industry?: string;
  sector?: string;
}

const StrategyConfigModal: React.FC<StrategyConfigModalProps> = ({
  isOpen,
  onClose,
  onSave,
  strategy,
  currentConfig,
  isFirstStrategy = false,
  previousOutputCount = 0
}) => {
  const [config, setConfig] = useState<StrategyConfig>({
    strategyId: strategy?.id || '',
    marketCapLimit: 1000,
    outputCount: 20,
    industry: '',
    sector: ''
  });

  useEffect(() => {
    if (strategy && isOpen) {
      setConfig({
        strategyId: strategy.id,
        marketCapLimit: currentConfig?.marketCapLimit || (isFirstStrategy ? 1000 : previousOutputCount),
        outputCount: currentConfig?.outputCount || 20,
        industry: currentConfig?.industry || '',
        sector: currentConfig?.sector || ''
      });
    }
  }, [strategy, currentConfig, isOpen, isFirstStrategy, previousOutputCount]);

  const handleInputChange = (field: keyof StrategyConfig, value: string | number) => {
    setConfig(prev => {
      const newConfig = { ...prev, [field]: value };
      
      // Auto-adjust output count if it exceeds input
      if (field === 'marketCapLimit' && isFirstStrategy) {
        const maxOutput = Math.floor(Number(value) * 0.8);
        if (newConfig.outputCount > maxOutput) {
          newConfig.outputCount = Math.max(1, maxOutput);
        }
      }
      
      return newConfig;
    });
  };

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  const maxInputCount = isFirstStrategy ? config.marketCapLimit : previousOutputCount;
  const maxOutputCount = Math.floor(maxInputCount * 0.8) || 1;

  console.log('StrategyConfigModal render:', { isOpen, strategy: strategy?.name, currentConfig });
  
  if (!isOpen || !strategy) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black bg-opacity-50"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Configure Strategy</h2>
              <p className="text-sm text-gray-600 mt-1">{strategy.name}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Strategy Info */}
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start space-x-3">
                <Info size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Strategy Information</p>
                  <p>{strategy.description}</p>
                </div>
              </div>
            </div>

            {/* Input Stocks Count - For all strategies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Input Stocks Count
                {isFirstStrategy && (
                  <span className="text-xs text-gray-500 ml-1">(Top by Market Cap)</span>
                )}
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  min="10"
                  max="1000"
                  step="10"
                  value={config.marketCapLimit}
                  onChange={(e) => handleInputChange('marketCapLimit', parseInt(e.target.value))}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>10</span>
                  <span className="font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                    {config.marketCapLimit} stocks
                  </span>
                  <span>1000</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {isFirstStrategy 
                  ? "Number of top stocks by market cap to analyze"
                  : "Number of stocks to receive from previous strategy (can be adjusted)"
                }
              </p>
            </div>

            {/* Output Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Output Stocks
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  min="1"
                  max={maxOutputCount}
                  step="1"
                  value={Math.min(config.outputCount, maxOutputCount)}
                  onChange={(e) => handleInputChange('outputCount', parseInt(e.target.value))}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>1</span>
                  <span className="font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                    {Math.min(config.outputCount, maxOutputCount)} stocks
                  </span>
                  <span>{maxOutputCount}</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Number of top-scored stocks to output to next strategy
              </p>
              {config.outputCount > maxOutputCount && (
                <p className="text-xs text-amber-600 mt-1">
                  ⚠️ Output count adjusted to maximum allowed ({maxOutputCount})
                </p>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="btn-primary flex items-center space-x-2"
            >
              <Save size={16} />
              <span>Save Configuration</span>
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default StrategyConfigModal;