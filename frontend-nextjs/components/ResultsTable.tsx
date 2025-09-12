import React, { useState } from 'react';
import { Download, Table, Search, ArrowUpDown } from 'lucide-react';
import { MomentumScore } from '@/services/api';

interface ResultsTableProps {
  momentumScores: MomentumScore[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ momentumScores }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof MomentumScore>('momentum_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

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

  const handleSort = (field: keyof MomentumScore) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSortedData = React.useMemo(() => {
    let filtered = momentumScores.filter(stock =>
      stock.stock.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.sector.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.industry.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();
      
      if (sortDirection === 'asc') {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });
  }, [momentumScores, searchTerm, sortField, sortDirection]);

  const downloadCSV = () => {
    const headers = ['Stock', 'Name', 'Sector', 'Industry', 'Momentum Score', '12-2 Month', '6 Month', '3 Month', '1 Month'];
    const csvContent = [
      headers.join(','),
      ...filteredAndSortedData.map(stock => [
        stock.stock,
        `"${stock.name}"`,
        `"${stock.sector}"`,
        `"${stock.industry}"`,
        stock.momentum_score !== null && stock.momentum_score !== undefined ? stock.momentum_score.toFixed(4) : 'N/A',
        stock.raw_momentum_12_2 ? stock.raw_momentum_12_2.toFixed(4) : 'N/A',
        stock.raw_momentum_6m ? stock.raw_momentum_6m.toFixed(4) : 'N/A',
        stock.raw_momentum_3m ? stock.raw_momentum_3m.toFixed(4) : 'N/A',
        stock.raw_momentum_1m ? stock.raw_momentum_1m.toFixed(4) : 'N/A'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `momentum_scores_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  if (!momentumScores || momentumScores.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Table className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">All Results</h2>
        </div>
        <div className="text-center py-8">
          <Table className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No results to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Table className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">All Results</h2>
          <span className="badge badge-primary">{filteredAndSortedData.length} stocks</span>
        </div>
        
        <button
          onClick={downloadCSV}
          className="btn btn-secondary flex items-center space-x-2"
        >
          <Download className="h-4 w-4" />
          <span>Download CSV</span>
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search stocks, sectors, or industries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-900">
                <button
                  onClick={() => handleSort('stock')}
                  className="flex items-center space-x-1 hover:text-primary-600"
                >
                  <span>Stock</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center space-x-1 hover:text-primary-600"
                >
                  <span>Name</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">
                <button
                  onClick={() => handleSort('sector')}
                  className="flex items-center space-x-1 hover:text-primary-600"
                >
                  <span>Sector</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">
                <button
                  onClick={() => handleSort('momentum_score')}
                  className="flex items-center space-x-1 hover:text-primary-600"
                >
                  <span>Momentum Score</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">12-2 Month</th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">6 Month</th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">3 Month</th>
              <th className="text-left py-3 px-4 font-medium text-gray-900">1 Month</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedData.map((stock, index) => (
              <tr key={stock.stock} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                <td className="py-3 px-4 font-medium text-gray-900">
                  <div>
                    <div>{stock.stock}</div>
                    {stock.calculation_date && (
                      <div className="text-xs text-gray-500 mt-1">
                        📅 {new Date(stock.calculation_date).toLocaleDateString('en-IN', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </div>
                    )}
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-600">{stock.name}</td>
                <td className="py-3 px-4 text-gray-600">{stock.sector}</td>
                <td className="py-3 px-4">
                  <span className={`font-medium ${getScoreColor(stock.momentum_score)}`}>
                    {stock.momentum_score !== null && stock.momentum_score !== undefined ? stock.momentum_score.toFixed(4) : 'N/A'}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-600">{formatPercentage(stock.raw_momentum_12_2)}</td>
                <td className="py-3 px-4 text-gray-600">{formatPercentage(stock.raw_momentum_6m)}</td>
                <td className="py-3 px-4 text-gray-600">{formatPercentage(stock.raw_momentum_3m)}</td>
                <td className="py-3 px-4 text-gray-600">{formatPercentage(stock.raw_momentum_1m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredAndSortedData.length === 0 && searchTerm && (
        <div className="text-center py-8">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No stocks found matching &quot;{searchTerm}&quot;</p>
        </div>
      )}
    </div>
  );
};

export default ResultsTable;
