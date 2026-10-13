from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.db import init_db
from .api.routes import router

app = FastAPI(title='AutoML Genetic Optimizer API', version='1.0.0')

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://gnetic-optmisation.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

init_db()

app.include_router(router, prefix='/api')

@app.get('/health')
@app.get('/api/health')
def health():
    return {'status': 'ok'}
