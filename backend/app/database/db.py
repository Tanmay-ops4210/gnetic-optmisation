import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'automl.db')

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
