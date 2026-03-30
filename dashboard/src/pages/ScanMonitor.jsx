import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getScan, getScans, cancelScan } from "@/api"
import { Activity, Clock, Target, XCircle } from "lucide-react"

const statusColor = {
  pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  running: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  completed: "bg-green-500/10 text-green-400 border-green-500/30",
  failed: "bg-red-500/10 text-red-400 border-red-500/30",
}

function ScanCard({ scan, onCancel }) {
  const isActive = scan.status === "pending" || scan.status === "running"

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-orange-400" />
          <span className="font-mono text-sm text-zinc-200">{scan.target}</span>
        </div>
        <Badge className={`border text-xs ${statusColor[scan.status] ?? "bg-zinc-700 text-zinc-300 border-zinc-600"}`}>
          {scan.status}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-6 text-xs text-zinc-400">
          <span>ID: <span className="text-zinc-300 font-mono">{scan.scan_id}</span></span>
          {scan.platform && <span>Platform: <span className="text-zinc-300">{scan.platform}</span></span>}
        </div>

        <div className="flex gap-6 text-xs text-zinc-400">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            Created: {new Date(scan.created_at).toLocaleString()}
          </span>
          {scan.started_at && (
            <span>Started: {new Date(scan.started_at).toLocaleString()}</span>
          )}
          {scan.completed_at && (
            <span>Completed: {new Date(scan.completed_at).toLocaleString()}</span>
          )}
        </div>

        {isActive && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-zinc-400">
              <span>
                {scan.status === "pending" ? "Waiting to start..." : "Scan in progress..."}
              </span>
              {scan.status === "running" && (
                <span className="text-blue-400 animate-pulse">● Live</span>
              )}
            </div>
            <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  scan.status === "pending"
                    ? "w-1/6 bg-yellow-500"
                    : "w-2/3 bg-blue-500 animate-pulse"
                }`}
              />
            </div>
          </div>
        )}

        {isActive && (
          <button
            onClick={() => onCancel(scan.scan_id)}
            className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 transition-colors mt-1"
          >
            <XCircle size={14} />
            Cancel Scan
          </button>
        )}
      </CardContent>
    </Card>
  )
}

export default function ScanMonitor() {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchScans = () => {
    getScans().then((data) => {
      setScans(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleCancel = async (id) => {
    await cancelScan(id)
    fetchScans()
  }

  const active = scans.filter(s => s.status === "pending" || s.status === "running")
  const done = scans.filter(s => s.status === "completed" || s.status === "failed")

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Scan Monitor</h1>
          <p className="text-zinc-400 text-sm mt-1">Live scan status — auto refreshes every 3s</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <Activity size={14} className="text-orange-400 animate-pulse" />
          Live
        </div>
      </div>

      {loading ? (
        <p className="text-zinc-500 text-sm">Loading scans...</p>
      ) : (
        <>
          {active.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-zinc-400">Active ({active.length})</h2>
              {active.map(scan => (
                <ScanCard key={scan.scan_id} scan={scan} onCancel={handleCancel} />
              ))}
            </div>
          )}

          {done.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-zinc-400">Completed ({done.length})</h2>
              {done.map(scan => (
                <ScanCard key={scan.scan_id} scan={scan} onCancel={handleCancel} />
              ))}
            </div>
          )}

          {scans.length === 0 && (
            <Card className="bg-zinc-900 border-zinc-800">
              <CardContent className="py-12 text-center">
                <p className="text-zinc-500 text-sm">No scans yet. Launch one from New Scan!</p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
