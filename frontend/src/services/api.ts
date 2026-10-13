import axios from 'axios'
import API_BASE_URL from '../config/api'
import type {
  DatasetInfo, DatasetAnalysis, OptimizationConfig,
  OptimizationStatus, OptimizationResult, HistoryItem, Stats, PredictionResponse
} from '../types'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 60000,
})

export const datasetApi = {
  upload: async (file: File): Promise<DatasetInfo> => {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/dataset/upload', form)
    return res.data
  },
  get: async (id: string): Promise<DatasetInfo> => {
    const res = await api.get(`/dataset/${id}`)
    return res.data
  },
  analyze: async (id: string): Promise<DatasetAnalysis> => {
    const res = await api.post(`/dataset/${id}/analyze`)
    return res.data
  },
  updateConfig: async (id: string, config: {
    target_column: string
    features: string[]
    problem_type?: string
    handle_missing?: boolean
    encode_categorical?: boolean
    standardize?: boolean
    remove_duplicates?: boolean
  }): Promise<DatasetInfo> => {
    const res = await api.post(`/dataset/${id}/config`, config)
    return res.data
  },
}

export const optimizationApi = {
  start: async (config: OptimizationConfig): Promise<{ optimization_id: string }> => {
    const res = await api.post('/optimization/start', config)
    return res.data
  },
  getStatus: async (id: string): Promise<OptimizationStatus> => {
    const res = await api.get(`/optimization/${id}/status`)
    return res.data
  },
  getResults: async (id: string): Promise<OptimizationResult> => {
    const res = await api.get(`/optimization/${id}/results`)
    return res.data
  },
  control: async (id: string, action: string): Promise<void> => {
    await api.post(`/optimization/${id}/control`, { action })
  },
  getModelDownloadUrl: (id: string): string => `${API_BASE_URL}/api/optimization/${id}/download-model`,
  getReportDownloadUrl: (id: string): string => `${API_BASE_URL}/api/optimization/${id}/download-report`,
}

export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const res = await axios.get(`${API_BASE_URL}/health`)
    return res.data
  },
}

export const predictionApi = {
  predict: async (optimization_id: string, features: Record<string, unknown>): Promise<PredictionResponse> => {
    const res = await api.post('/prediction', { optimization_id, features })
    return res.data
  },
}

export const historyApi = {
  list: async (): Promise<HistoryItem[]> => {
    const res = await api.get('/history')
    return res.data
  },
  get: async (id: string): Promise<HistoryItem> => {
    const res = await api.get(`/history/${id}`)
    return res.data
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/history/${id}`)
  },
}

export const statsApi = {
  get: async (): Promise<Stats> => {
    const res = await api.get('/stats')
    return res.data
  },
}
