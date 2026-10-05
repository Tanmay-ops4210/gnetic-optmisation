import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { predictionApi, optimizationApi } from '../services/api'
import type { DatasetInfo, OptimizationResult, PredictionResponse } from '../types'

export default function Prediction() {
  const { id: paramId } = useParams<{ id: string }>()
  const [optId, setOptId] = useState(paramId || localStorage.getItem('currentOptimization') || '')
  const [dataset, setDataset] = useState<DatasetInfo | null>(null)
  const [features, setFeatures] = useState<Record<string, string>>({})
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem('currentDataset')
    if (raw) {
      const ds: DatasetInfo = JSON.parse(raw)
      setDataset(ds)
      const initial: Record<string, string> = {}
      ds.features?.forEach(f => { initial[f] = '' })
      setFeatures(initial)
    }
  }, [])

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!optId) {
      setError('Please provide an Optimization ID')
      return
    }
    setLoading(true)
    setError(null)
    setPrediction(null)

    // Convert numeric inputs
    const parsedFeatures: Record<string, unknown> = {}
    Object.entries(features).forEach(([k, v]) => {
      parsedFeatures[k] = isNaN(Number(v)) || v.trim() === '' ? v : Number(v)
    })

    try {
      const res = await predictionApi.predict(optId, parsedFeatures)
      setPrediction(res)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-6">
      <PageHeader title="Make Predictions" subtitle="Use your optimized model to predict new data" />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card space-y-6">
          <h2 className="font-semibold text-white">Input Features</h2>
          
          <div className="space-y-4">
            <div>
              <label className="label">Optimization ID</label>
              <input
                type="text"
                className="input"
                value={optId}
                onChange={(e) => setOptId(e.target.value)}
                placeholder="Enter Model / Optimization ID"
              />
            </div>

            <hr className="border-slate-800" />

            <form onSubmit={handlePredict} className="space-y-4">
              {dataset?.features ? dataset.features.map(f => (
                <div key={f}>
                  <label className="label">{f}</label>
                  <input
                    type="text"
                    className="input"
                    value={features[f] || ''}
                    onChange={(e) => setFeatures({ ...features, [f]: e.target.value })}
                    required
                  />
                </div>
              )) : (
                <Alert type="info" message="No dataset context loaded. Please run an optimization first to auto-fill feature fields." />
              )}
              
              <button type="submit" className="btn-primary w-full" disabled={loading || !dataset?.features}>
                {loading ? <Spinner size="sm" /> : 'Predict'}
              </button>
            </form>
          </div>
        </div>

        <div>
          {prediction && (
            <div className="card bg-brand-900/10 border-brand-800">
              <h2 className="font-semibold text-white mb-4">Prediction Result</h2>
              
              <div className="mb-6">
                <p className="text-sm text-slate-400 mb-1">Predicted Value / Class</p>
                <p className="text-4xl font-bold text-emerald-400">{String(prediction.prediction)}</p>
              </div>

              {prediction.confidence !== undefined && (
                <div className="mb-4">
                  <p className="text-sm text-slate-400 mb-1">Confidence</p>
                  <p className="text-lg font-medium text-slate-200">{(prediction.confidence * 100).toFixed(2)}%</p>
                </div>
              )}

              {prediction.class_probabilities && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">Class Probabilities</p>
                  <div className="space-y-2">
                    {Object.entries(prediction.class_probabilities).map(([cls, prob]) => (
                      <div key={cls}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-300">{cls}</span>
                          <span className="text-slate-400">{(prob * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1.5">
                          <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${prob * 100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
