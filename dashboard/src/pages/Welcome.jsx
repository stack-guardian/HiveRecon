import { Shield, Zap, Target, ChevronRight } from "lucide-react"

export default function Welcome({ onStart }) {
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="max-w-lg w-full space-y-8 text-center">

        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="p-5 rounded-full bg-orange-500/10 border border-orange-500/20">
              <Shield size={48} className="text-orange-500" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight">HiveRecon</h1>
          <p className="text-zinc-400 text-sm">AI-Powered Reconnaissance Framework for Bug Bounty Hunting</p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: Zap, label: "AI Coordinated", desc: "LLM-guided recon agents" },
            { icon: Target, label: "Scope Aware", desc: "Respects boundaries" },
            { icon: Shield, label: "Audit Logged", desc: "Full accountability" },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 space-y-1">
              <Icon size={18} className="text-orange-500 mx-auto" />
              <p className="text-white text-xs font-medium">{label}</p>
              <p className="text-zinc-500 text-xs">{desc}</p>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <button
            onClick={onStart}
            className="w-full py-3 rounded-lg font-medium bg-orange-500 hover:bg-orange-600 text-white transition-colors flex items-center justify-center gap-2"
          >
            Get Started <ChevronRight size={18} />
          </button>
          <p className="text-zinc-600 text-xs">Authorized security research only</p>
        </div>

      </div>
    </div>
  )
}
