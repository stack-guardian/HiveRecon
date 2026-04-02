import { useState } from "react"
import { Shield, Plus, X, ChevronRight, ClipboardPaste } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

function TagInput({ tags, onAdd, onRemove, placeholder, color }) {
  const [input, setInput] = useState("")
  const add = () => {
    if (!input.trim()) return
    onAdd(input.trim())
    setInput("")
  }
  const colors = {
    green: {
      btn: "bg-green-500/10 border-green-500/30 text-green-400 hover:bg-green-500/20",
      tag: "bg-green-500/10 border-green-500/20 text-green-400",
    },
    red: {
      btn: "bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20",
      tag: "bg-red-500/10 border-red-500/20 text-red-400",
    },
  }
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 text-sm"
        />
        <button onClick={add} className={`px-3 py-2 rounded-lg border transition-colors flex-shrink-0 ${colors[color].btn}`}>
          <Plus size={16} />
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((item, i) => (
            <div key={i} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-mono ${colors[color].tag}`}>
              {item}
              <button onClick={() => onRemove(i)}>
                <X size={11} className="hover:text-white transition-colors" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PasteParser({ onParsed, color }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState("")
  const parse = () => {
    const lines = text
      .split("\n")
      .map((l) => l.replace(/^[\\s\\-\\*\\•\\[\\]]+/, "").trim())
      .filter((l) => l.length > 4)
    onParsed(lines)
    setText("")
    setOpen(false)
  }
  const colors = {
    green: "border-green-500/30 text-green-400",
    red: "border-red-500/30 text-red-400",
  }
  return (
    <div className="space-y-2">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 text-xs border rounded-md px-2.5 py-1.5 transition-colors ${colors[color]} hover:bg-zinc-800`}
      >
        <ClipboardPaste size={12} />
        Paste a list to auto-parse
      </button>
      {open && (
        <div className="space-y-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste multiple items here, one per line..."
            rows={5}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-3 text-sm text-zinc-300 placeholder:text-zinc-600 resize-none focus:outline-none focus:border-zinc-500"
          />
          <button
            onClick={parse}
            disabled={!text.trim()}
            className={`px-3 py-1.5 rounded-lg text-xs border transition-colors ${
              text.trim() ? `${colors[color]} hover:bg-zinc-800` : "border-zinc-700 text-zinc-600 cursor-not-allowed"
            }`}
          >
            Parse & Add Items
          </button>
        </div>
      )}
    </div>
  )
}

export default function ScopeConfig({ onDone }) {
  const [program, setProgram] = useState("")
  const [inDomains, setInDomains] = useState([])
  const [inVulns, setInVulns] = useState([])
  const [outDomains, setOutDomains] = useState([])
  const [outVulns, setOutVulns] = useState([])

  const addTo = (setter) => (item) => setter(prev => [...prev, item])
  const removeFrom = (setter) => (i) => setter(prev => prev.filter((_, idx) => idx !== i))
  const parseInto = (setter) => (items) => setter(prev => [...new Set([...prev, ...items])])

  const canProceed = inDomains.length > 0 || inVulns.length > 0

  const handleDone = () => {
    if (!canProceed) return
    localStorage.setItem("scope_program", program)
    localStorage.setItem("scope_in_domains", JSON.stringify(inDomains))
    localStorage.setItem("scope_in_vulns", JSON.stringify(inVulns))
    localStorage.setItem("scope_out_domains", JSON.stringify(outDomains))
    localStorage.setItem("scope_out_vulns", JSON.stringify(outVulns))
    onDone()
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="max-w-xl w-full space-y-5">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="p-4 rounded-full bg-orange-500/10 border border-orange-500/20">
              <Shield size={36} className="text-orange-500" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">Scope Configuration</h1>
          <p className="text-zinc-400 text-sm">Define targets and vulnerability types before scanning</p>
        </div>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400">Bug Bounty Program (optional)</CardTitle>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="e.g. HackerOne — Acme Corp"
              value={program}
              onChange={(e) => setProgram(e.target.value)}
              className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500"
            />
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400" /> In Scope
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Domains / Targets</p>
              <TagInput tags={inDomains} onAdd={addTo(setInDomains)} onRemove={removeFrom(setInDomains)} placeholder="e.g. *.example.com" color="green" />
              <PasteParser onParsed={parseInto(setInDomains)} color="green" />
            </div>
            <div className="border-t border-zinc-800 pt-3 space-y-1">
              <p className="text-xs text-zinc-500">Vulnerability Types</p>
              <TagInput tags={inVulns} onAdd={addTo(setInVulns)} onRemove={removeFrom(setInVulns)} placeholder="e.g. XSS, SQLi, SSRF" color="green" />
              <PasteParser onParsed={parseInto(setInVulns)} color="green" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-400" /> Out of Scope
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Domains / Targets</p>
              <TagInput tags={outDomains} onAdd={addTo(setOutDomains)} onRemove={removeFrom(setOutDomains)} placeholder="e.g. admin.example.com" color="red" />
              <PasteParser onParsed={parseInto(setOutDomains)} color="red" />
            </div>
            <div className="border-t border-zinc-800 pt-3 space-y-1">
              <p className="text-xs text-zinc-500">Vulnerability Types</p>
              <TagInput tags={outVulns} onAdd={addTo(setOutVulns)} onRemove={removeFrom(setOutVulns)} placeholder="e.g. Clickjacking, CSRF" color="red" />
              <PasteParser onParsed={parseInto(setOutVulns)} color="red" />
            </div>
          </CardContent>
        </Card>
        <button
          onClick={handleDone}
          disabled={!canProceed}
          className={`w-full py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
            canProceed ? "bg-orange-500 hover:bg-orange-600 text-white" : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          }`}
        >
          Enter HiveRecon <ChevronRight size={18} />
        </button>
        <p className="text-zinc-600 text-xs text-center">You can update scope anytime from Settings</p>
      </div>
    </div>
  )
}
