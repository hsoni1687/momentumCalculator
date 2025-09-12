import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface Strategy {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  color: string;
}

export interface StrategyConfig {
  strategyId: string;
  marketCapLimit: number;
  outputCount: number;
  industry?: string;
  sector?: string;
}

export interface PipelineRequest {
  strategies: StrategyConfig[];
  name?: string;
}

export interface PipelineResult {
  pipelineId: string;
  name: string;
  strategies: StrategyConfig[];
  results: StrategyExecutionResult[];
  finalStocks: StockResult[];
  executionTime: number;
  totalStocksProcessed: number;
  createdAt: string;
}

export interface StrategyExecutionResult {
  strategyId: string;
  strategyName: string;
  inputCount: number;
  outputCount: number;
  executionTime: number;
  stocks: StockResult[];
  metrics: {
    averageScore: number;
    topScore: number;
    bottomScore: number;
  };
}

export interface StockResult {
  stock: string;
  name: string;
  sector: string;
  industry: string;
  score: number;
  currentPrice: number;
  marketCap: number;
  additionalData?: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  database: string;
  version: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async healthCheck(): Promise<HealthResponse> {
    const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
    return response.data;
  }

  async getAvailableStrategies(): Promise<Strategy[]> {
    const response: AxiosResponse<{ strategies: Strategy[] }> = await this.client.get('/strategies');
    return response.data.strategies;
  }

  async executePipeline(pipeline: PipelineRequest): Promise<PipelineResult> {
    const response: AxiosResponse<PipelineResult> = await this.client.post('/pipeline/execute', pipeline);
    return response.data;
  }

  async getPipelineResult(pipelineId: string): Promise<PipelineResult> {
    const response: AxiosResponse<PipelineResult> = await this.client.get(`/pipeline/${pipelineId}`);
    return response.data;
  }

  async getIndustries(): Promise<string[]> {
    const response: AxiosResponse<{ industries: string[] }> = await this.client.get('/industries');
    return response.data.industries;
  }

  async getSectors(): Promise<string[]> {
    const response: AxiosResponse<{ sectors: string[] }> = await this.client.get('/sectors');
    return response.data.sectors;
  }

  async savePipeline(pipeline: PipelineRequest & { name: string }): Promise<{ pipelineId: string }> {
    const response: AxiosResponse<{ pipelineId: string }> = await this.client.post('/pipeline/save', pipeline);
    return response.data;
  }

  async getSavedPipelines(): Promise<Array<{ id: string; name: string; createdAt: string; strategies: StrategyConfig[] }>> {
    const response: AxiosResponse<{ pipelines: Array<{ id: string; name: string; createdAt: string; strategies: StrategyConfig[] }> }> = 
      await this.client.get('/pipeline/saved');
    return response.data.pipelines;
  }
}

export const apiClient = new ApiClient();
