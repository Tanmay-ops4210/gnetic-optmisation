from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.db import init_db
from .api.routes import router

app = FastAPI(title='AutoML Genetic Optimizer API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

init_db()

app.include_router(router, prefix='/api')

@app.get('/health')
def health():
    return {'status': 'ok'}
