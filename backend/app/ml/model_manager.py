from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from typing import Dict, Any, List
import numpy as np

CLASSIFICATION_MODELS = {
    'LogisticRegression': {
        'class': LogisticRegression,
        'params': {'max_iter': 1000, 'random_state': 42},
        'search_space': {
            'C': [0.01, 0.1, 1.0, 10.0],
            'solver': ['lbfgs', 'liblinear'],
        },
        'ga_space': {
            'C': (0.01, 100.0, 'float'),
        }
    },
    'DecisionTree': {
        'class': DecisionTreeClassifier,
        'params': {'random_state': 42},
        'search_space': {
            'max_depth': [3, 5, 7, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
        },
        'ga_space': {
            'max_depth': (2, 20, 'int'),
            'min_samples_split': (2, 20, 'int'),
            'min_samples_leaf': (1, 10, 'int'),
        }
    },
    'RandomForest': {
        'class': RandomForestClassifier,
        'params': {'random_state': 42, 'n_jobs': -1},
        'search_space': {
            'n_estimators': [50, 100, 150, 200],
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
        },
        'ga_space': {
            'n_estimators': (10, 300, 'int'),
            'max_depth': (3, 30, 'int'),
            'min_samples_split': (2, 20, 'int'),
            'min_samples_leaf': (1, 10, 'int'),
        }
    },
    'KNN': {
        'class': KNeighborsClassifier,
        'params': {'n_jobs': -1},
        'search_space': {
            'n_neighbors': [3, 5, 7, 9, 11, 15],
            'weights': ['uniform', 'distance'],
            'metric': ['euclidean', 'manhattan'],
        },
        'ga_space': {
            'n_neighbors': (1, 20, 'int'),
        }
    },
    'SVM': {
        'class': SVC,
        'params': {'probability': True, 'random_state': 42},
        'search_space': {
            'C': [0.1, 1.0, 10.0],
            'kernel': ['rbf', 'linear'],
            'gamma': ['scale', 'auto'],
        },
        'ga_space': {
            'C': (0.01, 50.0, 'float'),
        }
    },
    'GradientBoosting': {
        'class': GradientBoostingClassifier,
        'params': {'random_state': 42},
        'search_space': {
            'n_estimators': [50, 100, 150],
            'learning_rate': [0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7],
        },
        'ga_space': {
            'n_estimators': (20, 200, 'int'),
            'learning_rate': (0.01, 0.5, 'float'),
            'max_depth': (2, 10, 'int'),
        }
    },
}

REGRESSION_MODELS = {
    'LinearRegression': {
        'class': Ridge,
        'params': {},
        'search_space': {'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]},
        'ga_space': {'alpha': (0.001, 100.0, 'float')}
    },
    'DecisionTreeRegressor': {
        'class': DecisionTreeRegressor,
        'params': {'random_state': 42},
        'search_space': {
            'max_depth': [3, 5, 7, 10, 15, None],
            'min_samples_split': [2, 5, 10],
        },
        'ga_space': {
            'max_depth': (2, 20, 'int'),
            'min_samples_split': (2, 20, 'int'),
        }
    },
    'RandomForestRegressor': {
        'class': RandomForestRegressor,
        'params': {'random_state': 42, 'n_jobs': -1},
        'search_space': {
            'n_estimators': [50, 100, 150, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
        },
        'ga_space': {
            'n_estimators': (10, 200, 'int'),
            'max_depth': (3, 25, 'int'),
            'min_samples_split': (2, 20, 'int'),
        }
    },
    'GradientBoostingRegressor': {
        'class': GradientBoostingRegressor,
        'params': {'random_state': 42},
        'search_space': {
            'n_estimators': [50, 100, 150],
            'learning_rate': [0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7],
        },
        'ga_space': {
            'n_estimators': (20, 200, 'int'),
            'learning_rate': (0.01, 0.5, 'float'),
            'max_depth': (2, 8, 'int'),
        }
    },
}

def get_model_registry(problem_type: str) -> Dict:
    if problem_type == 'classification':
        return CLASSIFICATION_MODELS
    return REGRESSION_MODELS

def build_model(model_name: str, problem_type: str, params: Dict[str, Any]):
    registry = get_model_registry(problem_type)
    if model_name not in registry:
        raise ValueError(f'Unknown model: {model_name}')
    spec = registry[model_name]
    base_params = spec['params'].copy()
    base_params.update(params)
    # Handle None for max_depth etc
    return spec['class'](**base_params)
