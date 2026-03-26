import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const SEVERITY_COL: Record<string, string> = {
  CRITICAL:'#ff1a35', HIGH:'#ffc800', MEDIUM:'#ff7800', LOW:'#00ff64', UNKNOWN:'#888'
}

const formatTime = (isoString: string): string => {
  const date = new Date(isoString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export default function Dashboard({ onLogout }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    critical: 0,
    highScore: 0
  })
  const [tick, setTick] = useState(0)
  const navigate = useNavigate()
  
  // Fetch results on component mount
  useEffect(() => {
    fetchResults()
  }, [])
  
  // Auto-refresh every 5 seconds
  useEffect(() => { 
    const id = setInterval(() => {
      fetchResults()
      setTick(t => t+1)
    }, 5000)
    return () => clearInterval(id)
  }, [])

  const fetchResults = async () => {
    try {
      const response = await fetch('/api/analysis/results')
      if (!response.ok) throw new Error('Failed to fetch results')
      
      const data = await response.json()
      setResults(data.results || [])
      
      // Calculate stats
      const resultsArray = data.results || []
      setStats({
        total: resultsArray.length,
        completed: resultsArray.length,
        critical: resultsArray.filter((r: any) => r.severity === 'CRITICAL').length,
        highScore: resultsArray.filter((r: any) => r.cvss_score >= 7.0).length
      })
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching results:', error)
      setLoading(false)
    }
  }


  const handleLogout = () => {
    onLogout()
    navigate('/login')
  }

  const STATS = [
    { label: 'Total Analyses', value: stats.total, sub: 'All time', color: '#e8001d' },
    { label: 'Completed Scans',     value: stats.completed,  sub: 'Results ready', color: '#00ff64' },
    { label: 'Critical Issues',   value: stats.critical, sub: 'High priority', color: '#e8001d' },
    { label: 'High Risk Score',    value: stats.highScore,  sub: 'CVSS >= 7.0', color: '#ffc800' },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:28 }}>

      {/* STAT CARDS */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16 }}>
        {STATS.map((s,i) => (
          <div key={i} className={`panel fade-up d${i+1}`} style={{ position:'relative' }}>
            <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#555', letterSpacing:3, textTransform:'uppercase', marginBottom:14 }}>{s.label}</div>
            <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:52, lineHeight:1, color:s.color, textShadow:`0 0 20px ${s.color}55` }}>{s.value}</div>
            <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#666', marginTop:8, letterSpacing:1 }}>{s.sub}</div>
            <div style={{ position:'absolute', bottom:0, left:0, right:0, height:2, background:`linear-gradient(90deg,transparent,${s.color}55,transparent)` }}/>
          </div>
        ))}
      </div>

      {/* ANALYSIS RESULTS TABLE */}
      <div className="panel fade-up d2">
        <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:20 }}>
          <div className="section-title">Analysis Results</div>
          <span className={`badge ${loading ? 'analyzing' : 'complete'}`}>
            <span className="badge-dot"/>{loading ? 'LOADING' : 'READY'}
          </span>
        </div>
        
        {loading && (
          <div style={{ textAlign:'center', padding:'40px', color:'#888' }}>
            <div style={{ fontFamily:"'Share Tech Mono',monospace" }}>Loading analysis results...</div>
          </div>
        )}
        
        {!loading && results.length === 0 && (
          <div style={{ textAlign:'center', padding:'40px', color:'#888' }}>
            <div style={{ fontFamily:"'Share Tech Mono',monospace" }}>No analysis results available</div>
            <div style={{ fontSize:12, marginTop:10 }}>Run an analysis to see results here</div>
          </div>
        )}
        
        {!loading && results.length > 0 && (
          <table className="zorix-table">
            <thead>
              <tr>
                {['Repository','Vulnerability','Severity','CVSS','Confidence','Status','Time'].map(h => <th key={h}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {results.map((result: any, i: number) => (
                <tr key={i} style={{ cursor:'pointer' }}>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#4db8ff', maxWidth:'150px', overflow:'hidden', textOverflow:'ellipsis' }}>
                    {result.repository?.split('/').pop() || 'Unknown'}
                  </td>
                  <td style={{ fontSize:12, color:'#ccc' }}>{result.vulnerability_type || 'Unknown'}</td>
                  <td><span style={{ color:SEVERITY_COL[result.severity] || '#888', fontFamily:"'Share Tech Mono',monospace", fontSize:10, fontWeight:700 }}>{result.severity || 'UNKNOWN'}</span></td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", color:'#f0f0f0' }}>{result.cvss_score?.toFixed(1) || 'N/A'}</td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", color:'#f0f0f0' }}>{result.confidence_score?.toFixed(0) || 'N/A'}%</td>
                  <td><span className="badge complete"><span className="badge-dot"/>{result.status?.toUpperCase() || 'COMPLETE'}</span></td>
                  <td style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, color:'#555' }}>{formatTime(result.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
