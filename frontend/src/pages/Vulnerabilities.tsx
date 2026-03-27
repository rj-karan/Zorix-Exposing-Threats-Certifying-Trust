import { useState, useEffect } from 'react'

interface VulnerabilityRecord {
  id: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  score: number
  status: string
  system: string
  desc: string
  date: string
}

const SEV_COL: Record<string, string> = { CRITICAL: '#ff1a35', HIGH: '#ffc800', MEDIUM: '#ff7800', LOW: '#00ff64' }
const FILTERS = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function Vulnerabilities() {
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<VulnerabilityRecord | null>(null)
  const [results, setResults] = useState<VulnerabilityRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true)
        const res = await fetch('http://localhost:8000/api/analysis/results')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        
        // Map API results to CVE format
        const mapped = (data.results || []).map((r: any, idx: number) => {
          const severity = (r.severity || 'LOW').toUpperCase() as 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
          return {
            id: `CVE-2024-${String(1000 + idx).slice(-4)}`,
            severity,
            score: r.cvss_score || 5.0,
            status: r.status || 'analyzing',
            system: r.repository || 'Unknown System',
            desc: r.root_cause || r.vulnerability_type || 'No description available',
            date: r.created_at ? new Date(r.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
          }
        })
        
        setResults(mapped)
        setError('')
      } catch (err) {
        console.error('Failed to fetch results:', err)
        setError('Failed to load vulnerabilities')
        setResults([])
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
    const interval = setInterval(fetchResults, 10000)
    return () => clearInterval(interval)
  }, [])

  const visible = results.filter(c =>
    (filter === 'All' || c.severity === filter) &&
    (c.id.toLowerCase().includes(search.toLowerCase()) || c.system.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div style={{ display:'flex', gap:20 }}>
      {/* LIST */}
      <div style={{ flex:1, display:'flex', flexDirection:'column', gap:16 }}>
        {/* TOOLBAR */}
        <div style={{ display:'flex', gap:12, alignItems:'center' }}>
          <input className="zorix-input" placeholder="Search CVE ID or system..." value={search} onChange={e=>setSearch(e.target.value)} style={{ flex:1 }}/>
          <div style={{ display:'flex', gap:4 }}>
            {FILTERS.map(f => (
              <button key={f} onClick={()=>setFilter(f)} style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, letterSpacing:1.5, padding:'8px 14px', cursor:'pointer', border:`1px solid ${filter===f ? '#e8001d' : 'rgba(232,0,29,.2)'}`, borderRadius:2, background: filter===f ? 'rgba(232,0,29,.15)' : 'transparent', color: filter===f ? '#fff' : '#888', transition:'all .2s', textTransform:'uppercase' }}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* LOADING STATE */}
        {loading && (
          <div style={{ padding: 20, textAlign: 'center', color: '#888' }}>
            <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>Loading vulnerabilities...</div>
          </div>
        )}

        {/* ERROR STATE */}
        {error && (
          <div style={{ padding: 16, border: '1px solid rgba(255,26,53,.3)', borderRadius: 2, color: '#ff1a35', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>
            {error}
          </div>
        )}

        {/* EMPTY STATE */}
        {!loading && !error && visible.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: '#555' }}>
            <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No vulnerabilities found</div>
          </div>
        )}

        {/* CARDS */}
        {!loading && visible.map((c, i) => (
          <div key={i} className="panel" onClick={()=>setSelected(c)} style={{ cursor:'pointer', border: selected?.id===c.id ? '1px solid rgba(232,0,29,.4)' : undefined }}>
            <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
            <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16 }}>
              <div style={{ flex:1 }}>
                <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:8 }}>
                  <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:13, color:'#e8001d', fontWeight:700 }}>{c.id}</span>
                  <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:SEV_COL[c.severity], border:`1px solid ${SEV_COL[c.severity]}44`, padding:'2px 8px', borderRadius:2 }}>{c.severity}</span>
                  <span className={`badge ${c.status}`}><span className="badge-dot"/>{c.status.toUpperCase()}</span>
                </div>
                <div style={{ fontSize:15, fontWeight:600, color:'#f0f0f0', marginBottom:4 }}>{c.system}</div>
                <div style={{ fontSize:13, color:'#777' }}>{c.desc}</div>
              </div>
              <div style={{ textAlign:'right', flexShrink:0 }}>
                <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:32, color:SEV_COL[c.severity], lineHeight:1, textShadow:`0 0 15px ${SEV_COL[c.severity]}66` }}>{c.score.toFixed(1)}</div>
                <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#555', letterSpacing:1 }}>CVSS v3</div>
                <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#444', marginTop:6 }}>{c.date}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* DETAIL PANEL */}
      {selected && (
        <div className="panel" style={{ width:340, flexShrink:0, alignSelf:'flex-start', position:'sticky', top:20 }}>
          <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:18 }}>
            <div className="section-title" style={{ fontSize:14 }}>Detail View</div>
            <button onClick={()=>setSelected(null)} style={{ background:'none', border:'none', color:'#555', cursor:'pointer', fontSize:18 }}>Γ£ò</button>
          </div>

          <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:13, color:'#e8001d', marginBottom:4 }}>{selected.id}</div>
          <div style={{ fontSize:16, fontWeight:700, color:'#fff', marginBottom:6 }}>{selected.system}</div>
          <div style={{ fontSize:13, color:'#888', marginBottom:18, lineHeight:1.5 }}>{selected.desc}</div>

          <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:56, color:SEV_COL[selected.severity], textAlign:'center', textShadow:`0 0 30px ${SEV_COL[selected.severity]}77`, marginBottom:4 }}>{selected.score}</div>
          <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#555', textAlign:'center', letterSpacing:3, marginBottom:20 }}>CVSS v3 SCORE</div>

          {[
            ['Severity',  selected.severity],
            ['Status',    selected.status.toUpperCase()],
            ['Reported',  selected.date],
            ['Vector',    'NETWORK'],
            ['Complexity','LOW'],
          ].map(([k,v]) => (
            <div key={k} style={{ display:'flex', justifyContent:'space-between', padding:'8px 0', borderBottom:'1px solid rgba(255,255,255,.04)' }}>
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#555', letterSpacing:1 }}>{k}</span>
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#ccc' }}>{v}</span>
            </div>
          ))}

          <div style={{ display:'flex', flexDirection:'column', gap:8, marginTop:20 }}>
            <button className="btn-solid" style={{ width:'100%' }}>Γû╢ Run Exploit Sim</button>
            <button className="btn-outline" style={{ width:'100%' }}>Γ¼ç Download Report</button>
          </div>
        </div>
      )}
    </div>
  )
}

