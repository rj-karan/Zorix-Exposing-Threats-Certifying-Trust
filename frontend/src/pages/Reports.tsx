import { useState, useEffect } from 'react'

interface AnalysisResult {
  id: string
  repository: string
  vulnerability_type: string
  status: string
  cvss_score: number
  severity: string
  root_cause: string
  created_at: string
}

const VERDICT_COL: Record<string,string> = {
  'EXPLOITABLE':'#ff1a35', 'PATCHED':'#00ff64', 'FALSE POSITIVE':'#ffc800', 'LOW RISK':'#ff7800', 'UNDER REVIEW':'#4db8ff'
}

export default function Reports() {
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true)
        const res = await fetch('http://localhost:8000/api/analysis/results')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setResults(data.results || [])
        setError('')
      } catch (err) {
        console.error('Failed to fetch results:', err)
        setError('Failed to load data')
        setResults([])
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
    const interval = setInterval(fetchResults, 10000)
    return () => clearInterval(interval)
  }, [])

  const stats = [
    { label:'Total Reports', val:results.length.toString(), color:'#e8001d' },
    { label:'Critical', val:results.filter(r => r.severity === 'CRITICAL').length.toString(), color:'#ff1a35' },
    { label:'Completed', val:results.filter(r => r.status === 'complete').length.toString(), color:'#00ff64' },
    { label:'Avg CVSS', val:results.length > 0 ? (results.reduce((sum, r) => sum + (r.cvss_score || 0), 0) / results.length).toFixed(1) : '0', color:'#ffc800' },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:22 }}>

      {/* STATS ROW */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14 }}>
        {stats.map((s,i) => (
          <div key={i} className="panel" style={{ textAlign:'center', padding:'18px' }}>
            <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
            <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:42, color:s.color, lineHeight:1, textShadow:`0 0 15px ${s.color}55` }}>{s.val}</div>
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#555', letterSpacing:2, textTransform:'uppercase', marginTop:6 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* TABLE */}
      <div className="panel">
        <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:22 }}>
          <div className="section-title">Report Archive</div>
          <button className="btn-outline">+ Generate New</button>
        </div>
        <table className="zorix-table">
          <thead>
            <tr>{['Report ID','CVE','System','Status','CVSS','Date','Action'].map(h=><th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding:'20px', textAlign:'center', color:'#888' }}>Loading...</td></tr>
            ) : error ? (
              <tr><td colSpan={7} style={{ padding:'20px', textAlign:'center', color:'#ff1a35' }}>{error}</td></tr>
            ) : results.length === 0 ? (
              <tr><td colSpan={7} style={{ padding:'20px', textAlign:'center', color:'#888' }}>No reports yet</td></tr>
            ) : (
              results.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:12, color:'#888' }}>RPT-{String(1000 + i).slice(-4)}</td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:12, color:'#e8001d' }}>CVE-2024-{String(i + 1).padStart(4, '0')}</td>
                  <td style={{ color:'#ccc', fontSize:14 }}>{r.repository || r.vulnerability_type}</td>
                  <td><span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:VERDICT_COL[r.status] ?? '#ccc', border:`1px solid ${VERDICT_COL[r.status] ?? '#ccc'}44`, padding:'3px 9px', borderRadius:2 }}>{r.status?.toUpperCase()}</span></td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", color:'#f0f0f0' }}>{r.cvss_score?.toFixed(1) || 'N/A'}</td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#555' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                  <td><button className="btn-outline" style={{ padding:'5px 14px', fontSize:9 }}>Γ¼ç PDF</button></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

