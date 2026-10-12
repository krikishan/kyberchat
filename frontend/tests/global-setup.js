import { spawn } from 'node:child_process'
import path from 'node:path'

const PORT = 5055
export const BACKEND_URL = `http://127.0.0.1:${PORT}`

let serverProcess

async function waitForHealth(timeoutMs = 15000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/health`)
      if (res.ok) return
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 300))
  }
  throw new Error('Backend test server did not become healthy in time.')
}

export async function setup() {
  const backendDir = path.resolve(__dirname, '../../backend')
  serverProcess = spawn('python3', ['scripts/test_server.py', String(PORT)], {
    cwd: backendDir,
    stdio: 'pipe',
  })
  await waitForHealth()
}

export async function teardown() {
  if (serverProcess) serverProcess.kill()
}
