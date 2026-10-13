import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trash2, BarChart2, Download, FileText } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { historyApi, optimizationApi } from '../services/api'
import type { HistoryItem } from '../types'
import { formatDate } from '../utils/format'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = () => {
    setLoading(true)
    historyApi.list()
      .then(setHistory)
      .catch(e => setError(e.response?.data?.detail ?? 'Failed to load history'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this optimization history?')) return
    try {
      await historyApi.delete(id)
      setHistory(history.filter(h => h.id !== id))
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Delete failed')
    }
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto space-y-6">
      <PageHeader title="Optimization History" subtitle="View past model training sessions" />
      
      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-10 flex justify-center"><Spinner /></div>
        ) : history.length === 0 ? (
          <div className="p-10 text-center text-slate-500">No history found. Start an optimization first.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-400">
                  <th className="py-3 px-4 text-left font-medium">Dataset</th>
                  <th className="py-3 px-4 text-left font-medium">Problem Type</th>
                  <th className="py-3 px-4 text-left font-medium">Best Model</th>
                  <th className="py-3 px-4 text-left font-medium">Score</th>
                  <th className="py-3 px-4 text-left font-medium">Date</th>
                  <th className="py-3 px-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {history.map(item => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors cursor-pointer group" onClick={() => navigate(`/results/${item.optimization_id}`)}>
                    <td className="py-3 px-4 text-slate-200">{item.dataset_name}</td>
                    <td className="py-3 px-4 text-slate-400 capitalize">{item.problem_type}</td>
                    <td className="py-3 px-4 text-brand-300 font-medium">{item.model_name}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">{(item.score * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4 text-slate-500">{formatDate(item.created_at)}</td>
                    <td className="py-3 px-4 flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <a
                        href={optimizationApi.getModelDownloadUrl(item.optimization_id)}
                        download
                        className="p-1.5 text-brand-400 hover:bg-brand-900/50 rounded transition-colors"
                        title="Download Model (.joblib)"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      <a
                        href={optimizationApi.getReportDownloadUrl(item.optimization_id)}
                        download
                        className="p-1.5 text-emerald-400 hover:bg-emerald-900/50 rounded transition-colors"
                        title="Download PDF Report"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <FileText className="w-4 h-4" />
                      </a>
                      <button className="p-1.5 text-brand-400 hover:bg-brand-900/50 rounded" title="View Results" onClick={(e) => { e.stopPropagation(); navigate(`/results/${item.optimization_id}`) }}>
                        <BarChart2 className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 text-red-400 hover:bg-red-900/50 rounded" title="Delete" onClick={(e) => handleDelete(e, item.id)}>
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
