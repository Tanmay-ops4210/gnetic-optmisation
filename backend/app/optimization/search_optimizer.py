from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from typing import Dict, Any, List, Optional, Callable
import numpy as np

def run_grid_search(
    model,
    X, y,
    param_grid: Dict[str, List],
    cv: int = 5,
    scoring: str = 'accuracy',
    callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    gs = GridSearchCV(
        model, param_grid, cv=cv, scoring=scoring,
        n_jobs=-1, refit=True, return_train_score=False
    )
    gs.fit(X, y)
    return {
        'best_params': gs.best_params_,
        'best_score': float(gs.best_score_),
        'best_estimator': gs.best_estimator_,
        'results': [
            {
                'params': dict(gs.cv_results_['params'][i]),
                'mean_score': float(gs.cv_results_['mean_test_score'][i]),
            }
            for i in range(len(gs.cv_results_['params']))
        ]
    }

def run_random_search(
    model,
    X, y,
    param_distributions: Dict[str, Any],
    n_iter: int = 30,
    cv: int = 5,
    scoring: str = 'accuracy',
    callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    rs = RandomizedSearchCV(
        model, param_distributions, n_iter=n_iter,
        cv=cv, scoring=scoring, n_jobs=-1,
        refit=True, random_state=42, return_train_score=False
    )
    rs.fit(X, y)
    return {
        'best_params': rs.best_params_,
        'best_score': float(rs.best_score_),
        'best_estimator': rs.best_estimator_,
        'results': [
            {
                'params': dict(rs.cv_results_['params'][i]),
                'mean_score': float(rs.cv_results_['mean_test_score'][i]),
            }
            for i in range(len(rs.cv_results_['params']))
        ]
    }
