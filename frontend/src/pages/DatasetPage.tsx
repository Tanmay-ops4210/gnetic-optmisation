import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, AlertCircle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { datasetApi } from '../services/api'
import type { DatasetInfo, DatasetAnalysis } from '../types'
import { formatBytes } from '../utils/format'

export default function DatasetPage() {
  const navigate = useNavigate()
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [dataset, setDataset] = useState<DatasetInfo | null>(null)
  const [analysis, setAnalysis] = useState<DatasetAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [targetCol, setTargetCol] = useState('')
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])
  const [problemType, setProblemType] = useState('auto')
  const [preprocessing, setPreprocessing] = useState({
    handle_missing: true,
    encode_categorical: true,
    standardize: true,
    remove_duplicates: true,
  })
  const [showPreview, setShowPreview] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (f: File) => {
    if (!f.name.endsWith('.csv')) {
      setError('Only CSV files are accepted.')
      return
    }
    if (f.size > 50 * 1024 * 1024) {
      setError('File too large. Max 50MB.')
      return
    }
    setError(null)
    setFile(f)
    setDataset(null)
    setAnalysis(null)
    setLoading(true)
    try {
      const info = await datasetApi.upload(f)
      setDataset(info)
      localStorage.setItem('currentDataset', JSON.stringify(info))
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Upload failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleAnalyze = async () => {
    if (!dataset) return
    setAnalyzing(true)
    setError(null)
    try {
      const a = await datasetApi.analyze(dataset.id)
      setAnalysis(a)
      const cols = a.columns.map(c => c.name)
      const smartTarget = cols.find(c => ['sentiment', 'target', 'result', 'finalresult', 'label', 'class', 'outcome'].includes(c.toLowerCase())) || cols[cols.length - 1]
      const chosenTarget = targetCol && cols.includes(targetCol) ? targetCol : smartTarget
      setTargetCol(chosenTarget)
      setSelectedFeatures(cols.filter(c => c !== chosenTarget))
      setShowPreview(true)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleContinue = async () => {
    if (!dataset || !targetCol || selectedFeatures.length === 0) {
      setError('Please select a target column and at least one feature.')
      return
    }
    try {
      const updated = await datasetApi.updateConfig(dataset.id, {
        target_column: targetCol,
        features: selectedFeatures,
        problem_type: problemType === 'auto' ? undefined : problemType,
        ...preprocessing,
      })
      localStorage.setItem('currentDataset', JSON.stringify(updated))
      navigate('/optimization')
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Failed to save configuration')
    }
  }

  const featureCols = analysis?.columns.filter(c => c.name !== targetCol).map(c => c.name) ?? []

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <PageHeader title="Dataset" subtitle="Upload and configure your CSV dataset" />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

      {!dataset && (
        <div
          className={`border-2 border-dashed rounded-xl p-10 md:p-16 text-center cursor-pointer transition-colors ${
            dragging ? 'border-brand-500 bg-brand-900/10' : 'border-slate-700 hover:border-slate-600'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }} />
          {loading ? (
            <div className="flex flex-col items-center gap-3">
              <Spinner size="lg" />
              <p className="text-slate-400">Uploading…</p>
            </div>
          ) : (
            <>
              <Upload className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-lg font-semibold text-slate-300">Drop your CSV dataset here</p>
              <p className="text-sm text-slate-500 mt-1">or click to browse · Max 50MB</p>
              <button className="btn-primary mt-4" onClick={(e) => { e.stopPropagation(); fileRef.current?.click() }}>Browse CSV</button>
            </>
          )}
        </div>
      )}

      {dataset && (
        <div className="card">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-brand-600/20">
              <FileText className="w-6 h-6 text-brand-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-white truncate">{dataset.original_name}</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-3">
                <div><p className="text-xs text-slate-500">Size</p><p className="text-sm font-medium text-slate-200">{formatBytes(dataset.file_size)}</p></div>
                <div><p className="text-xs text-slate-500">Rows</p><p className="text-sm font-medium text-slate-200">{dataset.rows.toLocaleString()}</p></div>
                <div><p className="text-xs text-slate-500">Columns</p><p className="text-sm font-medium text-slate-200">{dataset.cols}</p></div>
                {analysis && <div><p className="text-xs text-slate-500">Missing</p><p className="text-sm font-medium text-slate-200">{analysis.missing_total}</p></div>}
              </div>
            </div>
            <button className="btn-secondary text-sm" onClick={() => { setDataset(null); setAnalysis(null); setFile(null) }}>Change</button>
          </div>

          {!analysis && (
            <button className="btn-primary mt-4 w-full sm:w-auto flex items-center justify-center gap-2" onClick={handleAnalyze} disabled={analyzing}>
              {analyzing ? <><Spinner size="sm" /> Analyzing…</> : 'Analyze Dataset'}
            </button>
          )}
        </div>
      )}

      {analysis && (
        <>
          <div className="card">
            <h2 className="font-semibold text-white mb-4">Column Information</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[500px]">
                <thead>
                  <tr className="border-b border-slate-800">
                    {['Column', 'Type', 'Missing', 'Unique', 'Sample Values'].map(h => (
                      <th key={h} className="text-left py-2 text-slate-500 font-medium pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {analysis.columns.map(col => (
                    <tr key={col.name} className="border-b border-slate-800/50">
                      <td className="py-2 text-slate-200 font-medium pr-4">{col.name}</td>
                      <td className="py-2 pr-4"><span className="badge-blue">{col.dtype}</span></td>
                      <td className="py-2 pr-4">
                        <span className={col.missing > 0 ? 'text-amber-400' : 'text-slate-500'}>{col.missing}</span>
                      </td>
                      <td className="py-2 text-slate-400 pr-4">{col.unique}</td>
                      <td className="py-2 text-slate-500 text-xs">{col.sample_values.slice(0, 3).join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card space-y-4">
            <h2 className="font-semibold text-white">Configuration</h2>

            <div>
              <label className="label">Target Column</label>
              <select className="input" value={targetCol} onChange={e => {
                setTargetCol(e.target.value)
                setSelectedFeatures(analysis.columns.filter(c => c.name !== e.target.value).map(c => c.name))
              }}>
                <option value="">Select target column…</option>
                {analysis.columns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
              </select>
            </div>

            <div>
              <label className="label">Problem Type</label>
              <select className="input" value={problemType} onChange={e => setProblemType(e.target.value)}>
                <option value="auto">Auto Detect</option>
                <option value="classification">Classification</option>
                <option value="regression">Regression</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label mb-0">Features ({selectedFeatures.length} selected)</label>
                <div className="flex gap-2">
                  <button className="text-xs text-brand-400 hover:text-brand-300" onClick={() => setSelectedFeatures(featureCols)}>All</button>
                  <button className="text-xs text-slate-500 hover:text-slate-300" onClick={() => setSelectedFeatures([])}>None</button>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-3 bg-slate-800 rounded-lg">
                {featureCols.map(col => (
                  <label key={col} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedFeatures.includes(col)}
                      onChange={e => setSelectedFeatures(prev =>
                        e.target.checked ? [...prev, col] : prev.filter(f => f !== col)
                      )}
                      className="rounded border-slate-600 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-sm text-slate-300 truncate">{col}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Preprocessing</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {(Object.keys(preprocessing) as (keyof typeof preprocessing)[]).map(key => (
                  <label key={key} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preprocessing[key]}
                      onChange={e => setPreprocessing(p => ({ ...p, [key]: e.target.checked }))}
                      className="rounded border-slate-600 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-xs text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <button
              className="flex items-center gap-2 text-sm font-medium text-slate-300 hover:text-white w-full"
              onClick={() => setShowPreview(v => !v)}
            >
              {showPreview ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              Dataset Preview (first 10 rows)
            </button>
            {showPreview && (
              <div className="overflow-x-auto mt-4">
                <table className="text-xs min-w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      {analysis.columns.map(c => (
                        <th key={c.name} className="text-left py-1.5 px-3 text-slate-400 whitespace-nowrap font-medium">{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.preview.map((row, i) => (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                        {analysis.columns.map(c => (
                          <td key={c.name} className="py-1.5 px-3 text-slate-300 whitespace-nowrap">
                            {String(row[c.name] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <button className="btn-primary w-full sm:w-auto" onClick={handleContinue}>
            Continue to Optimization →
          </button>
        </>
      )}
    </div>
  )
}
