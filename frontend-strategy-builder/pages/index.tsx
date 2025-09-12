import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '@/components/Layout';
import PipelineBuilder from '@/components/PipelineBuilder';
import ResultsAnalysis from '@/components/ResultsAnalysis';
import { 
  apiClient, 
  Strategy, 
  StrategyConfig, 
  PipelineResult,
  HealthResponse 
} from '@/services/api';
import { 
  Play, 
  Save, 
  Loader2, 
  AlertCircle, 
  CheckCircle,
  Zap,
  Target,
  BarChart3
} from 'lucide-react';

type ViewMode = 'builder' | 'results';

const Home: React.FC = () => {
  // State management
  const [viewMode, setViewMode] = useState<ViewMode>('builder');
  const [availableStrategies, setAvailableStrategies] = useState<Strategy[]>([]);
  const [pipeline, setPipeline] = useState<StrategyConfig[]>([]);
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pipelineResults, setPipelineResults] = useState<any[]>([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Auto-execute pipeline when it changes
  useEffect(() => {
    if (pipeline.length > 0) {
      executePipeline();
    } else {
      setPipelineResults([]);
      setPipelineResult(null);
    }
  }, [pipeline]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check health
      const health = await apiClient.healthCheck();
      setHealthData(health);

      // Load available strategies
      const strategies = await apiClient.getAvailableStrategies();
      setAvailableStrategies(strategies);

      console.log('Data loaded successfully!');
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Failed to connect to the API. Please ensure the backend is running.');
      console.error('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePipelineChange = (newPipeline: StrategyConfig[]) => {
    setPipeline(newPipeline);
  };

  const executePipeline = async () => {
    if (pipeline.length === 0) {
      return;
    }

    try {
      setIsExecuting(true);
      console.log('Executing pipeline...');

      const result = await apiClient.executePipeline({
        strategies: pipeline,
        name: `Pipeline ${new Date().toLocaleString()}`
      });

      console.log('DEBUG: Full pipeline result:', JSON.stringify(result, null, 2));
      console.log('DEBUG: Results array:', result.results);
      if (result.results && result.results[0] && result.results[0].stocks) {
        console.log('DEBUG: First few stocks:', result.results[0].stocks.slice(0, 3));
        console.log('DEBUG: First stock score:', result.results[0].stocks[0]?.score);
      }

      setPipelineResult(result);
      setPipelineResults(result.results || []);
      
      console.log('Pipeline executed successfully!');
    } catch (err) {
      console.error('Pipeline execution failed:', err);
      setPipelineResults([]);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSave = async () => {
    if (pipeline.length === 0) {
      console.error('Please add at least one strategy to the pipeline');
      return;
    }

    try {
      const pipelineName = prompt('Enter a name for your pipeline:');
      if (!pipelineName) return;

      await apiClient.savePipeline({
        strategies: pipeline,
        name: pipelineName
      });

      console.log('Pipeline saved successfully!');
    } catch (err) {
      console.error('Failed to save pipeline:', err);
      console.error('Failed to save pipeline');
    }
  };

  const handleBackToBuilder = () => {
    setViewMode('builder');
    setPipelineResult(null);
  };

  if (isLoading) {
    return (
      <Layout title="Loading...">
        <div className="min-h-screen flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <Loader2 size={48} className="mx-auto mb-4 text-primary-600 animate-spin" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Strategy Builder</h2>
            <p className="text-gray-600">Setting up your trading pipeline...</p>
          </motion.div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Error">
        <div className="min-h-screen flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-md"
          >
            <AlertCircle size={48} className="mx-auto mb-4 text-red-500" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={loadInitialData}
              className="btn-primary"
            >
              Retry Connection
            </button>
          </motion.div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <Zap size={24} className="text-primary-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Strategy Builder</h1>
                  <p className="text-sm text-gray-600">Build custom trading pipelines</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Health Status */}
              <div className="flex items-center space-x-2">
                {healthData?.status === 'healthy' ? (
                  <CheckCircle size={16} className="text-green-500" />
                ) : (
                  <AlertCircle size={16} className="text-red-500" />
                )}
                <span className="text-sm text-gray-600">
                  {healthData?.status === 'healthy' ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {/* View Mode Indicator */}
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                {viewMode === 'builder' ? (
                  <>
                    <Target size={16} />
                    <span>Builder</span>
                  </>
                ) : (
                  <>
                    <BarChart3 size={16} />
                    <span>Results</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          {viewMode === 'builder' ? (
            <motion.div
              key="builder"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <PipelineBuilder
                availableStrategies={availableStrategies}
                pipeline={pipeline}
                onPipelineChange={handlePipelineChange}
                onSave={handleSave}
                pipelineResults={pipelineResults}
                isExecuting={isExecuting}
              />
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {pipelineResult && (
                <ResultsAnalysis
                  result={pipelineResult}
                  onBack={handleBackToBuilder}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Floating Action Button for Mobile */}
      <div className="fixed bottom-6 right-6 md:hidden">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setViewMode(viewMode === 'builder' ? 'results' : 'builder')}
          className="p-4 bg-primary-600 text-white rounded-full shadow-lg"
        >
          {viewMode === 'builder' ? <BarChart3 size={24} /> : <Target size={24} />}
        </motion.button>
      </div>
    </Layout>
  );
};

export default Home;
