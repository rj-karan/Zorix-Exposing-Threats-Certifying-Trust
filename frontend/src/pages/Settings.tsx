import { useState, useEffect } from 'react'

interface SettingsState {
  ai: {
    provider: string
    model: string
    ollama_base_url: string
    anthropic_api_key: string
    openai_api_key: string
  }
  scanners: {
    bandit_enabled: boolean
    semgrep_enabled: boolean
    nuclei_enabled: boolean
  }
  sandbox: {
    docker_socket: string
    sandbox_image: string
    sandbox_timeout: number
    sandbox_memory: string
  }
  database: {
    type: string
    url: string
  }
  notifications: {
    default_webhook_url: string
    email_notifications: boolean
    notification_email: string
  }
}

const MONO = "'Share Tech Mono',monospace"
const BEBAS = "'Bebas Neue',sans-serif"

export default function Settings() {
  const [settings, setSettings] = useState<SettingsState | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')
  const [dbTestResult, setDbTestResult] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/settings')
      if (res.ok) {
        const data = await res.json()
        setSettings(data)
      }
    } catch (err) {
      console.error('Failed to load settings:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    setSaveMsg('')
    try {
      const body: any = {
        ai_provider: settings.ai.provider,
        ai_model: settings.ai.model,
        ollama_base_url: settings.ai.ollama_base_url,
        bandit_enabled: settings.scanners.bandit_enabled,
        semgrep_enabled: settings.scanners.semgrep_enabled,
        nuclei_enabled: settings.scanners.nuclei_enabled,
        sandbox_timeout: settings.sandbox.sandbox_timeout,
        sandbox_memory: settings.sandbox.sandbox_memory,
        default_webhook_url: settings.notifications.default_webhook_url,
        email_notifications: settings.notifications.email_notifications,
        notification_email: settings.notifications.notification_email,
      }
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        setSaveMsg('Settings saved successfully')
        setTimeout(() => setSaveMsg(''), 3000)
      } else {
        setSaveMsg('Failed to save settings')
      }
    } catch (err) {
      setSaveMsg('Error saving settings')
    } finally {
      setSaving(false)
    }
  }

  const testDbConnection = async () => {
    setDbTestResult('Testing...')
    try {
      const res = await fetch('/health')
      const data = await res.json()
      if (data.services?.database) {
        setDbTestResult('Connection successful')
      } else {
        setDbTestResult('Connection failed')
      }
    } catch {
      setDbTestResult('Connection failed')
    }
    setTimeout(() => setDbTestResult(''), 4000)
  }

  const updateSetting = (section: string, key: string, value: any) => {
    setSettings(prev => {
      if (!prev) return prev
      return {
        ...prev,
        [section]: {
          ...prev[section as keyof SettingsState],
          [key]: value,
        },
      } as SettingsState
    })
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh' }}>
        <div style={{ fontFamily: MONO, fontSize: 12, color: '#888', letterSpacing: 2 }}>LOADING CONFIGURATION...</div>
      </div>
    )
  }

  if (!settings) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh' }}>
        <div style={{ fontFamily: MONO, fontSize: 12, color: '#ff1a35', letterSpacing: 2 }}>FAILED TO LOAD SETTINGS</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 900 }}>

      {/* SAVE BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="section-title">System Configuration</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {saveMsg && (
            <span style={{ fontFamily: MONO, fontSize: 11, color: saveMsg.includes('success') ? '#00ff64' : '#ff1a35', letterSpacing: 1 }}>
              {saveMsg}
            </span>
          )}
          <button className="btn-outline" onClick={fetchSettings}>Reset</button>
          <button className="btn-solid" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : '\u{2714} Save Configuration'}
          </button>
        </div>
      </div>

      {/* AI CONFIGURATION */}
      <div className="panel fade-up d1">
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div className="section-title" style={{ marginBottom: 20 }}>AI / LLM Configuration</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>PROVIDER</label>
            <select
              className="zorix-input"
              value={settings.ai.provider}
              onChange={e => updateSetting('ai', 'provider', e.target.value)}
            >
              <option value="ollama">Ollama (Local / Free)</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="openai">OpenAI (GPT)</option>
            </select>
          </div>

          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>MODEL</label>
            <input
              className="zorix-input"
              value={settings.ai.model}
              onChange={e => updateSetting('ai', 'model', e.target.value)}
              placeholder="e.g. mistral, codellama, llama2"
            />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>OLLAMA BASE URL</label>
            <input
              className="zorix-input"
              value={settings.ai.ollama_base_url}
              onChange={e => updateSetting('ai', 'ollama_base_url', e.target.value)}
              placeholder="http://localhost:11434"
            />
          </div>
        </div>

        <div style={{ marginTop: 14, padding: '10px 14px', background: 'rgba(0,255,100,.04)', border: '1px solid rgba(0,255,100,.15)', borderRadius: 3 }}>
          <span style={{ fontFamily: MONO, fontSize: 10, color: '#00ff64', letterSpacing: 1 }}>
            {'\u{2139}'} Using Ollama with locally hosted models. No API costs.
          </span>
        </div>
      </div>

      {/* SCANNER CONFIGURATION */}
      <div className="panel fade-up d2">
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div className="section-title" style={{ marginBottom: 20 }}>Scanner Configuration</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            { key: 'bandit_enabled', label: 'Bandit', desc: 'Python static analysis (AST-based)', icon: '\u{1F40D}' },
            { key: 'semgrep_enabled', label: 'Semgrep', desc: 'Multi-language pattern matching', icon: '\u{1F50E}' },
            { key: 'nuclei_enabled', label: 'Nuclei', desc: 'Template-based vulnerability scanner', icon: '\u{2622}' },
          ].map(scanner => (
            <div
              key={scanner.key}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '14px 16px', background: 'rgba(0,0,0,.2)', border: '1px solid rgba(232,0,29,.1)',
                borderRadius: 3, cursor: 'pointer',
              }}
              onClick={() => updateSetting('scanners', scanner.key, !settings.scanners[scanner.key as keyof typeof settings.scanners])}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 18 }}>{scanner.icon}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f0' }}>{scanner.label}</div>
                  <div style={{ fontFamily: MONO, fontSize: 10, color: '#666', letterSpacing: 1 }}>{scanner.desc}</div>
                </div>
              </div>
              <div style={{
                width: 44, height: 24, borderRadius: 12, position: 'relative', cursor: 'pointer', transition: 'all .2s',
                background: settings.scanners[scanner.key as keyof typeof settings.scanners] ? 'rgba(0,255,100,.3)' : 'rgba(255,255,255,.08)',
                border: `1px solid ${settings.scanners[scanner.key as keyof typeof settings.scanners] ? 'rgba(0,255,100,.5)' : 'rgba(255,255,255,.12)'}`,
              }}>
                <div style={{
                  width: 18, height: 18, borderRadius: '50%', position: 'absolute', top: 2, transition: 'all .2s',
                  left: settings.scanners[scanner.key as keyof typeof settings.scanners] ? 22 : 2,
                  background: settings.scanners[scanner.key as keyof typeof settings.scanners] ? '#00ff64' : '#555',
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SANDBOX CONFIGURATION */}
      <div className="panel fade-up d3">
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div className="section-title" style={{ marginBottom: 20 }}>Docker Sandbox</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>TIMEOUT (SECONDS)</label>
            <input
              className="zorix-input"
              type="number"
              value={settings.sandbox.sandbox_timeout}
              onChange={e => updateSetting('sandbox', 'sandbox_timeout', parseInt(e.target.value) || 60)}
              min={10}
              max={300}
            />
          </div>
          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>MEMORY LIMIT</label>
            <select
              className="zorix-input"
              value={settings.sandbox.sandbox_memory}
              onChange={e => updateSetting('sandbox', 'sandbox_memory', e.target.value)}
            >
              <option value="256m">256 MB</option>
              <option value="512m">512 MB</option>
              <option value="1g">1 GB</option>
              <option value="2g">2 GB</option>
            </select>
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>IMAGE</label>
            <input className="zorix-input" value={settings.sandbox.sandbox_image} disabled />
          </div>
        </div>
      </div>

      {/* DATABASE */}
      <div className="panel fade-up d4">
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div className="section-title" style={{ marginBottom: 20 }}>Database Connection</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'end' }}>
          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>TYPE</label>
            <input className="zorix-input" value={settings.database.type.toUpperCase()} disabled />
          </div>
          <button className="btn-outline" style={{ height: 42 }} onClick={testDbConnection}>
            Test Connection
          </button>
        </div>
        {dbTestResult && (
          <div style={{
            marginTop: 12, padding: '8px 12px', borderRadius: 3,
            fontFamily: MONO, fontSize: 11, letterSpacing: 1,
            background: dbTestResult.includes('success') ? 'rgba(0,255,100,.06)' : 'rgba(255,26,53,.06)',
            border: `1px solid ${dbTestResult.includes('success') ? 'rgba(0,255,100,.2)' : 'rgba(255,26,53,.2)'}`,
            color: dbTestResult.includes('success') ? '#00ff64' : '#ff1a35',
          }}>
            {dbTestResult}
          </div>
        )}
      </div>

      {/* NOTIFICATIONS */}
      <div className="panel fade-up d4">
        <div className="corner tl" /><div className="corner tr" /><div className="corner bl" /><div className="corner br" />
        <div className="section-title" style={{ marginBottom: 20 }}>Notifications</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>WEBHOOK URL</label>
            <input
              className="zorix-input"
              value={settings.notifications.default_webhook_url}
              onChange={e => updateSetting('notifications', 'default_webhook_url', e.target.value)}
              placeholder="https://hooks.slack.com/..."
            />
          </div>

          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '14px 16px', background: 'rgba(0,0,0,.2)', border: '1px solid rgba(232,0,29,.1)',
            borderRadius: 3, cursor: 'pointer',
          }}
            onClick={() => updateSetting('notifications', 'email_notifications', !settings.notifications.email_notifications)}
          >
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f0' }}>Email Notifications</div>
              <div style={{ fontFamily: MONO, fontSize: 10, color: '#666', letterSpacing: 1 }}>Receive alerts on analysis completion</div>
            </div>
            <div style={{
              width: 44, height: 24, borderRadius: 12, position: 'relative', transition: 'all .2s',
              background: settings.notifications.email_notifications ? 'rgba(0,255,100,.3)' : 'rgba(255,255,255,.08)',
              border: `1px solid ${settings.notifications.email_notifications ? 'rgba(0,255,100,.5)' : 'rgba(255,255,255,.12)'}`,
            }}>
              <div style={{
                width: 18, height: 18, borderRadius: '50%', position: 'absolute', top: 2, transition: 'all .2s',
                left: settings.notifications.email_notifications ? 22 : 2,
                background: settings.notifications.email_notifications ? '#00ff64' : '#555',
              }} />
            </div>
          </div>

          {settings.notifications.email_notifications && (
            <div>
              <label style={{ fontFamily: MONO, fontSize: 10, color: '#888', letterSpacing: 2, display: 'block', marginBottom: 6 }}>EMAIL ADDRESS</label>
              <input
                className="zorix-input"
                value={settings.notifications.notification_email}
                onChange={e => updateSetting('notifications', 'notification_email', e.target.value)}
                placeholder="admin@example.com"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
