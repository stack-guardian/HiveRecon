import { Shield, LayoutDashboard, Search, AlertTriangle, Activity, Settings } from "lucide-react"

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "scan", label: "New Scan", icon: Search },
  { id: "monitor", label: "Scan Monitor", icon: Activity },
  { id: "findings", label: "Findings", icon: AlertTriangle },
]

export default function Sidebar({ currentPage, onNavigate }) {
  return (
    <aside className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="p-6 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <Shield className="text-orange-500" size={28} />
          <span className="text-xl font-bold tracking-tight">HiveRecon</span>
        </div>
        <p className="text-zinc-500 text-xs mt-1">Recon Framework</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
              currentPage === id
                ? "bg-orange-500/10 text-orange-400 font-medium"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-zinc-800">
        <button
          onClick={() => onNavigate("settings")}
          className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
            currentPage === "settings"
              ? "bg-orange-500/10 text-orange-400 font-medium"
              : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
          }`}
        >
          <Settings size={18} />
          Settings
        </button>
        <p className="text-zinc-600 text-xs text-center mt-3">v0.1.0 — dev build</p>
      </div>
    </aside>
  )
}
