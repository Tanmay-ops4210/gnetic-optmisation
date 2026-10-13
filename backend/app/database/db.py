import sqlite3
import os

def _get_db_path() -> str:
    if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        return '/tmp/automl.db'
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_file = os.path.join(base_dir, 'automl.db')
    try:
        test_file = os.path.join(base_dir, '.write_check')
        with open(test_file, 'w') as f:
            f.write('')
        os.remove(test_file)
        return db_file
    except OSError:
        return '/tmp/automl.db'

DB_PATH = _get_db_path()

_initialized = False

def init_db():
    global _initialized
    if _initialized and os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        filename TEXT,
        original_name TEXT,
        rows INTEGER,
        cols INTEGER,
        file_size INTEGER,
        target_column TEXT,
        features TEXT,
        problem_type TEXT,
        created_at TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS optimizations (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        status TEXT,
        config TEXT,
        result TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id TEXT PRIMARY KEY,
        optimization_id TEXT,
        dataset_name TEXT,
        model_name TEXT,
        problem_type TEXT,
        score REAL,
        optimization_method TEXT,
        duration REAL,
        created_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    _initialized = True

def get_db() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
