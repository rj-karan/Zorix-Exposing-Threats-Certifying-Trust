import { useState, useEffect } from 'react'

interface AnalysisResult {
  id: string
  repository: string
  vulnerability_type: string
  status: string
  cvss_score: number
  severity: string
  root_cause: string
  confidence_score: number
  created_at: string
}

const SEVERITY_COL: Record<string, string> = {
  CRITICAL:'#ff1a35', HIGH:'#ffc800', MEDIUM:'#ff7800', LOW:'#00ff64'
}

export default function Dashboard() {
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
    { label: 'Total Analyses', value: results.length, sub: 'All time', color: '#e8001d' },
    { label: 'Completed', value: results.filter(r => r.status === 'complete').length, sub: 'Ready', color: '#ffc800' },
    { label: 'Critical Count', value: results.filter(r => r.severity === 'CRITICAL').length, sub: 'High priority', color: '#ff1a35' },
    { label: 'Avg Confidence', value: `${Math.round(results.reduce((sum, r) => sum + (r.confidence_score || 0), 0) / Math.max(results.length, 1))}%`, sub: 'Accuracy', color: '#00ff64' },
  ]

  const topCves = results.slice(0, 5)

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:28 }}>

      {/* STAT CARDS */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16 }}>
        {stats.map((s,i) => (
          <div key={i} className={`panel fade-up d${i+1}`} style={{ position:'relative' }}>
            <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#555', letterSpacing:3, textTransform:'uppercase', marginBottom:14 }}>{s.label}</div>
            <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:52, lineHeight:1, color:s.color, textShadow:`0 0 20px ${s.color}55` }}>{s.value}</div>
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#666', marginTop:8, letterSpacing:1 }}>{s.sub}</div>
            <div style={{ position:'absolute', bottom:0, left:0, right:0, height:2, background:`linear-gradient(90deg,transparent,${s.color}55,transparent)` }}/>
          </div>
        ))}
      </div>

      {/* MIDDLE ROW */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 340px', gap:16 }}>

        {/* LIVE CVE TABLE */}
        <div className="panel fade-up d2">
          <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:20 }}>
            <div className="section-title">Live Verifications</div>
            <span className="badge analyzing"><span className="badge-dot"/>SCANNING</span>
          </div>
          <table className="zorix-table">
            <thead>
              <tr>
                {['CVE ID','Severity','CVSS','System','Status','Time'].map(h => <th key={h}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding:'20px', textAlign:'center', color:'#888' }}>Loading...</td></tr>
              ) : error ? (
                <tr><td colSpan={6} style={{ padding:'20px', textAlign:'center', color:'#ff1a35' }}>{error}</td></tr>
              ) : topCves.length === 0 ? (
                <tr><td colSpan={6} style={{ padding:'20px', textAlign:'center', color:'#888' }}>No analyses yet</td></tr>
              ) : (
                topCves.map((c,i) => (
                  <tr key={i} style={{ cursor:'pointer' }}>
                    <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:12, color:'#e8001d' }}>CVE-2024-{String(i + 1).padStart(4, '0')}</td>
                    <td><span style={{ color:SEVERITY_COL[c.severity] ?? '#ccc', fontFamily:"'Share Tech Mono',monospace", fontSize:10, fontWeight:700 }}>{c.severity}</span></td>
                    <td style={{ fontFamily:"'Share Tech Mono',monospace", color:'#f0f0f0' }}>{c.cvss_score?.toFixed(1) || 'N/A'}</td>
                    <td style={{ color:'#ccc' }}>{c.repository || c.vulnerability_type}</td>
                    <td><span className={`badge ${c.status}`}><span className="badge-dot"/>{c.status?.toUpperCase()}</span></td>
                    <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#555' }}>{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* CONFIDENCE PANEL */}
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
          <div className="panel fade-up d3" style={{ flex:1 }}>
            <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
            <div className="section-title" style={{ marginBottom:18 }}>Confidence Score</div>
            <div style={{ textAlign:'center', padding:'10px 0 18px' }}>
              <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:72, lineHeight:1, color:'#e8001d', textShadow:'0 0 30px rgba(232,0,29,.7)' }}>84<span style={{ fontSize:32 }}>%</span></div>
              <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#555', letterSpacing:2, marginTop:4 }}>OVERALL ACCURACY</div>
            </div>
            {[
              { label:'Exploit Success', val:78, cls:'r' },
              { label:'Static Analysis', val:91, cls:'g' },
              { label:'Patch Validation', val:85, cls:'g' },
              { label:'AI Root Cause',   val:82, cls:'r' },
            ].map((m,i) => (
              <div key={i} style={{ marginBottom:12 }}>
                <div style={{ display:'flex', justifyContent:'space-between', marginBottom:5 }}>
                  <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#888', letterSpacing:1 }}>{m.label}</span>
                  <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#f0f0f0' }}>{m.val}%</span>
                </div>
                <div className="prog-track"><div className={`prog-fill ${m.cls}`} style={{ width:`${m.val}%` }}/></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* BOTTOM ROW */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>

        {/* ACTIVITY FEED */}
        <div className="panel fade-up d3">
          <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
          <div className="section-title" style={{ marginBottom:18 }}>Activity Feed</div>
          {[
            { dot:'#e8001d', text:'CVE-2024-1234 exploit payload generated', t:'2m ago' },
            { dot:'#ffc800', text:'Static scan initiated on OpenSSL 3.x source', t:'8m ago' },
            { dot:'#00ff64', text:'Patch verified ΓÇö CVE-2024-9012 CLOSED', t:'34m ago' },
            { dot:'#4db8ff', text:'AI root cause report generated for Spring Boot', t:'2h ago' },
            { dot:'#e8001d', text:'New CVE ingested from NVD feed', t:'3h ago' },
            { dot:'#ff7800', text:'Sandbox execution timed out ΓÇö retrying', t:'4h ago' },
          ].map((a,i) => (
            <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, padding:'11px 0', borderBottom:'1px solid rgba(255,255,255,.04)' }}>
              <div style={{ width:7, height:7, borderRadius:'50%', background:a.dot, boxShadow:`0 0 8px ${a.dot}`, marginTop:5, flexShrink:0 }}/>
              <div style={{ flex:1, fontSize:13, color:'#ccc', lineHeight:1.4 }}>{a.text}</div>
              <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#444', flexShrink:0 }}>{a.t}</div>
            </div>
          ))}
        </div>

        {/* EXPLOIT SIMULATION */}
        <div className="panel fade-up d4">
          <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:18 }}>
            <div className="section-title">Exploit Simulation</div>
            <span className="badge simulating"><span className="badge-dot"/>READY</span>
          </div>
          <div style={{ fontFamily:"'Share Tech Mono',monospace", background:'#060606', border:'1px solid rgba(232,0,29,.12)', borderRadius:3, padding:'16px 18px', marginBottom:16, lineHeight:1.9, fontSize:11 }}>
            <div style={{ color:'#555' }}>{'>'} Initializing sandbox environment...</div>
            <div style={{ color:'#00ff64' }}>{'>'} Target: CVE-2024-1234 [Apache Struts]</div>
            <div style={{ color:'#ffc800' }}>{'>'} Payload: RCE via OGNL injection</div>
            <div style={{ color:'#e8001d', animation:`blink 1.4s infinite` }}>{'>'} Awaiting execution trigger_</div>
          </div>
          {[
            { label:'Sandbox Ready',     val:true  },
            { label:'Payload Compiled',  val:true  },
            { label:'Target Isolated',   val:true  },
            { label:'Execution Complete',val:false },
          ].map((s,i) => (
            <div key={i} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'8px 0', borderBottom:'1px solid rgba(255,255,255,.03)' }}>
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#888', letterSpacing:1 }}>{s.label}</span>
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color: s.val ? '#00ff64' : '#e8001d' }}>{s.val ? 'Γ£ô OK' : 'Γùï PENDING'}</span>
            </div>
          ))}
          <div style={{ marginTop:18 }}>
            <button className="btn-solid" style={{ width:'100%' }}>Γû╢ RUN SIMULATION</button>
          </div>
        </div>
      </div>
    </div>
  )
}

