import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, Shield, CheckCircle } from "lucide-react"
import { createScan } from "@/api"

const emptyScopeData = {
  program: "",
  inDomains: [],
  inVulns: [],
  outDomains: [],
  outVulns: [],
}

function parseStoredArray(key) {
  try {
    const value = localStorage.getItem(key)
    const parsed = value ? JSON.parse(value) : []
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : []
  } catch {
    return []
  }
}

export default function NewScan() {
  const [target, setTarget] = useState("")
  const [platform, setPlatform] = useState("none")
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [scopeData, setScopeData] = useState(emptyScopeData)

  useEffect(() => {
    setScopeData({
      program: localStorage.getItem("scope_program") ?? "",
      inDomains: parseStoredArray("scope_in_domains"),
      inVulns: parseStoredArray("scope_in_vulns"),
      outDomains: parseStoredArray("scope_out_domains"),
      outVulns: parseStoredArray("scope_out_vulns"),
    })
  }, [])

  const handleScan = async () => {
    if (!target) return
    setScanning(true)
    setResult(null)
    setError(null)
    try {
      const scopeConfig = {
        program: scopeData.program,
        in_domains: scopeData.inDomains,
        in_vulns: scopeData.inVulns,
        out_domains: scopeData.outDomains,
        out_vulns: scopeData.outVulns,
      }
      const data = await createScan(target, platform === "none" ? null : platform, scopeConfig)
      setResult(data)
    } catch (e) {
      setError("Failed to connect to backend. Is the API running?")
    } finally {
      setScanning(false)
    }
  }

  const hasScope =
    Boolean(scopeData.program) ||
    scopeData.inDomains.length > 0 ||
    scopeData.outDomains.length > 0

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">New Scan</h1>
        <p className="text-zinc-400 text-sm mt-1">Launch a new reconnaissance scan</p>
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-orange-400 flex items-center gap-2">
            <Shield size={16} /> Active Scope
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasScope ? (
            <>
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wide text-zinc-500">Program</p>
                <p className="text-sm text-zinc-200">{scopeData.program || "No program selected"}</p>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-zinc-500">In Scope Domains</p>
                <div className="flex flex-wrap gap-2">
                  {scopeData.inDomains.length > 0 ? (
                    scopeData.inDomains.map((domain) => (
                      <Badge key={domain} className="bg-green-500/10 text-green-400 border border-green-500/30">
                        {domain}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-zinc-500">No in-scope domains configured.</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-zinc-500">Out of Scope Domains</p>
                <div className="flex flex-wrap gap-2">
                  {scopeData.outDomains.length > 0 ? (
                    scopeData.outDomains.map((domain) => (
                      <Badge key={domain} className="bg-red-500/10 text-red-400 border border-red-500/30">
                        {domain}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-zinc-500">No out-of-scope domains configured.</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-zinc-500">No active scope found in local storage.</p>
          )}
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Search size={16} /> Target Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm text-zinc-300">Target Domain</label>
            <Input
              placeholder="e.g. example.com"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-zinc-300">Bug Bounty Platform</label>
            <div className="flex gap-2 flex-wrap">
              {["none", "hackerone", "bugcrowd", "intigriti"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPlatform(p)}
                  className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
                    platform === p
                      ? "bg-orange-500/10 border-orange-500 text-orange-400"
                      : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
                  }`}
                >
                  {p === "none" ? "No Platform" : p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Shield size={16} /> Scan Modules
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {["Subdomain Enum", "Port Scan", "Nuclei", "Tech Detection", "JS Analysis"].map((mod) => (
              <Badge key={mod} className="bg-zinc-800 text-zinc-300 border border-zinc-700">
                {mod}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {result && (
        <div className="flex items-center gap-2 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
          <CheckCircle size={18} className="text-green-400" />
          <div>
            <p className="text-green-400 text-sm font-medium">Scan created successfully!</p>
            <p className="text-zinc-400 text-xs mt-0.5">Scan ID: {result.id} — Status: {result.status}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <button
        onClick={handleScan}
        disabled={!target || scanning}
        className={`w-full py-3 rounded-lg font-medium transition-colors ${
          scanning
            ? "bg-orange-500/50 text-white cursor-not-allowed"
            : target
            ? "bg-orange-500 hover:bg-orange-600 text-white"
            : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
        }`}
      >
        {scanning ? "Launching Scan..." : "Launch Scan"}
      </button>
    </div>
  )
}
