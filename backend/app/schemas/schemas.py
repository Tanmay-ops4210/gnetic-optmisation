from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class DatasetInfo(BaseModel):
    id: str
    filename: str
    original_name: str
    rows: int
    cols: int
    file_size: int
    target_column: Optional[str] = None
    features: Optional[List[str]] = None
    problem_type: Optional[str] = None
    created_at: str

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    missing: int
    unique: int
    sample_values: List[Any]

class DatasetAnalysis(BaseModel):
    id: str
    rows: int
    cols: int
    columns: List[ColumnInfo]
    missing_total: int
    duplicate_rows: int
    preview: List[Dict[str, Any]]  # first 10 rows

class OptimizationConfig(BaseModel):
    dataset_id: str
    target_column: str
    features: List[str]
    problem_type: str  # classification or regression
    models: List[str]
    optimization_method: str  # genetic, grid, random, genetic+random, genetic+grid
    metric: str  # accuracy, f1, r2, rmse, mae
    # GA params
    population_size: int = 20
    generations: int = 30
    mutation_rate: float = 0.2
    crossover_rate: float = 0.8
    selection_method: str = 'tournament'  # tournament or roulette
    # Search params
    cv_folds: int = 5
    test_size: float = 0.2
    # Preprocessing
    handle_missing: bool = True
    encode_categorical: bool = True
    standardize: bool = True
    remove_duplicates: bool = True

class OptimizationStatus(BaseModel):
    id: str
    status: str
    stage: str
    stage_index: int
    total_stages: int
    generation: int
    total_generations: int
    best_score: float
    avg_score: float
    models_tested: int
    best_model: str
    best_params: Dict[str, Any]
    logs: List[str]
    fitness_history: List[Dict[str, float]]  # [{generation, best, avg}]
    model_scores: List[Dict[str, Any]]  # [{model, score, time}]
    progress_pct: float

class OptimizationResult(BaseModel):
    id: str
    status: str
    best_model: str
    best_params: Dict[str, Any]
    best_score: float
    baseline_score: float
    improvement: float
    metric: str
    problem_type: str
    total_generations: int
    population_size: int
    models_tested: int
    duration: float
    fitness_history: List[Dict[str, float]]
    model_comparison: List[Dict[str, Any]]
    confusion_matrix: Optional[List[List[int]]] = None
    feature_importance: Optional[Dict[str, float]] = None
    actual_vs_predicted: Optional[List[Dict[str, float]]] = None
    class_labels: Optional[List[str]] = None

class PredictionRequest(BaseModel):
    optimization_id: str
    features: Dict[str, Any]

class PredictionResponse(BaseModel):
    prediction: Any
    confidence: Optional[float] = None
    class_probabilities: Optional[Dict[str, float]] = None
    problem_type: str

class HistoryItem(BaseModel):
    id: str
    optimization_id: str
    dataset_name: str
    model_name: str
    problem_type: str
    score: float
    optimization_method: str
    duration: float
    created_at: str

class DatasetConfigUpdate(BaseModel):
    target_column: str
    features: List[str]
    problem_type: Optional[str] = None
    handle_missing: bool = True
    encode_categorical: bool = True
    standardize: bool = True
    remove_duplicates: bool = True
