import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Database, Trophy, Cpu, ArrowRight, Plus } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Spinner from '../components/Spinner'
import { statsApi, historyApi } from '../services/api'
import type { Stats, HistoryItem } from '../types'
import { formatScore, formatDate } from '../utils/format'

const WORKFLOW = [
  'CSV Dataset', 'Preprocessing', 'Model Selection',
  'Genetic Algorithm', 'Search Optimization', 'Best Model', 'Prediction'
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([statsApi.get(), historyApi.list()])
      .then(([s, h]) => { setStats(s); setHistory(h.slice(0, 5)) })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      <div className="card bg-gradient-to-br from-brand-900/40 to-slate-900 border-brand-800/50">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              AutoML Genetic Optimizer
            </h1>
            <p className="text-slate-400 mt-2 max-w-xl">
              Automatically discover better machine-learning models using evolutionary optimization.
              Upload a CSV, configure your target, and let the genetic algorithm find the best model.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0">
            <button className="btn-primary flex items-center gap-2" onClick={() => navigate('/dataset')}>
              <Plus className="w-4 h-4" /> Start New Optimization
            </button>
            <button className="btn-secondary" onClick={() => navigate('/history')}>View History</button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card animate-pulse h-20 bg-slate-800" />
          ))
        ) : (
          <>
            <StatCard label="Datasets Processed" value={stats?.datasets_processed ?? 0} icon={<Database className="w-4 h-4" />} color="brand" />
            <StatCard label="Optimizations" value={stats?.optimizations_completed ?? 0} icon={<Zap className="w-4 h-4" />} color="green" />
            <StatCard label="Best Score" value={stats?.best_score ? `${(stats.best_score * 100).toFixed(1)}%` : '—'} icon={<Trophy className="w-4 h-4" />} color="amber" />
            <StatCard label="Models Tested" value={stats?.models_tested ?? 0} icon={<Cpu className="w-4 h-4" />} color="purple" />
          </>
        )}
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Pipeline Workflow</h2>
        <div className="flex flex-wrap items-center gap-2 justify-center">
          {WORKFLOW.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm font-medium text-slate-300 whitespace-nowrap">
                {step}
              </div>
              {i < WORKFLOW.length - 1 && <ArrowRight className="w-4 h-4 text-brand-500 flex-shrink-0" />}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center mb-3">
            <Database className="w-4 h-4 text-brand-400" />
          </div>
          <h3 className="font-semibold text-white mb-1">1. Upload Dataset</h3>
          <p className="text-sm text-slate-400">Upload any CSV file. The system auto-detects column types, missing values, and suggests the problem type.</p>
        </div>
        <div className="card">
          <div className="w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center mb-3">
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="font-semibold text-white mb-1">2. Evolve Models</h3>
          <p className="text-sm text-slate-400">A Genetic Algorithm evolves hyperparameter combinations across generations to find the optimal configuration.</p>
        </div>
        <div className="card">
          <div className="w-8 h-8 rounded-lg bg-amber-600/20 flex items-center justify-center mb-3">
            <Trophy className="w-4 h-4 text-amber-400" />
          </div>
          <h3 className="font-semibold text-white mb-1">3. Get Best Model</h3>
          <p className="text-sm text-slate-400">Compare baseline vs optimized, view metrics and charts, then use the model for instant predictions.</p>
        </div>
      </div>

      {history.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">Recent Optimizations</h2>
            <button className="text-sm text-brand-400 hover:text-brand-300" onClick={() => navigate('/history')}>View all →</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left py-2 text-slate-500 font-medium">Dataset</th>
                  <th className="text-left py-2 text-slate-500 font-medium">Model</th>
                  <th className="text-left py-2 text-slate-500 font-medium">Score</th>
                  <th className="text-left py-2 text-slate-500 font-medium hidden sm:table-cell">Method</th>
                  <th className="text-left py-2 text-slate-500 font-medium hidden md:table-cell">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map(h => (
                  <tr key={h.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer" onClick={() => navigate(`/results/${h.optimization_id}`)}>
                    <td className="py-2.5 text-slate-300">{h.dataset_name}</td>
                    <td className="py-2.5 text-slate-300">{h.model_name}</td>
                    <td className="py-2.5 text-emerald-400 font-semibold">{(h.score * 100).toFixed(2)}%</td>
                    <td className="py-2.5 text-slate-400 hidden sm:table-cell">{h.optimization_method}</td>
                    <td className="py-2.5 text-slate-500 hidden md:table-cell">{formatDate(h.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
