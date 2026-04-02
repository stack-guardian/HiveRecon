import { useState } from "react"
import { Shield, AlertTriangle, CheckCircle } from "lucide-react"

export default function LegalDisclaimer({ onAccept }) {
  const [checked, setChecked] = useState({
    authorized: false,
    scope: false,
    laws: false,
    logged: false,
  })

  const allChecked = Object.values(checked).every(Boolean)

  const toggle = (key) => setChecked((prev) => ({ ...prev, [key]: !prev[key] }))

  const handleAccept = () => {
    if (!allChecked) return
    onAccept()
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="max-w-lg w-full space-y-6">

        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="p-4 rounded-full bg-orange-500/10 border border-orange-500/20">
              <Shield size={40} className="text-orange-500" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">HiveRecon</h1>
          <p className="text-zinc-400 text-sm">AI-Powered Reconnaissance Framework</p>
        </div>

        <div className="border border-red-500/30 rounded-lg bg-red-500/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-red-400" />
            <span className="text-red-400 text-sm font-medium">Legal Disclaimer</span>
          </div>
          <p className="text-zinc-300 text-sm leading-relaxed">
            HiveRecon is designed for <span className="text-white font-medium">authorized security research only</span>. 
            Unauthorized scanning is illegal and violates terms of service. 
            All actions are logged for accountability. 
            The authors are not liable for misuse of this tool.
          </p>
        </div>

        <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-4 space-y-3">
          <p className="text-zinc-400 text-xs uppercase tracking-wider">I acknowledge that:</p>

          {[
            { key: "authorized", text: "I have explicit authorization to scan all targets" },
            { key: "scope", text: "I will respect scope boundaries at all times" },
            { key: "laws", text: "I will comply with all applicable laws and regulations" },
            { key: "logged", text: "I understand all actions are logged for accountability" },
          ].map(({ key, text }) => (
            <label
              key={key}
              onClick={() => toggle(key)}
              className="flex items-start gap-3 cursor-pointer group"
            >
              <div className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                checked[key]
                  ? "bg-orange-500 border-orange-500"
                  : "border-zinc-600 group-hover:border-zinc-400"
              }`}>
                {checked[key] && <CheckCircle size={14} className="text-white" />}
              </div>
              <span className="text-sm text-zinc-300 leading-relaxed">{text}</span>
            </label>
          ))}
        </div>

        <button
          onClick={handleAccept}
          disabled={!allChecked}
          className={`w-full py-3 rounded-lg font-medium transition-colors ${
            allChecked
              ? "bg-orange-500 hover:bg-orange-600 text-white"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          }`}
        >
          I Agree — Enter HiveRecon
        </button>

        <p className="text-zinc-600 text-xs text-center">
          By proceeding you accept full legal responsibility for your actions.
        </p>
      </div>
    </div>
  )
}
