export const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export const formatScore = (score: number, metric: string): string => {
  if (['accuracy', 'f1', 'precision', 'recall', 'r2'].includes(metric)) {
    return `${(score * 100).toFixed(2)}%`
  }
  return score.toFixed(4)
}

export const formatDate = (iso: string): string => {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

export const truncate = (str: string, n: number): string =>
  str.length > n ? str.slice(0, n) + '…' : str
