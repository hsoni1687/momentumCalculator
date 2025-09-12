import React from 'react';
import { RefreshCw, Filter, TrendingUp, Database } from 'lucide-react';

interface SidebarProps {
  nStocks: number;
  setNStocks: (value: number) => void;
  industry: string;
  setIndustry: (value: string) => void;
  sector: string;
  setSector: (value: string) => void;
  topN: number;
  setTopN: (value: number) => void;
  onRefresh: () => void;
  isBackendConnected: boolean;
  isDatabaseConnected: boolean;
  industries: string[];
  sectors: string[];
  isLoading?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  nStocks,
  setNStocks,
  industry,
  setIndustry,
  sector,
  setSector,
  topN,
  setTopN,
  onRefresh,
  isBackendConnected,
  isDatabaseConnected,
  industries,
  sectors,
  isLoading = false,
}) => {
  return (
    <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-fit">
      <div className="flex items-center space-x-2 mb-6">
        <Filter className="h-5 w-5 text-primary-600" />
        <h2 className="text-lg font-semibold text-gray-900">Controls</h2>
      </div>

      {/* Number of stocks */}
      <div className="mb-6">
        <label className="label">
          Number of stocks to analyze
          {isLoading && <span className="text-xs text-blue-600 ml-2">(Loading...)</span>}
        </label>
        <input
          type="range"
          min="10"
          max="2525"
          value={nStocks}
          onChange={(e) => setNStocks(Number(e.target.value))}
          disabled={isLoading}
          className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        />
        <div className="flex justify-between text-sm text-gray-500 mt-1">
          <span>10</span>
          <span className="font-medium text-primary-600">{nStocks}</span>
          <span>2525</span>
        </div>
      </div>

      {/* Industry filter */}
      <div className="mb-6">
        <label className="label">
          Filter by Industry (optional)
        </label>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="input"
        >
          <option value="">All Industries</option>
          {industries.map((ind) => (
            <option key={ind} value={ind}>{ind}</option>
          ))}
        </select>
      </div>

      {/* Sector filter */}
      <div className="mb-6">
        <label className="label">
          Filter by Sector (optional)
        </label>
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="input"
        >
          <option value="">All Sectors</option>
          {sectors.map((sec) => (
            <option key={sec} value={sec}>{sec}</option>
          ))}
        </select>
      </div>

      {/* Top N stocks */}
      <div className="mb-6">
        <label className="label">
          Top N stocks to display
          {isLoading && <span className="text-xs text-blue-600 ml-2">(Loading...)</span>}
        </label>
        <input
          type="range"
          min="5"
          max="50"
          value={topN}
          onChange={(e) => setTopN(Number(e.target.value))}
          disabled={isLoading}
          className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        />
        <div className="flex justify-between text-sm text-gray-500 mt-1">
          <span>5</span>
          <span className="font-medium text-primary-600">{topN}</span>
          <span>50</span>
        </div>
      </div>

      {/* Refresh button */}
      <button
        onClick={onRefresh}
        className="btn btn-primary w-full flex items-center justify-center space-x-2"
      >
        <RefreshCw className="h-4 w-4" />
        <span>Refresh Data</span>
      </button>

      {/* Status indicators */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-4">System Status</h3>
        
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isBackendConnected ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-gray-600">Backend API</span>
            <span className={`text-xs px-2 py-1 rounded-full ${
              isBackendConnected ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'
            }`}>
              {isBackendConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isDatabaseConnected ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-gray-600">Database</span>
            <span className={`text-xs px-2 py-1 rounded-full ${
              isDatabaseConnected ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'
            }`}>
              {isDatabaseConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
