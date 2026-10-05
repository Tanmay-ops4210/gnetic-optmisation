import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from typing import Tuple, List, Dict, Any, Optional

def load_and_clean_csv(file_or_path) -> pd.DataFrame:
    """
    Robust CSV loader that automatically:
    1. Handles bad lines or alternative encodings.
    2. Detects and skips metadata/title headers (e.g. multi-row banner headers).
    3. Strips completely empty rows and trailing empty unnamed columns.
    """
    try:
        df = pd.read_csv(file_or_path)
    except Exception:
        try:
            df = pd.read_csv(file_or_path, encoding='latin1', on_bad_lines='skip')
        except Exception:
            df = pd.read_csv(file_or_path, engine='python', on_bad_lines='skip')

    # Detect if top rows contain title banners or blank rows before actual headers
    if len(df) > 1:
        unnamed_ratio = df.columns.str.startswith('Unnamed').mean()
        first_row_na_ratio = df.iloc[0].isna().mean()
        if unnamed_ratio > 0.4 or first_row_na_ratio > 0.5:
            best_row = None
            max_valid = 0
            for i in range(min(12, len(df))):
                row_vals = df.iloc[i].dropna()
                valid_headers = sum(
                    1 for v in row_vals
                    if isinstance(v, str) and not v.strip().replace('.', '').replace('-', '').isdigit()
                )
                if valid_headers > max_valid and valid_headers >= 2:
                    max_valid = valid_headers
                    best_row = i
            if best_row is not None:
                raw_headers = df.iloc[best_row].values
                df = df.iloc[best_row + 1:].copy()
                clean_headers = []
                seen = set()
                for idx, h in enumerate(raw_headers):
                    h_str = str(h).strip() if pd.notna(h) and str(h).strip() else f'Col_{idx+1}'
                    if h_str in seen:
                        h_str = f"{h_str}_{idx+1}"
                    seen.add(h_str)
                    clean_headers.append(h_str)
                df.columns = clean_headers

    # Drop completely empty rows
    df = df.dropna(how='all')

    # Drop completely empty columns
    df = df.dropna(axis=1, how='all')

    # Drop columns that have no name or are blank dummy unnamed columns with mostly NaNs
    cols_to_keep = []
    for c in df.columns:
        c_str = str(c).strip()
        if not c_str or c_str.lower() == 'nan':
            continue
        if ('Unnamed' in c_str or 'Col_' in c_str) and (df[c].isna().mean() > 0.85 or df[c].nunique() == 0):
            continue
        cols_to_keep.append(c)

    if cols_to_keep:
        df = df[cols_to_keep]

    df = df.reset_index(drop=True)
    return df


class Preprocessor:
    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler: Optional[StandardScaler] = None
        self.imputers: Dict[str, SimpleImputer] = {}
        self.feature_names: List[str] = []
        self.target_encoder: Optional[LabelEncoder] = None
        self.is_fitted: bool = False
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.target_col: Optional[str] = None
        self.problem_type: Optional[str] = None

    def fit_transform(self, df: pd.DataFrame, target_col: str, features: List[str],
                      handle_missing=True, encode_categorical=True,
                      standardize=True, remove_duplicates=True,
                      problem_type='classification') -> Tuple[np.ndarray, np.ndarray]:
        # Validate target column exists
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset columns: {list(df.columns)}")

        # Drop rows where target is missing
        valid_target = df[target_col].notna() & (df[target_col].astype(str).str.strip() != '') & (df[target_col].astype(str).str.lower() != 'nan')
        df = df[valid_target].copy()
        if len(df) < 5:
            raise ValueError(f"Target column '{target_col}' has fewer than 5 valid rows after removing missing values.")

        # Remove duplicate rows
        if remove_duplicates:
            df = df.drop_duplicates()

        self.target_col = target_col
        self.problem_type = problem_type

        # Filter features to those that actually exist in df and are not target
        valid_features = [f for f in features if f in df.columns and f != target_col]
        if not valid_features:
            valid_features = [c for c in df.columns if c != target_col]
        
        # Remove features that are 100% NaN
        usable_features = [f for f in valid_features if df[f].notna().sum() > 0]
        if not usable_features:
            raise ValueError("All selected features contain only missing values.")
        
        self.feature_names = usable_features
        X = df[self.feature_names].copy()
        y_raw = df[target_col].copy()

        # Identify numeric vs categorical
        self.numeric_cols = []
        self.categorical_cols = []
        for col in self.feature_names:
            # Check if column is numeric or can be converted to numeric
            coerced = pd.to_numeric(X[col], errors='coerce')
            if coerced.notna().sum() > len(X) * 0.5:
                X[col] = coerced
                self.numeric_cols.append(col)
            else:
                self.categorical_cols.append(col)

        # Handle missing values
        if handle_missing:
            if self.numeric_cols:
                for col in self.numeric_cols:
                    if X[col].isna().all():
                        X[col] = 0.0
                num_imputer = SimpleImputer(strategy='median')
                X[self.numeric_cols] = num_imputer.fit_transform(X[self.numeric_cols])
                self.imputers['numeric'] = num_imputer

            if self.categorical_cols:
                for col in self.categorical_cols:
                    X[col] = X[col].fillna('missing').astype(str)
                cat_imputer = SimpleImputer(strategy='most_frequent')
                X[self.categorical_cols] = cat_imputer.fit_transform(X[self.categorical_cols])
                self.imputers['categorical'] = cat_imputer

        # Encode categorical variables
        if encode_categorical and self.categorical_cols:
            for col in self.categorical_cols:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le

        # Standardize numerical features
        if standardize and self.numeric_cols:
            self.scaler = StandardScaler()
            X[self.numeric_cols] = self.scaler.fit_transform(X[self.numeric_cols])

        # Encode target
        if problem_type == 'classification':
            self.target_encoder = LabelEncoder()
            y = self.target_encoder.fit_transform(y_raw.astype(str))
            if len(self.target_encoder.classes_) < 2:
                raise ValueError(f"Classification requires at least 2 distinct classes in target '{target_col}', found: {list(self.target_encoder.classes_)}")
        else:
            y_num = pd.to_numeric(y_raw, errors='coerce').fillna(0.0)
            y = y_num.values.astype(np.float64)

        self.is_fitted = True
        return X.astype(np.float64).values, y

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = pd.DataFrame(index=df.index)
        for col in self.feature_names:
            if col in df.columns:
                X[col] = df[col]
            else:
                X[col] = np.nan

        # Convert numeric
        for col in self.numeric_cols:
            X[col] = pd.to_numeric(X[col], errors='coerce')

        if 'numeric' in self.imputers and self.numeric_cols:
            for col in self.numeric_cols:
                if X[col].isna().all():
                    X[col] = 0.0
            X[self.numeric_cols] = self.imputers['numeric'].transform(X[self.numeric_cols])

        if 'categorical' in self.imputers and self.categorical_cols:
            for col in self.categorical_cols:
                X[col] = X[col].fillna('missing').astype(str)
            X[self.categorical_cols] = self.imputers['categorical'].transform(X[self.categorical_cols])

        for col, le in self.label_encoders.items():
            known = set(le.classes_)
            X[col] = X[col].astype(str).map(
                lambda v: le.transform([v])[0] if v in known else 0
            )

        if self.scaler and self.numeric_cols:
            X[self.numeric_cols] = self.scaler.transform(X[self.numeric_cols])

        return X.astype(np.float64).values

    def transform_single(self, features: Dict[str, Any]) -> np.ndarray:
        df = pd.DataFrame([features])
        return self.transform(df)

    def get_class_labels(self) -> Optional[List[str]]:
        if self.target_encoder:
            return [str(c) for c in self.target_encoder.classes_]
        return None


def detect_problem_type(df: pd.DataFrame, target_col: str) -> str:
    if target_col not in df.columns:
        return 'classification'
    col = df[target_col].dropna()
    if len(col) == 0:
        return 'classification'
    if col.dtype in ['object', 'bool', 'category']:
        return 'classification'
    unique_count = col.nunique()
    unique_ratio = unique_count / max(len(col), 1)
    if unique_count <= 20 or unique_ratio < 0.05:
        return 'classification'
    return 'regression'
