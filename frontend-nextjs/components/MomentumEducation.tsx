import React, { useState } from 'react';
import { Info, ChevronDown, ChevronUp, TrendingUp, BarChart3, Target, Zap } from 'lucide-react';

const MomentumEducation: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="card mb-6">
      <div 
        className="flex items-center justify-between cursor-pointer p-4 bg-blue-50 hover:bg-blue-100 transition-colors duration-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <Info className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-blue-900">Understanding Momentum Values</h2>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-blue-600" />
        ) : (
          <ChevronDown className="h-5 w-5 text-blue-600" />
        )}
      </div>

      {isExpanded && (
        <div className="p-6 bg-white border-t border-blue-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Momentum vs Returns */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Momentum vs Returns</span>
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-900">True Momentum</h4>
                  <p className="text-sm text-green-700 mt-1">
                    Sophisticated calculation considering trend consistency, volatility, and quality. 
                    Values range from -100% to +100%.
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">Return (Reference)</h4>
                  <p className="text-sm text-gray-700 mt-1">
                    Simple price change: (Current Price - Past Price) / Past Price. 
                    Shows raw performance for comparison.
                  </p>
                </div>
              </div>
            </div>

            {/* Momentum Interpretation */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                <span>Momentum Interpretation</span>
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-900">High Positive Momentum (50%+)</h4>
                  <p className="text-sm text-green-700 mt-1">
                    Strong, consistent upward trend with low volatility. 
                    High-quality momentum with sustained performance.
                  </p>
                </div>
                <div className="p-3 bg-yellow-50 rounded-lg">
                  <h4 className="font-medium text-yellow-900">Moderate Momentum (10-50%)</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Decent momentum with some consistency. 
                    May have moderate volatility or mixed trend patterns.
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">Low Momentum (-10% to 10%)</h4>
                  <p className="text-sm text-gray-700 mt-1">
                    Weak or neutral momentum. 
                    May indicate sideways movement or high volatility.
                  </p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg">
                  <h4 className="font-medium text-red-900">Negative Momentum (-10% or lower)</h4>
                  <p className="text-sm text-red-700 mt-1">
                    Downward trend with consistent negative performance. 
                    High volatility or declining momentum.
                  </p>
                </div>
              </div>
            </div>

            {/* Key Components */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Target className="h-5 w-5 text-purple-600" />
                <span>Momentum Components</span>
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900">Base Return (40%)</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Fundamental price change over the period.
                  </p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <h4 className="font-medium text-purple-900">Consistency Bonus (30%)</h4>
                  <p className="text-sm text-purple-700 mt-1">
                    Reward for consistent directional movement.
                  </p>
                </div>
                <div className="p-3 bg-indigo-50 rounded-lg">
                  <h4 className="font-medium text-indigo-900">Risk Adjustment (20%)</h4>
                  <p className="text-sm text-indigo-700 mt-1">
                    Volatility-adjusted return (Sharpe-like ratio).
                  </p>
                </div>
                <div className="p-3 bg-pink-50 rounded-lg">
                  <h4 className="font-medium text-pink-900">Persistence Bonus (10%)</h4>
                  <p className="text-sm text-pink-700 mt-1">
                    Reward for maintaining momentum across sub-periods.
                  </p>
                </div>
              </div>
            </div>

            {/* Special Measures */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Zap className="h-5 w-5 text-orange-600" />
                <span>Special Measures</span>
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-orange-50 rounded-lg">
                  <h4 className="font-medium text-orange-900">12-2 Month Momentum</h4>
                  <p className="text-sm text-orange-700 mt-1">
                    Alpha Architect&apos;s primary measure: 12 months excluding last 2 months. 
                    Avoids short-term noise.
                  </p>
                </div>
                <div className="p-3 bg-teal-50 rounded-lg">
                  <h4 className="font-medium text-teal-900">FIP Quality Score</h4>
                  <p className="text-sm text-teal-700 mt-1">
                    &ldquo;Frog in the Pan&rdquo; quality measure. Higher values indicate 
                    more consistent, smooth momentum patterns.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">💡 Key Insight</h4>
            <p className="text-sm text-blue-700">
              True momentum identifies stocks with <strong>sustainable, high-quality momentum</strong> 
              rather than just high returns. A stock with 20% return and 60% momentum is better 
              than a stock with 30% return and 40% momentum because it has more consistent, 
              lower-volatility performance.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MomentumEducation;
