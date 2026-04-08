import { useState, useEffect } from 'react'

interface OllamaPromptData {
  id: string
  analysis_id: string
  prompt_type: string
  prompt_text: string
  response_text: string | null
  generated_time: string
}

interface DockerLogData {
  id: string
  analysis_id: string
  container_id: string
  stdout: string | null
  stderr: string | null
  exit_code: number | null
  execution_time: number | null
  status: string
  created_at: string
}

interface StageLogData {
  id: string
  analysis_id: string
  stage_name: string
  status: string
  start_time: string | null
  end_time: string | null
  output_message: string | null
  created_at: string
}

interface DynamicScanData {
  id: string
  repo_url: string
  change_detected: boolean
  change_log: string | null
  scan_status: string
  created_at: string
}

interface PayloadResultData {
  id: string
  payload_id: string
  payload_type: string
  payload_category: string
  payload_string: string
  execution_status: string
  response_output: string | null
  exploit_success: boolean
  execution_time_ms: number | null
  created_at: string
}

type AdminTab = 'prompts' | 'docker' | 'stages' | 'dynamic' | 'payloads' | 'repo'

const ADMIN_TABS = [
  { key: 'stages',   label: 'Pipeline Stages', icon: '⚡' },
  { key: 'payloads', label: 'Payload Results',  icon: '🎯' },
  { key: 'prompts',  label: 'Ollama Prompts',   icon: '🤖' },
  { key: 'docker',   label: 'Docker Logs',      icon: '🐳' },
  { key: 'dynamic',  label: 'Dynamic Scans',    icon: '🔄' },
  { key: 'repo',     label: 'Repo Changes',     icon: '📂' },
]

const STATUS_COLOR: Record<string, string> = {
  completed: '#00ff64',
  running: '#ffc800',
  pending: '#888',
  failed: '#ff1a35',
  SUCCESS: '#00ff64',
  FAILED: '#ff1a35',
  ERROR: '#ff1a35',
}

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState<AdminTab>('stages')
  const [prompts, setPrompts] = useState<OllamaPromptData[]>([])
  const [dockerLogs, setDockerLogs] = useState<DockerLogData[]>([])
  const [stageLogs, setStageLogs] = useState<StageLogData[]>([])
  const [dynamicScans, setDynamicScans] = useState<DynamicScanData[]>([])
  const [payloadResults, setPayloadResults] = useState<PayloadResultData[]>([])
  const [repoChanges, setRepoChanges] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [payloadStats, setPayloadStats] = useState({ total: 0, successful: 0, failed: 0 })

  const fetchData = async (tab: AdminTab) => {
    setLoading(true)
    try {
      const base = 'http://localhost:8000/api/admin'
      let url = ''
      switch (tab) {
        case 'prompts': url = `${base}/ollama-prompts`; break
        case 'docker':  url = `${base}/docker-logs`; break
        case 'stages':  url = `${base}/stage-logs`; break
        case 'dynamic': url = `${base}/dynamic-scans`; break
        case 'payloads': url = `${base}/payload-results`; break
        case 'repo':    url = `${base}/repo-changes`; break
      }
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      switch (tab) {
        case 'prompts': setPrompts(data.prompts || []); break
        case 'docker':  setDockerLogs(data.docker_logs || []); break
        case 'stages':  setStageLogs(data.stage_logs || []); break
        case 'dynamic': setDynamicScans(data.dynamic_scans || []); break
        case 'payloads':
          setPayloadResults(data.payload_results || [])
          setPayloadStats({ total: data.total || 0, successful: data.successful || 0, failed: data.failed || 0 })
          break
        case 'repo': setRepoChanges(data.repo_changes || []); break
      }
    } catch (err) {
      console.error('Admin data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(activeTab)
    const interval = setInterval(() => fetchData(activeTab), 8000)
    return () => clearInterval(interval)
  }, [activeTab])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* HEADER */}
      <div className="panel fade-up d1" style={{ position: 'relative' }}>
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div className="section-title" style={{ marginBottom: 6 }}>Admin Panel</div>
            <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#555', letterSpacing: 2 }}>
              // FULL BACKEND OBSERVABILITY
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 14px', border: '1px solid rgba(0,255,100,.22)', background: 'rgba(0,255,100,.04)', borderRadius: 2 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#00ff64', boxShadow: '0 0 8px #00ff64', animation: 'livePulse 1.2s infinite' }} />
            <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#00ff64', letterSpacing: 2 }}>MONITORING</span>
          </div>
        </div>
      </div>

      {/* TAB BAR */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {ADMIN_TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key as AdminTab)}
            style={{
              fontFamily: "'Share Tech Mono',monospace", fontSize: 11, letterSpacing: 1,
              padding: '8px 16px', cursor: 'pointer', border: '1px solid rgba(232,0,29,.2)',
              borderRadius: 3, textTransform: 'uppercase',
              background: activeTab === t.key ? 'rgba(232,0,29,.15)' : 'rgba(6,6,6,.8)',
              color: activeTab === t.key ? '#e8001d' : '#888',
              transition: 'all .2s',
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* CONTENT */}
      {loading ? (
        <div className="panel" style={{ textAlign: 'center', padding: 40, color: '#888' }}>
          Loading...
        </div>
      ) : (
        <>
          {activeTab === 'stages' && <StageLogsPanel data={stageLogs} />}
          {activeTab === 'payloads' && <PayloadResultsPanel data={payloadResults} stats={payloadStats} />}
          {activeTab === 'prompts' && <OllamaPromptsPanel data={prompts} />}
          {activeTab === 'docker' && <DockerLogsPanel data={dockerLogs} />}
          {activeTab === 'dynamic' && <DynamicScansPanel data={dynamicScans} />}
          {activeTab === 'repo' && <RepoChangesPanel data={repoChanges} />}
        </>
      )}
    </div>
  )
}


// ============================
// SUB-PANELS
// ============================

function StageLogsPanel({ data }: { data: StageLogData[] }) {
  // Group by analysis_id
  const grouped: Record<string, StageLogData[]> = {}
  data.forEach(l => {
    const key = l.analysis_id?.substring(0, 8) || 'unknown'
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(l)
  })

  return (
    <div className="panel fade-up d2">
      <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
      <div className="section-title" style={{ marginBottom: 16 }}>Backend Pipeline Trace</div>
      {Object.keys(grouped).length === 0 ? (
        <div style={{ color: '#555', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No stage logs yet</div>
      ) : (
        Object.entries(grouped).map(([analysisKey, logs]) => (
          <div key={analysisKey} style={{ marginBottom: 24 }}>
            <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#e8001d', marginBottom: 10, letterSpacing: 1 }}>
              Analysis: {analysisKey}...
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {logs.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map((l, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '8px 12px', borderLeft: `3px solid ${STATUS_COLOR[l.status] || '#555'}`,
                  background: 'rgba(0,0,0,.2)', borderRadius: '0 3px 3px 0',
                }}>
                  <div style={{ width: 7, height: 7, borderRadius: '50%', background: STATUS_COLOR[l.status] || '#555', flexShrink: 0 }} />
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#f0f0f0', minWidth: 200 }}>
                    {l.stage_name}
                  </div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: STATUS_COLOR[l.status] || '#888', fontWeight: 700, minWidth: 80 }}>
                    {l.status?.toUpperCase()}
                  </div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#666', flex: 1 }}>
                    {l.output_message?.substring(0, 80) || ''}
                  </div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: '#444', flexShrink: 0 }}>
                    {l.start_time ? new Date(l.start_time).toLocaleTimeString() : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}


function PayloadResultsPanel({ data, stats }: { data: PayloadResultData[], stats: { total: number, successful: number, failed: number } }) {
  const successful = data.filter(p => p.exploit_success)
  const failed = data.filter(p => !p.exploit_success)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* STATS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {[
          { label: 'Total Payloads', value: stats.total, color: '#e8001d' },
          { label: 'Successful', value: stats.successful, color: '#00ff64' },
          { label: 'Failed', value: stats.failed, color: '#ff1a35' },
        ].map((s, i) => (
          <div key={i} className="panel fade-up d1" style={{ position: 'relative' }}>
            <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
            <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: '#555', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 10 }}>{s.label}</div>
            <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 42, lineHeight: 1, color: s.color, textShadow: `0 0 20px ${s.color}55` }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* SUCCESSFUL PAYLOADS */}
      {successful.length > 0 && (
        <div className="panel fade-up d2">
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 16, color: '#00ff64' }}>✓ Successful Exploit Payloads</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {successful.map((p, i) => (
              <div key={i} style={{
                border: '1px solid rgba(0,255,100,.2)', borderRadius: 3,
                padding: '10px 14px', background: 'rgba(0,255,100,.04)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#00ff64', letterSpacing: 1 }}>
                    [{p.payload_category}] {p.payload_id}
                  </span>
                  <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#00ff64', fontWeight: 700 }}>SUCCESS</span>
                </div>
                <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 12, color: '#f0f0f0', background: 'rgba(0,0,0,.3)', padding: '8px 10px', borderRadius: 2, wordBreak: 'break-all' }}>
                  {p.payload_string}
                </div>
                {p.response_output && (
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#888', marginTop: 6 }}>
                    Result: {p.response_output.substring(0, 120)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FAILED PAYLOADS */}
      {failed.length > 0 && (
        <div className="panel fade-up d3">
          <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
          <div className="section-title" style={{ marginBottom: 16 }}>✗ Failed Payloads</div>
          <table className="zorix-table">
            <thead>
              <tr>
                {['Payload ID', 'Category', 'Payload', 'Status', 'Time'].map(h => <th key={h}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {failed.slice(0, 30).map((p, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#e8001d' }}>{p.payload_id}</td>
                  <td style={{ color: '#888' }}>{p.payload_category}</td>
                  <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#ccc', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.payload_string.substring(0, 50)}</td>
                  <td><span style={{ color: '#ff1a35', fontFamily: "'Share Tech Mono',monospace", fontSize: 10, fontWeight: 700 }}>{p.execution_status}</span></td>
                  <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#555' }}>{p.execution_time_ms}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}


function OllamaPromptsPanel({ data }: { data: OllamaPromptData[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  return (
    <div className="panel fade-up d2">
      <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
      <div className="section-title" style={{ marginBottom: 16 }}>Ollama Generated Prompts</div>
      {data.length === 0 ? (
        <div style={{ color: '#555', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No prompts recorded yet</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {data.map((p, i) => (
            <div key={i} style={{
              border: '1px solid rgba(232,0,29,.15)', borderRadius: 3,
              padding: '12px 14px', background: 'rgba(0,0,0,.2)',
            }}>
              <div
                style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}
                onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
              >
                <div>
                  <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#e8001d', letterSpacing: 1, marginRight: 12 }}>
                    [{p.prompt_type.toUpperCase()}]
                  </span>
                  <span style={{ fontSize: 12, color: '#ccc' }}>
                    {p.prompt_text.substring(0, 80)}...
                  </span>
                </div>
                <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#555' }}>
                  {p.generated_time ? new Date(p.generated_time).toLocaleString() : ''}
                </span>
              </div>
              {expandedId === p.id && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: '#555', letterSpacing: 2, marginBottom: 6 }}>PROMPT:</div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#ccc', background: 'rgba(0,0,0,.3)', padding: 10, borderRadius: 2, whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                    {p.prompt_text}
                  </div>
                  {p.response_text && (
                    <>
                      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: '#555', letterSpacing: 2, marginTop: 10, marginBottom: 6 }}>RESPONSE:</div>
                      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#00ff64', background: 'rgba(0,0,0,.3)', padding: 10, borderRadius: 2, whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                        {p.response_text}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


function DockerLogsPanel({ data }: { data: DockerLogData[] }) {
  return (
    <div className="panel fade-up d2">
      <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
      <div className="section-title" style={{ marginBottom: 16 }}>Docker Execution Logs</div>
      {data.length === 0 ? (
        <div style={{ color: '#555', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No Docker logs yet</div>
      ) : (
        <table className="zorix-table">
          <thead>
            <tr>
              {['Container', 'Status', 'Exit Code', 'Time (ms)', 'Stdout', 'Timestamp'].map(h => <th key={h}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((l, i) => (
              <tr key={i}>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#e8001d' }}>{l.container_id?.substring(0, 12) || 'simulated'}</td>
                <td><span style={{ color: STATUS_COLOR[l.status] || '#888', fontFamily: "'Share Tech Mono',monospace", fontSize: 10, fontWeight: 700 }}>{l.status}</span></td>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", color: '#f0f0f0' }}>{l.exit_code ?? 'N/A'}</td>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", color: '#888' }}>{l.execution_time ?? 'N/A'}</td>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#ccc', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.stdout?.substring(0, 60) || '-'}</td>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#555' }}>{l.created_at ? new Date(l.created_at).toLocaleTimeString() : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}


function DynamicScansPanel({ data }: { data: DynamicScanData[] }) {
  return (
    <div className="panel fade-up d2">
      <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
      <div className="section-title" style={{ marginBottom: 16 }}>Dynamic Scan Activity</div>
      {data.length === 0 ? (
        <div style={{ color: '#555', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No dynamic scans yet</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {data.map((d, i) => (
            <div key={i} style={{
              border: `1px solid ${d.change_detected ? 'rgba(255,200,0,.3)' : 'rgba(0,255,100,.15)'}`,
              borderRadius: 3, padding: '12px 14px',
              background: d.change_detected ? 'rgba(255,200,0,.04)' : 'rgba(0,255,100,.04)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#f0f0f0' }}>
                    {d.repo_url}
                  </div>
                  <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: d.change_detected ? '#ffc800' : '#00ff64', marginTop: 4 }}>
                    {d.change_detected ? '⚠ Changes detected — Running dynamic scan...' : '✓ No changes detected'}
                  </div>
                </div>
                <span style={{
                  fontFamily: "'Share Tech Mono',monospace", fontSize: 10,
                  padding: '3px 10px', borderRadius: 2,
                  background: d.change_detected ? 'rgba(255,200,0,.15)' : 'rgba(0,255,100,.1)',
                  color: d.change_detected ? '#ffc800' : '#00ff64',
                }}>
                  {d.scan_status?.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


function RepoChangesPanel({ data }: { data: any[] }) {
  return (
    <div className="panel fade-up d2">
      <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
      <div className="section-title" style={{ marginBottom: 16 }}>Repository Change Status</div>
      {data.length === 0 ? (
        <div style={{ color: '#555', fontFamily: "'Share Tech Mono',monospace", fontSize: 12 }}>No repository monitoring data yet</div>
      ) : (
        <table className="zorix-table">
          <thead>
            <tr>
              {['Repository', 'Status', 'Scan Status', 'Last Checked'].map(h => <th key={h}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.map((r: any, i: number) => (
              <tr key={i}>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: '#e8001d' }}>{r.repo_url}</td>
                <td>
                  <span style={{ color: r.change_detected ? '#ffc800' : '#00ff64', fontFamily: "'Share Tech Mono',monospace", fontSize: 10, fontWeight: 700 }}>
                    {r.status}
                  </span>
                </td>
                <td style={{ color: '#ccc' }}>{r.scan_status}</td>
                <td style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: '#555' }}>
                  {r.last_checked ? new Date(r.last_checked).toLocaleString() : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
