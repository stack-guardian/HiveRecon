import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Settings2, Server, Brain, CheckCircle, XCircle, Key } from "lucide-react"
import { getHealth } from "@/api"

const MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma-7b-it"]

export default function Settings() {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem("apiUrl") || "http://localhost:8080")
  const [groqKey, setGroqKey] = useState(localStorage.getItem("groqKey") || "")
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem("model") || "llama-3.1-8b-instant")
  const [apiStatus, setApiStatus] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    getHealth()
      .then(() => setApiStatus(true))
      .catch(() => setApiStatus(false))
  }, [])

  const handleSave = () => {
    localStorage.setItem("apiUrl", apiUrl)
    localStorage.setItem("groqKey", groqKey)
    localStorage.setItem("model", selectedModel)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-zinc-400 text-sm mt-1">Configure HiveRecon preferences</p>
      </div>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Server size={16} /> API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-sm text-zinc-300">Backend API URL</label>
              {apiStatus === true && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle size={12} /> Connected
                </span>
              )}
              {apiStatus === false && (
                <span className="flex items-center gap-1 text-xs text-red-400">
                  <XCircle size={12} /> Unreachable
                </span>
              )}
            </div>
            <Input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="bg-zinc-800 border-zinc-700 text-white font-mono text-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-zinc-300">Groq API Key</label>
            <Input
              value={groqKey}
              onChange={(e) => setGroqKey(e.target.value)}
              type="password"
              placeholder="gsk_..."
              className="bg-zinc-800 border-zinc-700 text-white font-mono text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Brain size={16} /> AI Model
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-zinc-500">Select the Groq model to use for AI coordination</p>
          <div className="flex flex-wrap gap-2">
            {MODELS.map((model) => (
              <button
                key={model}
                onClick={() => setSelectedModel(model)}
                className={`px-3 py-1.5 rounded-md text-sm border font-mono transition-colors ${
                  selectedModel === model
                    ? "bg-orange-500/10 border-orange-500 text-orange-400"
                    : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
                }`}
              >
                {model}
              </button>
            ))}
          </div>
          <p className="text-xs text-zinc-600 mt-1">
            Currently selected: <span className="text-zinc-400 font-mono">{selectedModel}</span>
          </p>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Settings2 size={16} /> About
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-400">
          <div className="flex justify-between">
            <span>Version</span>
            <span className="text-zinc-300 font-mono">0.1.0</span>
          </div>
          <div className="flex justify-between">
            <span>Dashboard</span>
            <span className="text-zinc-300 font-mono">Vite + React + shadcn/ui</span>
          </div>
          <div className="flex justify-between">
            <span>Backend</span>
            <span className="text-zinc-300 font-mono">FastAPI + SQLite</span>
          </div>
          <div className="flex justify-between">
            <span>AI</span>
            <span className="text-zinc-300 font-mono">Groq (cloud)</span>
          </div>
        </CardContent>
      </Card>

      <button
        onClick={handleSave}
        className={`w-full py-3 rounded-lg font-medium transition-colors ${
          saved
            ? "bg-green-500/20 text-green-400 border border-green-500/30"
            : "bg-orange-500 hover:bg-orange-600 text-white"
        }`}
      >
        {saved ? "✓ Saved!" : "Save Settings"}
      </button>
    </div>
  )
}
