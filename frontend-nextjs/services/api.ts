import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface Stock {
  stock: string;
  name: string;
  sector: string;
  industry: string;
}

export interface MomentumScore {
  stock: string;
  name: string;
  sector: string;
  industry: string;
  momentum_score: number;
  fip_quality: number;
  last_price_date?: string;
  
  // 12-2 Month momentum (Alpha Architect primary measure)
  raw_momentum_12_2: number;
  
  // True momentum (considering trend consistency and quality)
  true_momentum_6m: number;
  true_momentum_3m: number;
  true_momentum_1m: number;
  
  // Simple returns for reference
  raw_return_6m: number;
  raw_return_3m: number;
  raw_return_1m: number;
  
  // Legacy fields for backward compatibility
  raw_momentum_6m: number;
  raw_momentum_3m: number;
  raw_momentum_1m: number;
}

export interface MomentumResponse {
  momentum_scores: MomentumScore[];
  top_stocks: MomentumScore[];
  count: number;
  filters: {
    limit: number;
    industry?: string;
    sector?: string;
    top_n: number;
  };
}

export interface StocksResponse {
  stocks: Stock[];
  count: number;
  filters: {
    limit: number;
    industry?: string;
    sector?: string;
  };
}

export interface HealthResponse {
  status: string;
  database: string;
  version: string;
}

export interface SectorMomentumResponse {
  sector_momentum: Record<string, any>;
  count: number;
  filters: {
    limit: number;
    industry?: string;
    sector?: string;
  };
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
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

  async getStocks(
    limit: number = 50,
    industry?: string,
    sector?: string
  ): Promise<StocksResponse> {
    const params: any = { limit };
    if (industry) params.industry = industry;
    if (sector) params.sector = sector;

    const response: AxiosResponse<StocksResponse> = await this.client.get('/stocks', {
      params,
    });
    return response.data;
  }

  async getStockInfo(symbol: string): Promise<{ stock: Stock }> {
    const response: AxiosResponse<{ stock: Stock }> = await this.client.get(`/stocks/${symbol}`);
    return response.data;
  }

  async calculateMomentum(
    limit: number = 50,
    industry?: string,
    sector?: string,
    topN: number = 10
  ): Promise<MomentumResponse> {
    const params: any = { limit, top_n: topN };
    if (industry) params.industry = industry;
    if (sector) params.sector = sector;

    const response: AxiosResponse<MomentumResponse> = await this.client.get('/momentum', {
      params,
    });
    return response.data;
  }

  async getMomentumBySector(
    limit: number = 50,
    industry?: string,
    sector?: string
  ): Promise<SectorMomentumResponse> {
    const params: any = { limit };
    if (industry) params.industry = industry;
    if (sector) params.sector = sector;

    const response: AxiosResponse<SectorMomentumResponse> = await this.client.get('/momentum/sectors', {
      params,
    });
    return response.data;
  }

  async clearCache(): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.client.post('/cache/clear');
    return response.data;
  }
}

export const apiClient = new ApiClient();
