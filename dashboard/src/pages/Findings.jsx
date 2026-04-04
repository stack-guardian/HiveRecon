import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { AlertTriangle } from "lucide-react"
import { getFindings } from "@/api"

const severityColor = {
  info: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  low: "bg-green-500/10 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  high: "bg-red-500/10 text-red-400 border-red-500/30",
  critical: "bg-purple-500/10 text-purple-400 border-purple-500/30",
}

export default function Findings() {
  const [findings, setFindings] = useState([])
  const [filter, setFilter] = useState("All")

  useEffect(() => {
    getFindings().then(setFindings).catch(() => {})
  }, [])

  const filtered = filter === "All"
    ? findings
    : findings.filter((f) => f.severity?.toLowerCase() === filter.toLowerCase())

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Findings</h1>
        <p className="text-zinc-400 text-sm mt-1">All discovered vulnerabilities and recon data</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["All", "Critical", "High", "Medium", "Low", "Info"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
              filter === f
                ? "bg-orange-500/10 border-orange-500 text-orange-400"
                : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <AlertTriangle size={16} /> Results
            <Badge className="bg-zinc-800 text-zinc-300 border border-zinc-700 ml-auto">
              {filtered.length} found
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filtered.length === 0 ? (
            <p className="text-zinc-500 text-sm text-center py-8">No findings yet. Run a scan first!</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="text-zinc-400">Location</TableHead>
                  <TableHead className="text-zinc-400">Type</TableHead>
                  <TableHead className="text-zinc-400">Severity</TableHead>
                  <TableHead className="text-zinc-400">Title</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((f) => (
                  <TableRow key={f.id} className="border-zinc-800 hover:bg-zinc-800/50">
                    <TableCell className="font-mono text-sm text-zinc-200">{f.location || 'N/A'}</TableCell>
                    <TableCell className="text-zinc-300">{f.finding_type}</TableCell>
                    <TableCell>
                      <Badge className={`border text-xs ${severityColor[f.severity] ?? severityColor.info}`}>
                        {f.severity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-zinc-300 text-sm">{f.title}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

