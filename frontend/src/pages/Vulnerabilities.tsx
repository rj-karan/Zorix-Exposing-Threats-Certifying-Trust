import { useState } from 'react'

const ALL_CVES = [
  { id:'CVE-2024-1234', severity:'CRITICAL', score:9.8, status:'analyzing',  system:'Apache Struts 2',  desc:'Remote code execution via OGNL injection in file upload', date:'2024-03-15' },
  { id:'CVE-2024-5678', severity:'HIGH',     score:8.1, status:'simulating', system:'OpenSSL 3.x',      desc:'Buffer overflow in X.509 certificate parsing', date:'2024-03-14' },
  { id:'CVE-2024-9012', severity:'HIGH',     score:7.6, status:'complete',   system:'Linux Kernel 6.x', desc:'Privilege escalation via use-after-free in netfilter', date:'2024-03-13' },
  { id:'CVE-2024-3456', severity:'MEDIUM',   score:6.2, status:'failed',     system:'Node.js 18',       desc:'Path traversal in built-in HTTP module', date:'2024-03-12' },
  { id:'CVE-2024-7890', severity:'CRITICAL', score:9.1, status:'complete',   system:'Spring Boot 3',    desc:'Actuator endpoint exposes sensitive env variables', date:'2024-03-11' },
  { id:'CVE-2024-2345', severity:'HIGH',     score:8.4, status:'pending',    system:'Docker Engine',    desc:'Container escape via runc vulnerability', date:'2024-03-10' },
  { id:'CVE-2024-6789', severity:'MEDIUM',   score:5.9, status:'complete',   system:'Nginx 1.25',       desc:'HTTP/2 rapid reset denial of service', date:'2024-03-09' },
  { id:'CVE-2024-0123', severity:'LOW',      score:3.1, status:'complete',   system:'curl 8.x',         desc:'Certificate verification bypass in QUIC', date:'2024-03-08' },
]

const SEV_COL: Record<string,string> = { CRITICAL:'#ff1a35', HIGH:'#ffc800', MEDIUM:'#ff7800', LOW:'#00ff64' }
const FILTERS = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function Vulnerabilities() {
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<typeof ALL_CVES[0] | null>(null)

  const visible = ALL_CVES.filter(c =>
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

        {/* CARDS */}
        {visible.map((c,i) => (
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
                <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:32, color:SEV_COL[c.severity], lineHeight:1, textShadow:`0 0 15px ${SEV_COL[c.severity]}66` }}>{c.score}</div>
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
