const REPORTS = [
  { id:'RPT-0041', cve:'CVE-2024-7890', system:'Spring Boot 3',    verdict:'EXPLOITABLE',     score:9.1, date:'2024-03-11', pages:14 },
  { id:'RPT-0040', cve:'CVE-2024-9012', system:'Linux Kernel 6.x', verdict:'PATCHED',          score:7.6, date:'2024-03-13', pages:11 },
  { id:'RPT-0039', cve:'CVE-2024-6789', system:'Nginx 1.25',       verdict:'FALSE POSITIVE',   score:5.9, date:'2024-03-09', pages:8  },
  { id:'RPT-0038', cve:'CVE-2024-0123', system:'curl 8.x',         verdict:'LOW RISK',         score:3.1, date:'2024-03-08', pages:6  },
  { id:'RPT-0037', cve:'CVE-2024-2345', system:'Docker Engine',    verdict:'UNDER REVIEW',     score:8.4, date:'2024-03-10', pages:9  },
]

const VERDICT_COL: Record<string,string> = {
  'EXPLOITABLE':'#ff1a35', 'PATCHED':'#00ff64', 'FALSE POSITIVE':'#ffc800', 'LOW RISK':'#ff7800', 'UNDER REVIEW':'#4db8ff'
}

export default function Reports() {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:22 }}>

      {/* STATS ROW */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14 }}>
        {[
          { label:'Total Reports',    val:'41', color:'#e8001d' },
          { label:'Exploitable',      val:'18', color:'#ff1a35' },
          { label:'Patched',          val:'15', color:'#00ff64' },
          { label:'Avg Pages',        val:'10', color:'#ffc800' },
        ].map((s,i) => (
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
            <tr>{['Report ID','CVE','System','Verdict','CVSS','Date','Pages','Action'].map(h=><th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {REPORTS.map((r,i) => (
              <tr key={i}>
                <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:12, color:'#888' }}>{r.id}</td>
                <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:12, color:'#e8001d' }}>{r.cve}</td>
                <td style={{ color:'#ccc', fontSize:14 }}>{r.system}</td>
                <td><span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:VERDICT_COL[r.verdict] ?? '#ccc', border:`1px solid ${VERDICT_COL[r.verdict] ?? '#ccc'}44`, padding:'3px 9px', borderRadius:2 }}>{r.verdict}</span></td>
                <td style={{ fontFamily:"'Share Tech Mono',monospace", color:'#f0f0f0' }}>{r.score}</td>
                <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#555' }}>{r.date}</td>
                <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#666' }}>{r.pages}pp</td>
                <td><button className="btn-outline" style={{ padding:'5px 14px', fontSize:9 }}>⬇ PDF</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}