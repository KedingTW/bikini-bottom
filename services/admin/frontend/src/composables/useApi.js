import { ref } from 'vue'

export function useApi() {
  async function get(url) {
    const res = await fetch(url)
    if (res.status === 401) { location.href = '/login'; return null; }
    return res.json()
  }

  async function post(url, body = null) {
    const opts = { method: 'POST' }
    if (body) { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(body); }
    const res = await fetch(url, opts)
    return res.json()
  }

  async function put(url, body = null) {
    const opts = { method: 'PUT' }
    if (body) { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(body); }
    const res = await fetch(url, opts)
    return res.json()
  }

  function formatMem(mb) {
    if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB'
    return mb.toFixed(0) + ' MB'
  }

  function pad(n) { return String(n).padStart(2, '0') }

  function formatTime24(date) {
    return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  }

  function parseCpuRaw(raw) {
    if (!raw) return 0
    if (raw.endsWith('n')) return parseInt(raw) / 1e6
    if (raw.endsWith('m')) return parseInt(raw)
    return parseInt(raw) * 1000
  }

  function parseMemRaw(raw) {
    if (!raw) return 0
    if (raw.endsWith('Ki')) return parseInt(raw) / 1024
    if (raw.endsWith('Mi')) return parseInt(raw)
    if (raw.endsWith('Gi')) return parseInt(raw) * 1024
    return 0
  }

  return { get, post, put, formatMem, pad, formatTime24, parseCpuRaw, parseMemRaw }
}
