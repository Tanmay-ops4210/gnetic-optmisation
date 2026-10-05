export interface DatasetInfo {
  id: string
  filename: string
  original_name: string
  rows: number
  cols: number
  file_size: number
  target_column?: string
  features?: string[]
  problem_type?: string
  created_at: string
}

export interface ColumnInfo {
  name: string
  dtype: string
  missing: number
  unique: number
  sample_values: (string | number)[]
}

export interface DatasetAnalysis {
  id: string
  rows: number
  cols: number
  columns: ColumnInfo[]
  missing_total: number
  duplicate_rows: number
  preview: Record<string, unknown>[]
}

export interface OptimizationConfig {
  dataset_id: string
  target_column: string
  features: string[]
  problem_type: string
  models: string[]
  optimization_method: string
  metric: string
  population_size: number
  generations: number
  mutation_rate: number
  crossover_rate: number
  selection_method: string
  cv_folds: number
  test_size: number
  handle_missing: boolean
  encode_categorical: boolean
  standardize: boolean
  remove_duplicates: boolean
}

export interface OptimizationStatus {
  id: string
  status: string
  stage: string
  stage_index: number
  total_stages: number
  generation: number
  total_generations: number
  best_score: number
  avg_score: number
  models_tested: number
  best_model: string
  best_params: Record<string, unknown>
  logs: string[]
  fitness_history: { generation: number; best: number; avg: number }[]
  model_scores: { model: string; score: number; time: number; type: string }[]
  progress_pct: number
}

export interface OptimizationResult {
  id: string
  status: string
  best_model: string
  best_params: Record<string, unknown>
  best_score: number
  baseline_score: number
  improvement: number
  metric: string
  problem_type: string
  total_generations: number
  population_size: number
  models_tested: number
  duration: number
  fitness_history: { generation: number; best: number; avg: number }[]
  model_comparison: { model: string; score: number; time: number; type: string }[]
  confusion_matrix?: number[][]
  feature_importance?: Record<string, number>
  actual_vs_predicted?: { actual: number; predicted: number }[]
  class_labels?: string[]
}

export interface HistoryItem {
  id: string
  optimization_id: string
  dataset_name: string
  model_name: string
  problem_type: string
  score: number
  optimization_method: string
  duration: number
  created_at: string
  optimization_result?: OptimizationResult
}

export interface Stats {
  datasets_processed: number
  optimizations_completed: number
  best_score: number
  models_tested: number
}

export interface PredictionResponse {
  prediction: string | number
  confidence?: number
  class_probabilities?: Record<string, number>
  problem_type: string
}
