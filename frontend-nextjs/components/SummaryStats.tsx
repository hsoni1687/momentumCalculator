import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Building2, Target, Award } from 'lucide-react';
import { MomentumScore } from '@/services/api';

interface SummaryStatsProps {
  momentumScores: MomentumScore[];
}

const SummaryStats: React.FC<SummaryStatsProps> = ({ momentumScores }) => {
  const stats = React.useMemo(() => {
    if (!momentumScores || momentumScores.length === 0) {
      return {
        totalStocks: 0,
        avgMomentum: 0,
        maxMomentum: 0,
        sectorsCount: 0,
        sectorData: [],
        pieData: []
      };
    }

    const totalStocks = momentumScores.length;
    const avgMomentum = momentumScores.reduce((sum, stock) => sum + stock.momentum_score, 0) / totalStocks;
    const maxMomentum = Math.max(...momentumScores.map(stock => stock.momentum_score));
    const sectors = Array.from(new Set(momentumScores.map(stock => stock.sector)));
    const sectorsCount = sectors.length;

    // Sector breakdown for bar chart
    const sectorCounts = sectors.map(sector => {
      const count = momentumScores.filter(stock => stock.sector === sector).length;
      return { sector, count };
    }).sort((a, b) => b.count - a.count).slice(0, 10);

    // Sector breakdown for pie chart (top 5)
    const pieData = sectorCounts.slice(0, 5).map((item, index) => ({
      name: item.sector,
      value: item.count,
      fill: [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
      ][index % 5]
    }));

    return {
      totalStocks,
      avgMomentum,
      maxMomentum,
      sectorsCount,
      sectorData: sectorCounts,
      pieData
    };
  }, [momentumScores]);

  if (!momentumScores || momentumScores.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Summary Statistics</h2>
        </div>
        <div className="text-center py-8">
          <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No data available for statistics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-6">
          <TrendingUp className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Summary Statistics</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-lg mx-auto mb-3">
              <Target className="h-6 w-6" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{stats.totalStocks}</div>
            <div className="text-sm text-gray-500">Total Stocks Analyzed</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-success-100 text-success-600 rounded-lg mx-auto mb-3">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{stats.avgMomentum ? stats.avgMomentum.toFixed(3) : 'N/A'}</div>
            <div className="text-sm text-gray-500">Average Momentum Score</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-warning-100 text-warning-600 rounded-lg mx-auto mb-3">
              <Award className="h-6 w-6" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{stats.maxMomentum ? stats.maxMomentum.toFixed(3) : 'N/A'}</div>
            <div className="text-sm text-gray-500">Highest Momentum Score</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-lg mx-auto mb-3">
              <Building2 className="h-6 w-6" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{stats.sectorsCount}</div>
            <div className="text-sm text-gray-500">Sectors Covered</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Distribution Bar Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sector Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.sectorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="sector" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sector Distribution Pie Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 5 Sectors</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {stats.pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryStats;
