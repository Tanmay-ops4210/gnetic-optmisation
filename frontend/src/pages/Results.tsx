import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts'
import { Trophy, Clock, Cpu, ArrowRight } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { optimizationApi } from '../services/api'
import type { OptimizationResult } from '../types'
import { formatScore } from '../utils/format'

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<OptimizationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    optimizationApi.getResults(id)
      .then(setResult)
      .catch(e => setError(e.response?.data?.detail ?? 'Failed to load results'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="p-6 flex justify-center mt-20"><Spinner size="lg" /></div>
  if (error) return <div className="p-6"><Alert type="error" message={error} /></div>
  if (!result) return <div className="p-6"><Alert type="warning" message="No results found." /></div>

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-6">
      <PageHeader title="Optimization Results" subtitle={`Result ID: ${id}`}>
        <button className="btn-primary flex items-center gap-2" onClick={() => navigate(`/prediction/${id}`)}>
          Use Model for Prediction <ArrowRight className="w-4 h-4" />
        </button>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <StatCard label="Best Score" value={formatScore(result.best_score, result.metric)} sub={`Metric: ${result.metric}`} icon={<Trophy className="w-5 h-5" />} color="amber" />
          <StatCard label="Models Tested" value={result.models_tested} sub={`Over ${result.total_generations} generations`} icon={<Cpu className="w-5 h-5" />} color="purple" />
          <StatCard label="Duration" value={`${result.duration.toFixed(1)}s`} icon={<Clock className="w-5 h-5" />} color="brand" />
          
          <div className="card">
            <h3 className="font-semibold text-white mb-2">Improvement</h3>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-emerald-400">+{result.improvement.toFixed(2)}%</span>
            </div>
            <p className="text-sm text-slate-400 mt-1">over baseline ({formatScore(result.baseline_score, result.metric)})</p>
          </div>
        </div>

        <div className="lg:col-span-3 space-y-6">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Best Model: {result.best_model}</h3>
            <div className="bg-slate-950 p-4 rounded-lg overflow-x-auto">
              <pre className="text-sm text-brand-300">
                {JSON.stringify(result.best_params, null, 2)}
              </pre>
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-white mb-4">Model Comparison</h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={result.model_comparison}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="model" stroke="#94a3b8" tick={{ fontSize: 12 }} interval={0} angle={-30} textAnchor="end" height={60} />
                  <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                  <RechartsTooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
                    itemStyle={{ color: '#4f46e5' }}
                  />
                  <Bar dataKey="score" fill="#4f46e5" radius={[4, 4, 0, 0]} name="Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
