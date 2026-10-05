import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Info } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { optimizationApi } from '../services/api'
import type { DatasetInfo, OptimizationConfig } from '../types'

const CLASS_MODELS = ['LogisticRegression', 'DecisionTree', 'RandomForest', 'KNN', 'SVM', 'GradientBoosting']
const REG_MODELS = ['LinearRegression', 'DecisionTreeRegressor', 'RandomForestRegressor', 'GradientBoostingRegressor']

const CLASS_METRICS = ['accuracy', 'f1', 'precision', 'recall']
const REG_METRICS = ['r2', 'mae', 'mse', 'rmse']

export default function OptimizationConfigPage() {
  const navigate = useNavigate()
  const [dataset, setDataset] = useState<DatasetInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [problemType, setProblemType] = useState('classification')
  const [selectedModels, setSelectedModels] = useState<string[]>(['RandomForest', 'GradientBoosting'])
  const [optMethod, setOptMethod] = useState('genetic+random')
  const [metric, setMetric] = useState('accuracy')
  const [popSize, setPopSize] = useState(20)
  const [generations, setGenerations] = useState(25)
  const [mutationRate, setMutationRate] = useState(0.2)
  const [crossoverRate, setCrossoverRate] = useState(0.8)
  const [selectionMethod, setSelectionMethod] = useState('tournament')
  const [cvFolds, setCvFolds] = useState(5)
  const [testSize, setTestSize] = useState(0.2)

  useEffect(() => {
    const raw = localStorage.getItem('currentDataset')
    if (raw) {
      const ds: DatasetInfo = JSON.parse(raw)
      setDataset(ds)
      const pt = ds.problem_type || 'classification'
      setProblemType(pt)
      setSelectedModels(pt === 'regression' ? REG_MODELS.slice(0, 2) : ['RandomForest', 'GradientBoosting'])
      setMetric(pt === 'regression' ? 'r2' : 'accuracy')
    }
  }, [])

  const models = problemType === 'regression' ? REG_MODELS : CLASS_MODELS
  const metrics = problemType === 'regression' ? REG_METRICS : CLASS_METRICS

  const toggleModel = (m: string) =>
    setSelectedModels(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])

  const handleStart = async () => {
    if (!dataset) { setError('No dataset selected. Go to Dataset page first.'); return }
    if (!dataset.target_column) { setError('No target column selected.'); return }
    if (selectedModels.length === 0) { setError('Select at least one model.'); return }

    setLoading(true)
    setError(null)
    try {
      const config: OptimizationConfig = {
        dataset_id: dataset.id,
        target_column: dataset.target_column,
        features: dataset.features || [],
        problem_type: problemType,
        models: selectedModels,
        optimization_method: optMethod,
        metric,
        population_size: popSize,
        generations,
        mutation_rate: mutationRate,
        crossover_rate: crossoverRate,
        selection_method: selectionMethod,
        cv_folds: cvFolds,
        test_size: testSize,
        handle_missing: true,
        encode_categorical: true,
        standardize: true,
        remove_duplicates: true,
      }
      const { optimization_id } = await optimizationApi.start(config)
      localStorage.setItem('currentOptimization', optimization_id)
      navigate(`/optimization/run/${optimization_id}`)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Failed to start optimization')
    } finally {
      setLoading(false)
    }
  }

  if (!dataset) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-64 gap-4">
        <p className="text-slate-400">No dataset loaded.</p>
        <button className="btn-primary" onClick={() => navigate('/dataset')}>Go to Dataset →</button>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-6">
      <PageHeader title="Model Configuration" subtitle={`Dataset: ${dataset.original_name}`} />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="card space-y-4">
        <h2 className="font-semibold text-white">Problem Type</h2>
        <div className="grid grid-cols-3 gap-2">
          {['classification', 'regression'].map(pt => (
            <button
              key={pt}
              onClick={() => { setProblemType(pt); setSelectedModels(pt === 'regression' ? REG_MODELS.slice(0, 2) : ['RandomForest']); setMetric(pt === 'regression' ? 'r2' : 'accuracy') }}
              className={`py-2.5 px-4 rounded-lg border text-sm font-medium capitalize transition-colors ${
                problemType === pt ? 'bg-brand-600/20 border-brand-600 text-brand-300' : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
              }`}
            >{pt}</button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="font-semibold text-white">Model Selection</h2>
          <button className="text-xs text-brand-400" onClick={() => setSelectedModels(models)}>All</button>
          <button className="text-xs text-slate-500" onClick={() => setSelectedModels([])}>None</button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {models.map(m => (
            <label key={m} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedModels.includes(m) ? 'bg-brand-900/20 border-brand-700' : 'bg-slate-800 border-slate-700 hover:border-slate-600'
            }`}>
              <input type="checkbox" checked={selectedModels.includes(m)} onChange={() => toggleModel(m)} className="rounded border-slate-600 text-brand-600 focus:ring-brand-500" />
              <span className="text-sm font-medium text-slate-200">{m}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="card space-y-6">
        <h2 className="font-semibold text-white">Optimization Parameters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Optimization Method</label>
            <select className="input" value={optMethod} onChange={e => setOptMethod(e.target.value)}>
              <option value="genetic">Genetic Algorithm Only</option>
              <option value="random">Random Search Only</option>
              <option value="genetic+random">Genetic + Random (Recommended)</option>
            </select>
          </div>
          <div>
            <label className="label">Metric</label>
            <select className="input" value={metric} onChange={e => setMetric(e.target.value)}>
              {metrics.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Population Size: {popSize}</label>
            <input type="range" min="10" max="100" step="10" value={popSize} onChange={e => setPopSize(Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="label">Generations: {generations}</label>
            <input type="range" min="5" max="100" step="5" value={generations} onChange={e => setGenerations(Number(e.target.value))} className="w-full" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Mutation Rate: {mutationRate}</label>
            <input type="range" min="0.05" max="0.5" step="0.05" value={mutationRate} onChange={e => setMutationRate(Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="label">Crossover Rate: {crossoverRate}</label>
            <input type="range" min="0.5" max="1.0" step="0.05" value={crossoverRate} onChange={e => setCrossoverRate(Number(e.target.value))} className="w-full" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="label">Selection Method</label>
            <select className="input" value={selectionMethod} onChange={e => setSelectionMethod(e.target.value)}>
              <option value="tournament">Tournament</option>
              <option value="roulette">Roulette Wheel</option>
            </select>
          </div>
          <div>
            <label className="label">Cross-validation Folds: {cvFolds}</label>
            <input type="number" min="2" max="10" value={cvFolds} onChange={e => setCvFolds(Number(e.target.value))} className="input" />
          </div>
          <div>
            <label className="label">Test Size (split): {testSize}</label>
            <input type="number" min="0.1" max="0.5" step="0.05" value={testSize} onChange={e => setTestSize(Number(e.target.value))} className="input" />
          </div>
        </div>
      </div>

      <button className="btn-primary w-full md:w-auto" onClick={handleStart} disabled={loading}>
        {loading ? <Spinner size="sm" /> : 'Start Optimization →'}
      </button>
    </div>
  )
}
