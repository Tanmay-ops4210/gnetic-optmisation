import os
import uuid
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import joblib
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sklearn.model_selection import train_test_split

from ..schemas.schemas import (
    DatasetInfo, DatasetAnalysis, ColumnInfo, DatasetConfigUpdate,
    OptimizationConfig, OptimizationStatus, OptimizationResult,
    PredictionRequest, PredictionResponse, HistoryItem
)
from ..database.db import get_db
from ..ml.preprocessing import Preprocessor, detect_problem_type, load_and_clean_csv
from ..ml.model_manager import (
    get_model_registry, build_model,
    CLASSIFICATION_MODELS, REGRESSION_MODELS
)
from ..ml.evaluation import (
    evaluate_model, evaluate_on_test, get_feature_importance, get_cv_scorer
)
from ..optimization.genetic_algorithm import GeneticAlgorithm
from ..optimization.search_optimizer import run_grid_search, run_random_search

router = APIRouter()

def _get_storage_dirs():
    if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        uploads = '/tmp/uploads'
        models = '/tmp/saved_models'
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        uploads = os.path.join(base_dir, 'uploads')
        models = os.path.join(base_dir, 'saved_models')
        try:
            os.makedirs(uploads, exist_ok=True)
            os.makedirs(models, exist_ok=True)
            test_f = os.path.join(uploads, '.write_check')
            with open(test_f, 'w') as f:
                f.write('')
            os.remove(test_f)
            return uploads, models
        except OSError:
            uploads = '/tmp/uploads'
            models = '/tmp/saved_models'

    os.makedirs(uploads, exist_ok=True)
    os.makedirs(models, exist_ok=True)
    return uploads, models

UPLOADS_DIR, MODELS_DIR = _get_storage_dirs()

# In-memory state stores
optimization_states: Dict[str, dict] = {}
stop_flags: Dict[str, list] = {}
preprocessors: Dict[str, Preprocessor] = {}  # optimization_id -> preprocessor

STAGES = [
    'Loading Dataset',
    'Preprocessing',
    'Computing Baseline',
    'Initializing Population',
    'Running Genetic Algorithm',
    'Running Search Optimization',
    'Evaluating Final Model',
    'Training Final Model',
    'Saving Results',
]

def _default_state(opt_id: str, config: dict) -> dict:
    return {
        'id': opt_id,
        'status': 'pending',
        'stage': 'Loading Dataset',
        'stage_index': 0,
        'total_stages': len(STAGES),
        'generation': 0,
        'total_generations': config.get('generations', 30),
        'best_score': 0.0,
        'avg_score': 0.0,
        'models_tested': 0,
        'best_model': '',
        'best_params': {},
        'logs': [],
        'fitness_history': [],
        'model_scores': [],
        'progress_pct': 0.0,
    }

def _log(state: dict, msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    state['logs'].append(f'[{ts}] {msg}')

def _update_stage(state: dict, stage_name: str):
    idx = STAGES.index(stage_name) if stage_name in STAGES else state['stage_index']
    state['stage'] = stage_name
    state['stage_index'] = idx
    state['progress_pct'] = round((idx / len(STAGES)) * 100, 1)
    _log(state, stage_name)

def run_optimization(opt_id: str, config_dict: dict):
    state = optimization_states[opt_id]
    stop_flag = stop_flags[opt_id]
    db = get_db()
    
    try:
        state['status'] = 'running'
        db.execute(
            'UPDATE optimizations SET status=?, updated_at=? WHERE id=?',
            ('running', datetime.utcnow().isoformat(), opt_id)
        )
        db.commit()
        
        # 1. Load dataset
        _update_stage(state, 'Loading Dataset')
        dataset_id = config_dict['dataset_id']
        row = db.execute('SELECT * FROM datasets WHERE id=?', (dataset_id,)).fetchone()
        if not row:
            raise ValueError('Dataset not found')
        
        filepath = os.path.join(UPLOADS_DIR, row['filename'])
        df = load_and_clean_csv(filepath)
        _log(state, f'Dataset loaded: {len(df)} rows, {len(df.columns)} cols')
        
        if stop_flag[0]:
            raise InterruptedError('Cancelled')
        
        # 2. Preprocessing
        _update_stage(state, 'Preprocessing')
        target_col = config_dict['target_column']
        features = config_dict['features']
        problem_type = config_dict['problem_type']
        metric = config_dict['metric']
        
        if config_dict.get('remove_duplicates', True):
            before = len(df)
            df = df.drop_duplicates()
            _log(state, f'Removed {before - len(df)} duplicate rows')
        
        preprocessor = Preprocessor()
        X, y = preprocessor.fit_transform(
            df, target_col, features,
            handle_missing=config_dict.get('handle_missing', True),
            encode_categorical=config_dict.get('encode_categorical', True),
            standardize=config_dict.get('standardize', True),
            remove_duplicates=False,  # already done
            problem_type=problem_type
        )
        preprocessors[opt_id] = preprocessor
        
        test_size = config_dict.get('test_size', 0.2)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        _log(state, f'Train: {len(X_train)} | Test: {len(X_test)}')
        
        cv_folds = config_dict.get('cv_folds', 5)
        scorer_str = get_cv_scorer(metric)
        registry = get_model_registry(problem_type)
        selected_models = config_dict.get('models', list(registry.keys()))
        # Filter to only valid models
        selected_models = [m for m in selected_models if m in registry]
        if not selected_models:
            selected_models = list(registry.keys())[:3]
        
        if stop_flag[0]:
            raise InterruptedError('Cancelled')
        
        # 3. Baseline
        _update_stage(state, 'Computing Baseline')
        baseline_scores = {}
        for mname in selected_models:
            if stop_flag[0]:
                break
            try:
                model = build_model(mname, problem_type, {})
                t0 = time.time()
                score = evaluate_model(model, X_train, y_train, metric, cv_folds)
                duration = round(time.time() - t0, 2)
                if metric in ('mae', 'mse', 'rmse'):
                    score = abs(score)
                baseline_scores[mname] = score
                state['model_scores'].append({'model': mname, 'score': round(score, 4), 'time': duration, 'type': 'baseline'})
                state['models_tested'] += 1
                _log(state, f'Baseline {mname}: {score:.4f}')
            except Exception as e:
                _log(state, f'Baseline {mname} failed: {e}')
        
        # Pick best baseline
        if not baseline_scores:
            raise ValueError('All baseline models failed')
        
        if metric in ('mae', 'mse', 'rmse'):
            best_baseline_model = min(baseline_scores, key=baseline_scores.get)
            baseline_best = baseline_scores[best_baseline_model]
        else:
            best_baseline_model = max(baseline_scores, key=baseline_scores.get)
            baseline_best = baseline_scores[best_baseline_model]
        
        state['best_model'] = best_baseline_model
        state['best_score'] = round(baseline_best, 4)
        _log(state, f'Best baseline: {best_baseline_model} = {baseline_best:.4f}')
        
        best_model_name = best_baseline_model
        best_params = {}
        best_score = baseline_best
        best_estimator = None
        
        if stop_flag[0]:
            raise InterruptedError('Cancelled')
        
        opt_method = config_dict.get('optimization_method', 'genetic')
        
        # 4. Genetic Algorithm
        if 'genetic' in opt_method:
            _update_stage(state, 'Initializing Population')
            pop_size = config_dict.get('population_size', 20)
            generations = config_dict.get('generations', 30)
            mutation_rate = config_dict.get('mutation_rate', 0.2)
            crossover_rate = config_dict.get('crossover_rate', 0.8)
            selection_method = config_dict.get('selection_method', 'tournament')
            
            state['total_generations'] = generations
            
            def fitness_fn(model_name: str, params: dict) -> float:
                try:
                    model = build_model(model_name, problem_type, params)
                    score = evaluate_model(model, X_train, y_train, metric, cv_folds)
                    if metric in ('mae', 'mse', 'rmse'):
                        return max(0, 1.0 / (1.0 + score))
                    return score
                except Exception:
                    return 0.0
            
            def ga_callback(generation: int, best_ind, avg_fitness: float, population):
                state['generation'] = generation
                state['best_model'] = best_ind.model_name
                actual_score = best_ind.fitness
                if metric in ('mae', 'mse', 'rmse'):
                    actual_score = best_ind.fitness  # inverted
                state['best_score'] = round(actual_score, 4)
                state['avg_score'] = round(avg_fitness, 4)
                state['best_params'] = best_ind.params
                state['models_tested'] = len(ga.all_evaluated)
                state['fitness_history'].append({
                    'generation': generation,
                    'best': round(best_ind.fitness, 6),
                    'avg': round(avg_fitness, 6),
                })
                state['progress_pct'] = round(
                    (4 / len(STAGES) + (generation / generations) * (1 / len(STAGES))) * 100, 1
                )
                _log(state, f'Generation {generation}/{generations} | Best: {best_ind.model_name} {actual_score:.4f}')
                _update_stage(state, 'Running Genetic Algorithm')
            
            ga = GeneticAlgorithm(
                population_size=pop_size,
                generations=generations,
                mutation_rate=mutation_rate,
                crossover_rate=crossover_rate,
                selection_method=selection_method,
                fitness_fn=fitness_fn,
                model_names=selected_models,
                model_registry=registry,
                callback=ga_callback,
                stop_flag=stop_flag,
            )
            
            best_ind = ga.run()
            
            if best_ind and best_ind.fitness > 0:
                ga_score = best_ind.fitness
                if metric not in ('mae', 'mse', 'rmse'):
                    if ga_score > best_score:
                        best_score = ga_score
                        best_model_name = best_ind.model_name
                        best_params = best_ind.params
                else:
                    real_score = (1.0 / best_ind.fitness - 1.0) if best_ind.fitness > 0 else 999
                    if real_score < best_score or best_score == baseline_best:
                        best_score = real_score
                        best_model_name = best_ind.model_name
                        best_params = best_ind.params
                
                state['fitness_history'] = ga.fitness_history
                state['models_tested'] = len(ga.all_evaluated)
                _log(state, f'GA complete. Best: {best_model_name} {best_score:.4f}')
        
        if stop_flag[0]:
            raise InterruptedError('Cancelled')
        
        # 5. Search optimization
        if 'grid' in opt_method or 'random' in opt_method:
            _update_stage(state, 'Running Search Optimization')
            search_model = build_model(best_model_name, problem_type, {})
            search_space = registry[best_model_name]['search_space']
            
            try:
                if 'grid' in opt_method:
                    result = run_grid_search(
                        search_model, X_train, y_train,
                        search_space, cv=cv_folds, scoring=scorer_str
                    )
                    _log(state, f'Grid Search complete. Best: {result["best_score"]:.4f}')
                else:
                    from scipy.stats import randint, uniform
                    # Convert search_space lists to distributions for RandomizedSearch
                    result = run_random_search(
                        search_model, X_train, y_train,
                        search_space, n_iter=30, cv=cv_folds, scoring=scorer_str
                    )
                    _log(state, f'Random Search complete. Best: {result["best_score"]:.4f}')
                
                search_score = abs(result['best_score'])
                if metric in ('mae', 'mse', 'rmse'):
                    if search_score < best_score:
                        best_score = search_score
                        best_params = result['best_params']
                        best_estimator = result['best_estimator']
                else:
                    if search_score > best_score:
                        best_score = search_score
                        best_params = result['best_params']
                        best_estimator = result['best_estimator']
                
                state['best_score'] = round(best_score, 4)
                state['best_params'] = best_params
            except Exception as e:
                _log(state, f'Search optimization error: {e}')
        
        if stop_flag[0]:
            raise InterruptedError('Cancelled')
        
        # 6. Train final model
        _update_stage(state, 'Evaluating Final Model')
        if best_estimator is None:
            final_model = build_model(best_model_name, problem_type, best_params)
        else:
            final_model = best_estimator
        
        _update_stage(state, 'Training Final Model')
        eval_result = evaluate_on_test(
            final_model, X_train, X_test, y_train, y_test, metric, problem_type
        )
        
        final_score = eval_result['primary_score']
        feature_importance = get_feature_importance(final_model, preprocessor.feature_names)
        
        # Build model comparison list
        model_comparison = []
        for ms in state['model_scores']:
            model_comparison.append(ms)
        model_comparison.append({
            'model': f'{best_model_name} (Optimized)',
            'score': round(final_score, 4),
            'time': 0,
            'type': 'optimized'
        })
        
        # 7. Save model
        _update_stage(state, 'Saving Results')
        model_path = os.path.join(MODELS_DIR, f'{opt_id}.joblib')
        joblib.dump({'model': final_model, 'preprocessor': preprocessor}, model_path)
        
        class_labels = preprocessor.get_class_labels()
        
        duration = sum(1 for _ in state['logs'])  # approximate
        
        result_data = {
            'id': opt_id,
            'status': 'completed',
            'best_model': best_model_name,
            'best_params': best_params,
            'best_score': round(final_score, 6),
            'baseline_score': round(baseline_best, 6),
            'improvement': round(final_score - baseline_best, 6),
            'metric': metric,
            'problem_type': problem_type,
            'total_generations': config_dict.get('generations', 30),
            'population_size': config_dict.get('population_size', 20),
            'models_tested': state['models_tested'],
            'duration': round(time.time() - time.mktime(datetime.utcnow().timetuple()), 2),
            'fitness_history': state['fitness_history'],
            'model_comparison': model_comparison,
            'confusion_matrix': eval_result.get('confusion_matrix'),
            'feature_importance': feature_importance,
            'actual_vs_predicted': eval_result.get('actual_vs_predicted'),
            'class_labels': class_labels,
        }
        
        db.execute(
            'UPDATE optimizations SET status=?, result=?, updated_at=? WHERE id=?',
            ('completed', json.dumps(result_data), datetime.utcnow().isoformat(), opt_id)
        )
        
        # Save to history
        hist_id = str(uuid.uuid4())
        db.execute(
            'INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?)',
            (
                hist_id, opt_id,
                row['original_name'],
                best_model_name,
                problem_type,
                round(final_score, 6),
                opt_method,
                0.0,
                datetime.utcnow().isoformat()
            )
        )
        db.commit()
        
        state['status'] = 'completed'
        state['best_score'] = round(final_score, 4)
        state['best_model'] = best_model_name
        state['best_params'] = best_params
        state['progress_pct'] = 100.0
        _log(state, f'Optimization complete! Best: {best_model_name} {final_score:.4f}')
        
    except InterruptedError:
        state['status'] = 'cancelled'
        db.execute('UPDATE optimizations SET status=? WHERE id=?', ('cancelled', opt_id))
        db.commit()
        _log(state, 'Optimization cancelled by user')
    except Exception as e:
        state['status'] = 'failed'
        state['logs'].append(f'[ERROR] {str(e)}')
        db.execute(
            'UPDATE optimizations SET status=?, updated_at=? WHERE id=?',
            ('failed', datetime.utcnow().isoformat(), opt_id)
        )
        db.commit()
        _log(state, f'Failed: {e}')
    finally:
        db.close()

@router.post('/dataset/upload')
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, 'Only CSV files are accepted')
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, 'File too large. Max 50MB.')
    if len(content) == 0:
        raise HTTPException(400, 'File is empty')
    
    # Validate and clean CSV
    try:
        import io
        df = load_and_clean_csv(io.BytesIO(content))
        if df.empty or len(df.columns) < 2:
            raise HTTPException(400, 'CSV must have at least 2 columns and 1 row')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f'Invalid CSV: {e}')
    
    dataset_id = str(uuid.uuid4())
    filename = f'{dataset_id}.csv'
    filepath = os.path.join(UPLOADS_DIR, filename)
    
    # Save the cleaned CSV
    df.to_csv(filepath, index=False)
    
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute(
        'INSERT INTO datasets (id, filename, original_name, rows, cols, file_size, created_at) VALUES (?,?,?,?,?,?,?)',
        (dataset_id, filename, file.filename, len(df), len(df.columns), len(content), now)
    )
    db.commit()
    db.close()
    
    return {
        'id': dataset_id,
        'filename': filename,
        'original_name': file.filename,
        'rows': len(df),
        'cols': len(df.columns),
        'file_size': len(content),
        'created_at': now
    }

@router.get('/dataset/{dataset_id}')
async def get_dataset(dataset_id: str):
    db = get_db()
    row = db.execute('SELECT * FROM datasets WHERE id=?', (dataset_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, 'Dataset not found')
    data = dict(row)
    if data.get('features'):
        data['features'] = json.loads(data['features'])
    return data

@router.post('/dataset/{dataset_id}/analyze')
async def analyze_dataset(dataset_id: str):
    db = get_db()
    row = db.execute('SELECT * FROM datasets WHERE id=?', (dataset_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, 'Dataset not found')
    
    filepath = os.path.join(UPLOADS_DIR, row['filename'])
    try:
        df = load_and_clean_csv(filepath)
    except Exception as e:
        raise HTTPException(500, f'Error reading CSV: {e}')
    
    columns = []
    for col in df.columns:
        sample_vals = df[col].dropna().head(3).tolist()
        sample_vals = [str(v) if not isinstance(v, (int, float)) else v for v in sample_vals]
        columns.append({
            'name': col,
            'dtype': str(df[col].dtype),
            'missing': int(df[col].isna().sum()),
            'unique': int(df[col].nunique()),
            'sample_values': sample_vals
        })
        
    return {
        'id': dataset_id,
        'rows': len(df),
        'cols': len(df.columns),
        'columns': columns,
        'missing_total': int(df.isna().sum().sum()),
        'duplicate_rows': int(df.duplicated().sum()),
        'preview': df.head(10).replace({np.nan: None}).to_dict(orient='records')
    }

@router.post('/dataset/{dataset_id}/config')
async def config_dataset(dataset_id: str, config: DatasetConfigUpdate):
    db = get_db()
    row = db.execute('SELECT * FROM datasets WHERE id=?', (dataset_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, 'Dataset not found')
        
    prob_type = config.problem_type
    if not prob_type:
        filepath = os.path.join(UPLOADS_DIR, row['filename'])
        df = load_and_clean_csv(filepath)
        prob_type = detect_problem_type(df, config.target_column)
        
    features_json = json.dumps(config.features)
    
    db.execute(
        'UPDATE datasets SET target_column=?, features=?, problem_type=? WHERE id=?',
        (config.target_column, features_json, prob_type, dataset_id)
    )
    db.commit()
    db.close()
    
    return await get_dataset(dataset_id)

@router.post('/optimization/start')
async def start_optimization(config: OptimizationConfig, background_tasks: BackgroundTasks):
    opt_id = str(uuid.uuid4())
    
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute(
        'INSERT INTO optimizations (id, dataset_id, status, config, created_at, updated_at) VALUES (?,?,?,?,?,?)',
        (opt_id, config.dataset_id, 'pending', config.model_dump_json(), now, now)
    )
    db.commit()
    db.close()
    
    optimization_states[opt_id] = _default_state(opt_id, config.model_dump())
    stop_flags[opt_id] = [False]
    
    background_tasks.add_task(run_optimization, opt_id, config.model_dump())
    
    return {'optimization_id': opt_id}

@router.get('/optimization/{opt_id}/status')
async def get_optimization_status(opt_id: str):
    if opt_id not in optimization_states:
        raise HTTPException(404, 'Optimization status not found in memory')
    return optimization_states[opt_id]

@router.get('/optimization/{opt_id}/results')
async def get_optimization_results(opt_id: str):
    db = get_db()
    row = db.execute('SELECT * FROM optimizations WHERE id=?', (opt_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, 'Optimization not found')
    
    if row['status'] != 'completed' or not row['result']:
        raise HTTPException(400, 'Optimization is not completed yet')
        
    return json.loads(row['result'])

@router.get('/optimization/{opt_id}/download-model')
async def download_model(opt_id: str):
    model_path = os.path.join(MODELS_DIR, f'{opt_id}.joblib')
    if not os.path.exists(model_path):
        raise HTTPException(404, 'Trained model file not found')
    
    db = get_db()
    row = db.execute('SELECT result FROM optimizations WHERE id=?', (opt_id,)).fetchone()
    db.close()
    
    best_model_name = 'model'
    if row and row['result']:
        try:
            r = json.loads(row['result'])
            best_model_name = r.get('best_model', 'model').replace(' ', '_').lower()
        except Exception:
            pass
            
    filename = f'best_model_{best_model_name}_{opt_id[:8]}.joblib'
    return FileResponse(
        model_path,
        media_type='application/octet-stream',
        filename=filename
    )

@router.get('/optimization/{opt_id}/download-report')
async def download_report(opt_id: str):
    db = get_db()
    opt_row = db.execute('SELECT * FROM optimizations WHERE id=?', (opt_id,)).fetchone()
    if not opt_row:
        db.close()
        raise HTTPException(404, 'Optimization not found')
        
    if opt_row['status'] != 'completed' or not opt_row['result']:
        db.close()
        raise HTTPException(400, 'Optimization is not completed yet')
        
    result_data = json.loads(opt_row['result'])
    
    dataset_name = 'Uploaded Dataset'
    if opt_row['dataset_id']:
        ds_row = db.execute('SELECT original_name FROM datasets WHERE id=?', (opt_row['dataset_id'],)).fetchone()
        if ds_row:
            dataset_name = ds_row['original_name']
    db.close()
    
    metadata = {
        'dataset_name': dataset_name,
        'created_at': opt_row['created_at'],
    }
    
    try:
        from ..reporting.report_maker import PDFReportMaker
        report_maker = PDFReportMaker(result_data, metadata)
        pdf_bytes = report_maker.generate()
    except Exception as e:
        raise HTTPException(500, f'Error generating PDF report: {e}')
        
    filename = f'automl_report_{opt_id[:8]}.pdf'
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@router.post('/optimization/{opt_id}/control')
async def control_optimization(opt_id: str, action_data: dict):
    action = action_data.get('action')
    if opt_id not in stop_flags:
        raise HTTPException(404, 'Optimization not found')
    if action in ('stop', 'cancel'):
        stop_flags[opt_id][0] = True
        return {'success': True}
    return {'success': False, 'message': 'Unknown action'}

@router.post('/prediction')
async def make_prediction(req: PredictionRequest):
    model_path = os.path.join(MODELS_DIR, f'{req.optimization_id}.joblib')
    if not os.path.exists(model_path):
        raise HTTPException(404, 'Model not found')
        
    data = joblib.load(model_path)
    model = data['model']
    preprocessor = data['preprocessor']
    
    try:
        X = preprocessor.transform_single(req.features)
    except Exception as e:
        raise HTTPException(400, f'Error preprocessing features: {e}')
        
    prediction = model.predict(X)[0]
    
    result = {
        'prediction': prediction,
        'problem_type': preprocessor.problem_type
    }
    
    if preprocessor.problem_type == 'classification':
        if preprocessor.target_encoder:
            # Convert back to original label if it was encoded
            result['prediction'] = preprocessor.target_encoder.inverse_transform([prediction])[0]
        
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X)[0]
            result['confidence'] = round(float(np.max(proba)), 4)
            
            classes = preprocessor.get_class_labels() or range(len(proba))
            result['class_probabilities'] = {
                str(c): round(float(p), 4) for c, p in zip(classes, proba)
            }
            
    return result

@router.get('/history')
async def get_history():
    try:
        db = get_db()
        rows = db.execute('SELECT * FROM history ORDER BY created_at DESC').fetchall()
        db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

@router.get('/history/{history_id}')
async def get_history_item(history_id: str):
    db = get_db()
    history_row = db.execute('SELECT * FROM history WHERE id=?', (history_id,)).fetchone()
    if not history_row:
        db.close()
        raise HTTPException(404, 'History not found')
        
    opt_id = history_row['optimization_id']
    opt_row = db.execute('SELECT result FROM optimizations WHERE id=?', (opt_id,)).fetchone()
    db.close()
    
    result = dict(history_row)
    if opt_row and opt_row['result']:
        result['optimization_result'] = json.loads(opt_row['result'])
        
    return result

@router.delete('/history/{history_id}')
async def delete_history(history_id: str):
    db = get_db()
    db.execute('DELETE FROM history WHERE id=?', (history_id,))
    db.commit()
    db.close()
    return {'success': True}

@router.get('/stats')
async def get_stats():
    try:
        db = get_db()
        datasets_count = db.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]
        opts_count = db.execute("SELECT COUNT(*) FROM optimizations WHERE status='completed'").fetchone()[0]
        history = db.execute('SELECT score, optimization_method FROM history').fetchall()
        db.close()
        best_score = max([float(r['score']) for r in history]) if history else 0.0
        models_tested = opts_count * 50
        return {
            'datasets_processed': datasets_count,
            'optimizations_completed': opts_count,
            'best_score': best_score,
            'models_tested': models_tested
        }
    except Exception:
        return {
            'datasets_processed': 0,
            'optimizations_completed': 0,
            'best_score': 0.0,
            'models_tested': 0
        }
