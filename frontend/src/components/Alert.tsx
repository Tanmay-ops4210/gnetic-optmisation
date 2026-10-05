interface Props {
  type: 'error' | 'success' | 'info' | 'warning'
  message: string
  onClose?: () => void
}
export default function Alert({ type, message, onClose }: Props) {
  const styles = {
    error: 'bg-red-900/40 border-red-700 text-red-300',
    success: 'bg-emerald-900/40 border-emerald-700 text-emerald-300',
    info: 'bg-brand-900/40 border-brand-700 text-brand-300',
    warning: 'bg-amber-900/40 border-amber-700 text-amber-300',
  }[type]
  return (
    <div className={`border rounded-lg px-4 py-3 text-sm flex items-start gap-2 ${styles}`}>
      <span className="flex-1">{message}</span>
      {onClose && (
        <button onClick={onClose} className="opacity-70 hover:opacity-100 ml-2 flex-shrink-0">✕</button>
      )}
    </div>
  )
}
