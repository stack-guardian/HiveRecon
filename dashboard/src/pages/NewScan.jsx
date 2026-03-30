import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, Shield, CheckCircle } from "lucide-react"
import { createScan } from "@/api"

export default function NewScan() {
  const [target, setTarget] = useState("")
  const [platform, setPlatform] = useState("none")
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleScan = async () => {
    if (!target) return
    setScanning(true)
    setResult(null)
    setError(null)
    try {
      const data = await createScan(target, platform === "none" ? null : platform)
      setResult(data)
    } catch (e) {
      setError("Failed to connect to backend. Is the API running?")
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">New Scan</h1>
        <p className="text-zinc-400 text-sm mt-1">Launch a new reconnaissance scan</p>
      </div>

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
