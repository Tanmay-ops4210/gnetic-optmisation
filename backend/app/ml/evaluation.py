import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
    confusion_matrix
)
from sklearn.model_selection import cross_val_score, train_test_split
from typing import Dict, Any, Tuple, List, Optional
import time

def get_cv_scorer(metric: str) -> str:
    mapping = {
        'accuracy': 'accuracy',
        'f1': 'f1_weighted',
        'precision': 'precision_weighted',
        'recall': 'recall_weighted',
        'r2': 'r2',
        'mae': 'neg_mean_absolute_error',
        'mse': 'neg_mean_squared_error',
        'rmse': 'neg_root_mean_squared_error',
    }
    return mapping.get(metric, 'accuracy')

def evaluate_model(model, X, y, metric: str, cv_folds: int = 5) -> float:
    scorer = get_cv_scorer(metric)
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring=scorer, n_jobs=-1)
    score = float(np.mean(scores))
    if metric in ('mae', 'mse', 'rmse'):
        score = abs(score)
    return round(score, 6)

def evaluate_on_test(
    model, X_train, X_test, y_train, y_test, metric: str, problem_type: str
) -> Dict[str, Any]:
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    result = {}
    if problem_type == 'classification':
        result['accuracy'] = round(accuracy_score(y_test, y_pred), 6)
        result['f1'] = round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 6)
        result['precision'] = round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 6)
        result['recall'] = round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 6)
        cm = confusion_matrix(y_test, y_pred)
        result['confusion_matrix'] = cm.tolist()
        # Actual vs predicted (first 50)
        result['actual_vs_predicted'] = [
            {'actual': float(a), 'predicted': float(p)}
            for a, p in zip(y_test[:50], y_pred[:50])
        ]
    else:
        result['mae'] = round(mean_absolute_error(y_test, y_pred), 6)
        result['mse'] = round(mean_squared_error(y_test, y_pred), 6)
        result['rmse'] = round(np.sqrt(mean_squared_error(y_test, y_pred)), 6)
        result['r2'] = round(r2_score(y_test, y_pred), 6)
        result['actual_vs_predicted'] = [
            {'actual': float(a), 'predicted': float(p)}
            for a, p in zip(y_test[:50], y_pred[:50])
        ]
    
    result['primary_metric'] = metric
    result['primary_score'] = result.get(metric, result.get('accuracy', result.get('r2', 0)))
    return result

def get_feature_importance(model, feature_names: List[str]) -> Optional[Dict[str, float]]:
    if hasattr(model, 'feature_importances_'):
        fi = dict(zip(feature_names, model.feature_importances_.tolist()))
        return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
    if hasattr(model, 'coef_'):
        coef = model.coef_
        if coef.ndim > 1:
            coef = np.abs(coef).mean(axis=0)
        fi = dict(zip(feature_names, np.abs(coef).tolist()))
        return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
    return None
