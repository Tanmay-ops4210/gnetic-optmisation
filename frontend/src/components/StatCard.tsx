interface Props {
  label: string
  value: string | number
  icon?: React.ReactNode
  sub?: string
  color?: string
}
export default function StatCard({ label, value, icon, sub, color = 'brand' }: Props) {
  const colorMap: Record<string, string> = {
    brand: 'text-brand-400',
    green: 'text-emerald-400',
    amber: 'text-amber-400',
    purple: 'text-purple-400',
  }
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${colorMap[color] ?? colorMap.brand}`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
        </div>
        {icon && (
          <div className={`p-2.5 rounded-lg bg-slate-800 ${colorMap[color] ?? ''}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
