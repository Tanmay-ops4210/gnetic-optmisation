# AutoML Genetic Optimizer

> Automatically discover better machine-learning models using evolutionary optimization.

Upload a CSV → configure a target → watch a Genetic Algorithm evolve the best model → make predictions.

---

## Demo Flow

1. Open app → **Dashboard**
2. Click **Start New Optimization** → upload `data/student_performance.csv`
3. Click **Analyze Dataset** → select `FinalResult` as target → **Continue**
4. Select **Random Forest + Gradient Boosting**, method **Genetic + Random**, metric **Accuracy** → **Start Optimization**
5. Watch live generations on the **Optimization** page
6. View **Results**: baseline vs optimized accuracy, charts, confusion matrix
7. Click **Use Best Model** → enter feature values → **PREDICT**
8. Check **History** for saved runs

---

## Setup

### Requirements

- Python 3.9+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Windows shortcut:
```bash
cd backend
run.bat
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Project Structure

```
automl-genetic-optimizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── api/routes.py        # All REST endpoints
│   │   ├── database/db.py       # SQLite setup
│   │   ├── schemas/schemas.py   # Pydantic models
│   │   ├── ml/
│   │   │   ├── preprocessing.py # Imputation, encoding, scaling
│   │   │   ├── model_manager.py # Model registry + factory
│   │   │   └── evaluation.py    # Cross-validation + metrics
│   │   └── optimization/
│   │       ├── genetic_algorithm.py  # Custom GA implementation
│   │       └── search_optimizer.py   # Grid/Random Search
│   ├── uploads/       # Uploaded CSV files
│   ├── saved_models/  # Joblib model files
│   ├── automl.db      # SQLite database (auto-created)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/     # 8 pages (Dashboard, Dataset, Optimization, Results, Prediction, History, Docs)
│       ├── components/
│       ├── services/api.ts   # Axios API layer
│       ├── types/index.ts    # TypeScript types
│       └── hooks/usePolling.ts
├── data/
│   └── student_performance.csv   # Sample dataset
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/dataset/upload` | Upload CSV |
| POST | `/api/dataset/{id}/analyze` | Analyze columns/types |
| POST | `/api/dataset/{id}/config` | Set target + features |
| POST | `/api/optimization/start` | Start GA optimization |
| GET | `/api/optimization/{id}/status` | Poll live status |
| GET | `/api/optimization/{id}/results` | Get final results |
| POST | `/api/optimization/{id}/control` | Pause/Stop |
| POST | `/api/prediction` | Run prediction |
| GET | `/api/history` | List history |
| DELETE | `/api/history/{id}` | Delete history item |
| GET | `/api/stats` | Dashboard stats |

---

## Technologies

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React  
**Backend:** Python, FastAPI, Pandas, NumPy, Scikit-learn, Joblib  
**Optimization:** Custom Genetic Algorithm + Grid/Random Search (scikit-learn)  
**Storage:** SQLite (history), Joblib (models)

---

## Supported Models

**Classification:** Logistic Regression, Decision Tree, Random Forest, KNN, SVM, Gradient Boosting  
**Regression:** Ridge Regression, Decision Tree, Random Forest, Gradient Boosting

---

## License

MIT
