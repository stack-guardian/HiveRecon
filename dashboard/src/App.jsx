import { useState } from "react"
import Sidebar from "./components/Sidebar"
import Dashboard from "./pages/Dashboard"
import NewScan from "./pages/NewScan"
import Findings from "./pages/Findings"
import ScanMonitor from "./pages/ScanMonitor"
import Settings from "./pages/Settings"

export default function App() {
  const [page, setPage] = useState("dashboard")

  const renderPage = () => {
    if (page === "dashboard") return <Dashboard />
    if (page === "scan") return <NewScan />
    if (page === "monitor") return <ScanMonitor />
    if (page === "findings") return <Findings />
    if (page === "settings") return <Settings />
  }

  return (
    <div className="flex h-screen bg-zinc-950 text-white overflow-hidden">
      <Sidebar currentPage={page} onNavigate={setPage} />
      <main className="flex-1 overflow-y-auto p-6">
        {renderPage()}
      </main>
    </div>
  )
}
