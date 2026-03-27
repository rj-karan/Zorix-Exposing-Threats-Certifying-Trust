import { useState, useEffect } from 'react'

const MONO = "'Share Tech Mono',monospace"
const BEBAS = "'Bebas Neue',sans-serif"

interface PatchEntry {
  id: string
  cve_id: string
  repository: string
  severity: string
  cvss_score: number
  patch_description: string
  references: string[]
  patches_available: boolean
  created_at: string
}

const SEV_COL: Record<string, string> = {
  CRITICAL: '#ff1a35', HIGH: '#ffc800', MEDIUM: '#ff7800', LOW: '#00ff64', UNKNOWN: '#555'
}

export default function Patches() {
  const [patches, setPatches] = useState<PatchEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<PatchEntry | null>(null)

  useEffect(() => {
    const loadPatches = async () => {
      try {
        setLoading(true)
        const res = await fetch('/api/analysis/results?limit=50')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()

        // Map analysis results to patch format
        const mapped: PatchEntry[] = (data.results || []).map((r: any, idx: number) => ({
          id: r.id || `patch-${idx}`,
          cve_id: r.cwe_id || `CVE-2024-${String(1000 + idx).slice(-4)}`,
          repository: r.repository || 'Unknown',
          severity: r.severity || 'MEDIUM',
          cvss_score: r.cvss_score || 0,
          patch_description: r.root_cause || 'Security vulnerability detected',
          references: [],
          patches_available: r.status === 'completed',
          created_at: r.created_at || new Date().toISOString(),
        }))
        setPatches(mapped)
      } catch (err) {
        console.error('Failed to load patches:', err)
      } finally {
        setLoading(false)
      }
    }
    loadPatches()
    const interval = setInterval(loadPatches, 15000)
    return () => clearInterval(interval)
  }, [])

  const visible = patches.filter(p =>
    (filter === 'All' || p.severity === filter) &&
    (p.cve_id.toLowerCase().includes(search.toLowerCase()) || p.repository.toLowerCase().includes(search.toLowerCase()))
  )

  const statusCounts = {
    total: patches.length,
    patched: patches.filter(p => p.patches_available).length,
    pending: patches.filter(p => !p.patches_available).length,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* STAT CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
        {[
          { label: 'Total CVEs', val: statusCounts.total, color: '#e8001d' },
          { label: 'Patched', val: statusCounts.patched, color: '#00ff64' },
          { label: 'Pending', val: statusCounts.pending, color: '#ffc800' },
        ].map((s, i) => (
          <div key={i} className={`panel fade-up d${i + 1}`} style={{ position: 'relative', textAlign: 'center' }}>
            <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
            <div style={{ fontFamily: MONO, fontSize: 9, color: '#555', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 10 }}>{s.label}</div>
            <div style={{ fontFamily: BEBAS, fontSize: 48, lineHeight: 1, color: s.color, textShadow: `0 0 18px ${s.color}55` }}>{s.val}</div>
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg,transparent,${s.color}55,transparent)` }} />
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 20 }}>

        {/* PATCH LIST */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* TOOLBAR */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <input
              className="zorix-input"
              placeholder="Search CVE ID or repository..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1 }}
            />
            <div style={{ display: 'flex', gap: 4 }}>
              {['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    fontFamily: MONO, fontSize: 10, letterSpacing: 1.5, padding: '8px 14px',
                    cursor: 'pointer', borderRadius: 2, textTransform: 'uppercase',
                    border: `1px solid ${filter === f ? '#e8001d' : 'rgba(232,0,29,.2)'}`,
                    background: filter === f ? 'rgba(232,0,29,.15)' : 'transparent',
                    color: filter === f ? '#fff' : '#888', transition: 'all .2s',
                  }}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* LOADING */}
          {loading && (
            <div style={{ padding: 30, textAlign: 'center' }}>
              <div style={{ fontFamily: MONO, fontSize: 12, color: '#888', letterSpacing: 2 }}>Loading patches...</div>
            </div>
          )}

          {/* EMPTY */}
          {!loading && visible.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center' }}>
              <div style={{ fontFamily: MONO, fontSize: 12, color: '#555', letterSpacing: 2 }}>No patches found</div>
            </div>
          )}

          {/* PATCH CARDS */}
          {!loading && visible.map((p, i) => (
            <div
              key={i}
              className="panel"
              onClick={() => setSelected(p)}
              style={{ cursor: 'pointer', border: selected?.id === p.id ? '1px solid rgba(232,0,29,.4)' : undefined }}
            >
              <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
                    <span style={{ fontFamily: MONO, fontSize: 13, color: '#e8001d', fontWeight: 700 }}>{p.cve_id}</span>
                    <span style={{ fontFamily: MONO, fontSize: 10, color: SEV_COL[p.severity], border: `1px solid ${SEV_COL[p.severity]}44`, padding: '2px 8px', borderRadius: 2 }}>{p.severity}</span>
                    <span className={`badge ${p.patches_available ? 'complete' : 'pending'}`}>
                      <span className="badge-dot" />{p.patches_available ? 'PATCHED' : 'PENDING'}
                    </span>
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f0', marginBottom: 4 }}>{p.repository}</div>
                  <div style={{ fontSize: 12, color: '#777', lineHeight: 1.4 }}>{p.patch_description?.slice(0, 120)}{(p.patch_description?.length || 0) > 120 ? '...' : ''}</div>
                </div>

                <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 20 }}>
                  <div style={{ fontFamily: BEBAS, fontSize: 28, color: SEV_COL[p.severity], lineHeight: 1, textShadow: `0 0 12px ${SEV_COL[p.severity]}66` }}>
                    {p.cvss_score?.toFixed(1) || '0.0'}
                  </div>
                  <div style={{ fontFamily: MONO, fontSize: 9, color: '#555', letterSpacing: 1 }}>CVSS</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* DETAIL PANEL */}
        {selected && (
          <div className="panel" style={{ width: 340, flexShrink: 0, alignSelf: 'flex-start', position: 'sticky', top: 20 }}>
            <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div className="section-title" style={{ fontSize: 14 }}>Patch Detail</div>
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer', fontSize: 18 }}>{'\u2715'}</button>
            </div>

            <div style={{ fontFamily: MONO, fontSize: 13, color: '#e8001d', marginBottom: 4 }}>{selected.cve_id}</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 6 }}>{selected.repository}</div>
            <div style={{ fontSize: 13, color: '#888', marginBottom: 18, lineHeight: 1.5 }}>{selected.patch_description}</div>

            <div style={{ fontFamily: BEBAS, fontSize: 48, color: SEV_COL[selected.severity], textAlign: 'center', textShadow: `0 0 25px ${SEV_COL[selected.severity]}77`, marginBottom: 4 }}>
              {selected.cvss_score?.toFixed(1) || '0.0'}
            </div>
            <div style={{ fontFamily: MONO, fontSize: 9, color: '#555', textAlign: 'center', letterSpacing: 3, marginBottom: 20 }}>CVSS v3 SCORE</div>

            {[
              ['Status', selected.patches_available ? 'PATCHED' : 'PENDING'],
              ['Severity', selected.severity],
              ['Reported', new Date(selected.created_at).toLocaleDateString()],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,.04)' }}>
                <span style={{ fontFamily: MONO, fontSize: 10, color: '#555', letterSpacing: 1 }}>{k}</span>
                <span style={{ fontFamily: MONO, fontSize: 10, color: v === 'PATCHED' ? '#00ff64' : v === 'PENDING' ? '#ffc800' : '#ccc' }}>{v}</span>
              </div>
            ))}

            {selected.references && selected.references.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontFamily: MONO, fontSize: 9, color: '#888', letterSpacing: 2, marginBottom: 8 }}>REFERENCES</div>
                {selected.references.map((ref, i) => (
                  <a key={i} href={ref} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'block', fontFamily: MONO, fontSize: 10, color: '#4db8ff', wordBreak: 'break-all', marginBottom: 4, textDecoration: 'none' }}
                  >
                    {ref}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
