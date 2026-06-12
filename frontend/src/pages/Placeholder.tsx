export default function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-xl font-semibold text-white mb-4">{title}</h1>
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-500 text-sm">
        Diese Seite wird in einem späteren Schritt umgesetzt.
      </div>
    </div>
  )
}
