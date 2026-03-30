const BASE_URL = "http://localhost:8080"

export async function getHealth() {
  const res = await fetch(`${BASE_URL}/health`)
  return res.json()
}

export async function getStats() {
  const res = await fetch(`${BASE_URL}/stats`)
  return res.json()
}

export async function getScans() {
  const res = await fetch(`${BASE_URL}/scans`)
  const data = await res.json()
  return data.scans ?? []
}

export async function getScan(id) {
  const res = await fetch(`${BASE_URL}/scans/${id}`)
  return res.json()
}

export async function createScan(target, platform) {
  const res = await fetch(`${BASE_URL}/scans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, platform_id: platform })
  })
  return res.json()
}

export async function getFindings() {
  const res = await fetch(`${BASE_URL}/findings`)
  const data = await res.json()
  return data.findings ?? []
}

export async function cancelScan(id) {
  const res = await fetch(`${BASE_URL}/scans/${id}`, { method: "DELETE" })
  return res.json()
}
