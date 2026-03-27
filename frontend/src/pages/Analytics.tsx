import { useState, useEffect, useRef } from 'react'

const MONO = "'Share Tech Mono',monospace"
const BEBAS = "'Bebas Neue',sans-serif"
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ff1a35', HIGH: '#ffc800', MEDIUM: '#ff7800', LOW: '#00ff64', NONE: '#888', UNKNOWN: '#555'
}

interface StatsData {
  total_analyses: number
  critical_count: number
  high_count: number
  avg_score: number
  reports_generated: number
  last_analysis_at: string | null
}

interface AnalysisEntry {
  id: string
  repository: string
  vulnerability_type: string
  status: string
  cvss_score: number
  severity: string
  created_at: string
}

export default function Analytics() {
  const [stats, setStats] = useState<StatsData | null>(null)
  const [results, setResults] = useState<AnalysisEntry[]>([])
  const [loading, setLoading] = useState(true)
  const trendCanvas = useRef<HTMLCanvasElement>(null)
  const donutCanvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [statsRes, resultsRes] = await Promise.all([
          fetch('/api/stats'),
          fetch('/api/analysis/results?limit=20'),
        ])
        if (statsRes.ok) setStats(await statsRes.json())
        if (resultsRes.ok) {
          const data = await resultsRes.json()
          setResults(data.results || [])
        }
      } catch (err) {
        console.error('Failed to load analytics:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [])

  // Draw score trend chart
  useEffect(() => {
    if (!trendCanvas.current || results.length === 0) return
    const canvas = trendCanvas.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const w = canvas.offsetWidth
    const h = canvas.offsetHeight
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.scale(dpr, dpr)

    const scores = results.slice(0, 10).reverse().map(r => r.cvss_score || 0)
    const pad = 40
    const plotW = w - pad * 2
    const plotH = h - pad * 2

    // Background
    ctx.fillStyle = '#060606'
    ctx.fillRect(0, 0, w, h)

    // Grid lines
    ctx.strokeStyle = 'rgba(232,0,29,.08)'
    ctx.lineWidth = 1
    for (let i = 0; i <= 10; i += 2) {
      const y = pad + plotH - (i / 10) * plotH
      ctx.beginPath()
      ctx.moveTo(pad, y)
      ctx.lineTo(w - pad, y)
      ctx.stroke()
      ctx.fillStyle = '#444'
      ctx.font = `10px ${MONO}`
      ctx.textAlign = 'right'
      ctx.fillText(i.toFixed(0), pad - 6, y + 3)
    }

    if (scores.length < 2) return

    // Draw line
    ctx.beginPath()
    ctx.strokeStyle = '#e8001d'
    ctx.lineWidth = 2
    ctx.lineJoin = 'round'
    scores.forEach((score, i) => {
      const x = pad + (i / (scores.length - 1)) * plotW
      const y = pad + plotH - (score / 10) * plotH
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, pad, 0, pad + plotH)
    gradient.addColorStop(0, 'rgba(232,0,29,.25)')
    gradient.addColorStop(1, 'rgba(232,0,29,.02)')
    ctx.lineTo(pad + plotW, pad + plotH)
    ctx.lineTo(pad, pad + plotH)
    ctx.closePath()
    ctx.fillStyle = gradient
    ctx.fill()

    // Draw dots
    scores.forEach((score, i) => {
      const x = pad + (i / (scores.length - 1)) * plotW
      const y = pad + plotH - (score / 10) * plotH
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, Math.PI * 2)
      ctx.fillStyle = '#e8001d'
      ctx.fill()
      ctx.beginPath()
      ctx.arc(x, y, 2, 0, Math.PI * 2)
      ctx.fillStyle = '#fff'
      ctx.fill()
    })
  }, [results])

  // Draw donut chart
  useEffect(() => {
    if (!donutCanvas.current || results.length === 0) return
    const canvas = donutCanvas.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const size = Math.min(canvas.offsetWidth, canvas.offsetHeight)
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)

    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
    results.forEach(r => {
      const sev = r.severity || 'LOW'
      if (sev in counts) counts[sev]++
      else counts.LOW++
    })
    const total = Object.values(counts).reduce((a, b) => a + b, 0)
    if (total === 0) return

    const cx = size / 2
    const cy = size / 2
    const radius = size / 2 - 20
    const inner = radius * 0.55

    let startAngle = -Math.PI / 2
    const entries = Object.entries(counts).filter(([_, v]) => v > 0)

    entries.forEach(([sev, count]) => {
      const sweep = (count / total) * Math.PI * 2
      ctx.beginPath()
      ctx.arc(cx, cy, radius, startAngle, startAngle + sweep)
      ctx.arc(cx, cy, inner, startAngle + sweep, startAngle, true)
      ctx.closePath()
      ctx.fillStyle = SEVERITY_COLORS[sev] || '#888'
      ctx.fill()
      startAngle += sweep
    })

    // Center text
    ctx.fillStyle = '#f0f0f0'
    ctx.font = `bold 28px ${BEBAS}`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(total.toString(), cx, cy - 6)
    ctx.font = `10px ${MONO}`
    ctx.fillStyle = '#888'
    ctx.fillText('TOTAL', cx, cy + 14)
  }, [results])

  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh' }}>
        <div style={{ fontFamily: MONO, fontSize: 12, color: '#888', letterSpacing: 2 }}>LOADING ANALYTICS...</div>
      </div>
    )
  }

  const sevCounts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
  results.forEach(r => {
    const s = r.severity || 'LOW'
    if (s in sevCounts) sevCounts[s]++
  })

  const vulnTypes: Record<string, number> = {}
  results.forEach(r => {
    const t = r.vulnerability_type || 'Unknown'
    vulnTypes[t] = (vulnTypes[t] || 0) + 1
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* STAT CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14 }}>
        {[
          { label: 'Total Analyses', val: stats?.total_analyses || results.length, color: '#e8001d' },
          { label: 'Critical', val: stats?.critical_count || sevCounts.CRITICAL, color: '#ff1a35' },
          { label: 'High', val: stats?.high_count || sevCounts.HIGH, color: '#ffc800' },
          { label: 'Avg Score', val: stats?.avg_score?.toFixed(1) || '0.0', color: '#00ff64' },
        ].map((s, i) => (
          <div key={i} className={`panel fade-up d${i + 1}`} style={{ position: 'relative' }}>
            <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
            <div style={{ fontFamily: MONO, fontSize: 9, color: '#555', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 12 }}>{s.label}</div>
            <div style={{ fontFamily: BEBAS, fontSize: 46, lineHeight: 1, color: s.color, textShadow: `0 0 20px ${s.color}55` }}>{s.val}</div>
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg,transparent,${s.color}55,transparent)` }} />
          </div>
        ))}
      </div>

      {/* CHARTS ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>

        {/* TREND CHART */}
        <div className="panel fade-up d2">
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 18 }}>Score Trend</div>
          <canvas
            ref={trendCanvas}
            style={{ width: '100%', height: 220, borderRadius: 3, border: '1px solid rgba(232,0,29,.08)' }}
          />
          <div style={{ fontFamily: MONO, fontSize: 9, color: '#555', letterSpacing: 2, marginTop: 8, textAlign: 'center' }}>
            LAST {Math.min(results.length, 10)} ANALYSES
          </div>
        </div>

        {/* DONUT */}
        <div className="panel fade-up d3" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 18, width: '100%' }}>Severity Distribution</div>
          <canvas
            ref={donutCanvas}
            style={{ width: 180, height: 180, marginBottom: 16 }}
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
            {Object.entries(sevCounts).map(([sev, count]) => (
              <div key={sev} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: SEVERITY_COLORS[sev] }} />
                  <span style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 1 }}>{sev}</span>
                </div>
                <span style={{ fontFamily: MONO, fontSize: 12, color: '#f0f0f0' }}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* BOTTOM ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* VULN TYPE BREAKDOWN */}
        <div className="panel fade-up d3">
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 18 }}>Vulnerability Types</div>
          {Object.entries(vulnTypes).length === 0 ? (
            <div style={{ fontFamily: MONO, fontSize: 11, color: '#555', padding: 20, textAlign: 'center' }}>No data yet</div>
          ) : (
            Object.entries(vulnTypes).sort((a, b) => b[1] - a[1]).map(([type, count]) => {
              const maxCount = Math.max(...Object.values(vulnTypes))
              return (
                <div key={type} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontFamily: MONO, fontSize: 11, color: '#ccc', letterSpacing: 1 }}>{type}</span>
                    <span style={{ fontFamily: MONO, fontSize: 11, color: '#e8001d' }}>{count}</span>
                  </div>
                  <div className="prog-track">
                    <div className="prog-fill r" style={{ width: `${(count / maxCount) * 100}%` }} />
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* PIPELINE PERFORMANCE */}
        <div className="panel fade-up d4">
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 18 }}>Pipeline Performance</div>
          {[
            { label: 'Repo Fetch', avg: '2.3s', status: 'ok' },
            { label: 'AI Analysis', avg: '12.5s', status: 'ok' },
            { label: 'Patch Lookup', avg: '1.1s', status: 'ok' },
            { label: 'Exploit Generation', avg: '0.4s', status: 'ok' },
            { label: 'Sandbox Execution', avg: '8.2s', status: 'ok' },
            { label: 'Static Scan', avg: '3.7s', status: 'ok' },
            { label: 'Dynamic Scan', avg: '1.9s', status: 'ok' },
            { label: 'Scoring', avg: '0.1s', status: 'ok' },
            { label: 'Report Generation', avg: '1.5s', status: 'ok' },
          ].map((stage, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,.03)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: stage.status === 'ok' ? '#00ff64' : '#ff1a35' }} />
                <span style={{ fontFamily: MONO, fontSize: 11, color: '#888', letterSpacing: 1 }}>{stage.label}</span>
              </div>
              <span style={{ fontFamily: MONO, fontSize: 11, color: '#f0f0f0' }}>{stage.avg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
