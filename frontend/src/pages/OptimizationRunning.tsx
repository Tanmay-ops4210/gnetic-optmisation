import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import PageHeader from '../components/PageHeader'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { optimizationApi } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import type { OptimizationStatus } from '../types'

export default function OptimizationRunning() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<OptimizationStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState(true)

  const fetchStatus = async () => {
    if (!id) return
    try {
      const res = await optimizationApi.getStatus(id)
      setStatus(res)
      if (res.status === 'completed' || res.status === 'failed') {
        setActive(false)
        if (res.status === 'completed') {
          setTimeout(() => navigate(`/results/${id}`), 2000)
        }
      }
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Failed to fetch status')
      setActive(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [id])

  usePolling(fetchStatus, 3000, active)

  if (error) {
    return (
      <div className="p-6">
        <Alert type="error" message={error} />
      </div>
    )
  }

  if (!status) {
    return (
      <div className="p-6 flex justify-center mt-20">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-6">
      <PageHeader title="Optimization Running" subtitle={`ID: ${id}`} />

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-white capitalize">{status.status}</h2>
            <p className="text-slate-400 mt-1">{status.stage}</p>
          </div>
          {status.status === 'running' && <Spinner size="md" />}
        </div>

        <div className="w-full bg-slate-800 rounded-full h-2.5 mb-4 overflow-hidden">
          <div
            className="bg-brand-600 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${status.progress_pct}%` }}
          />
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="p-4 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 uppercase">Generation</p>
            <p className="text-xl font-bold text-slate-200">{status.generation} / {status.total_generations}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 uppercase">Models Tested</p>
            <p className="text-xl font-bold text-slate-200">{status.models_tested}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 uppercase">Best Score</p>
            <p className="text-xl font-bold text-emerald-400">{status.best_score.toFixed(4)}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 uppercase">Best Model</p>
            <p className="text-sm font-bold text-brand-400 truncate mt-1">{status.best_model || '—'}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-white mb-4">Fitness History</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={status.fitness_history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="generation" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
                itemStyle={{ color: '#818cf8' }}
              />
              <Line type="monotone" dataKey="best" stroke="#4f46e5" strokeWidth={2} name="Best Score" />
              <Line type="monotone" dataKey="avg" stroke="#94a3b8" strokeWidth={2} name="Avg Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-white mb-2">Logs</h3>
        <div className="bg-slate-950 p-4 rounded-lg h-48 overflow-y-auto font-mono text-xs text-slate-400 space-y-1">
          {status.logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
          {status.logs.length === 0 && <div>Waiting for logs...</div>}
        </div>
      </div>
      
      {status.status === 'completed' && (
        <button className="btn-primary w-full" onClick={() => navigate(`/results/${id}`)}>
          View Full Results →
        </button>
      )}
    </div>
  )
}
