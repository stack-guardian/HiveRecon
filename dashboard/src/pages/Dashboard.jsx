import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, Search, AlertTriangle, CheckCircle } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { getStats, getScans, getHealth } from "@/api"

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [scans, setScans] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {})
    getStats().then(setStats).catch(() => {})
    getScans().then(setScans).catch(() => {})
  }, [])

  const statCards = [
    { title: "Total Scans", value: stats?.scans?.total ?? "...", icon: Search, color: "text-blue-400" },
    { title: "Pending", value: stats?.scans?.by_status?.pending ?? 0, icon: Shield, color: "text-orange-400" },
    { title: "Completed", value: stats?.scans?.by_status?.completed ?? 0, icon: CheckCircle, color: "text-green-400" },
    { title: "Findings", value: stats?.findings?.total ?? 0, icon: AlertTriangle, color: "text-red-400" },
  ]

  const chartData = [
    { name: "Pending", value: stats?.scans?.by_status?.pending ?? 0 },
    { name: "Running", value: stats?.scans?.by_status?.running ?? 0 },
    { name: "Completed", value: stats?.scans?.by_status?.completed ?? 0 },
    { name: "Failed", value: stats?.scans?.by_status?.failed ?? 0 },
  ]

  const statusColor = {
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    running: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    completed: "bg-green-500/10 text-green-400 border-green-500/30",
    failed: "bg-red-500/10 text-red-400 border-red-500/30",
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-zinc-400 text-sm mt-1">Overview of your recon activity</p>
        </div>
        {health && (
          <Badge className="bg-green-500/10 text-green-400 border border-green-500/30">
            API Online
          </Badge>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ title, value, icon: Icon, color }) => (
          <Card key={title} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-zinc-400">{title}</CardTitle>
              <Icon size={18} className={color} />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">Scans by Status</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="#52525b" tick={{ fill: "#a1a1aa" }} />
              <YAxis stroke="#52525b" tick={{ fill: "#a1a1aa" }} allowDecimals={false} />
              <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", color: "#fff" }} />
              <Bar dataKey="value" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400">Recent Scans</CardTitle>
        </CardHeader>
        <CardContent>
          {scans.length === 0 ? (
            <p className="text-zinc-500 text-sm text-center py-8">No scans yet. Start your first scan!</p>
          ) : (
            <div className="space-y-2">
              {scans.slice(0, 5).map((scan) => (
                <div key={scan.scan_id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800">
                  <div>
                    <p className="font-mono text-sm text-zinc-200">{scan.target}</p>
                    <p className="text-zinc-500 text-xs mt-0.5">ID: {scan.scan_id}</p>
                  </div>
                  <Badge className={`border text-xs ${statusColor[scan.status] ?? "bg-zinc-700 text-zinc-300 border-zinc-600"}`}>
                    {scan.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
