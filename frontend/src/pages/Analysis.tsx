import { useState } from 'react'
import './Analysis.css'

export default function Analysis() {
  const [repoUrl, setRepoUrl] = useState('')
  const [vulnerabilityType, setVulnerabilityType] = useState('SQL_INJECTION')
  const [affectedFile, setAffectedFile] = useState('main.py')
  const [affectedLine, setAffectedLine] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState('')

  const vulnerabilityTypes = [
    'SQL_INJECTION',
    'XSS',
    'COMMAND_INJECTION',
    'PATH_TRAVERSAL',
    'CSRF',
    'XXEXML_INJECTION'
  ]

  const handleAnalyze = async (e) => {
    e.preventDefault()
    setError('')
    setResults(null)
    setLoading(true)

    try {
      const response = await fetch('/api/analysis/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          vulnerability_type: vulnerabilityType,
          affected_file: affectedFile,
          affected_line: affectedLine ? parseInt(affectedLine) : null,
          github_token: githubToken || null,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed')
      }

      setResults(data)
    } catch (err) {
      setError(err.message)
      console.error('Analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#ff0000',
      'HIGH': '#ff6600',
      'MEDIUM': '#ffcc00',
      'LOW': '#00cc00',
      'INFO': '#0099ff'
    }
    return colors[severity] || '#cccccc'
  }

  const getSeverityClass = (severity) => {
    return `severity-${severity?.toLowerCase() || 'unknown'}`
  }

  return (
    <div className="analysis-container">
      <div className="analysis-header">
        <h1>ðŸ” Vulnerability Analysis</h1>
        <p>Submit a GitHub repository for comprehensive security analysis</p>
      </div>

      <div className="analysis-content">
        {/* Analysis Form */}
        <div className="analysis-form-section">
          <h2>Analyze Repository</h2>
          
          <form onSubmit={handleAnalyze}>
            <div className="form-row">
              <div className="form-group full-width">
                <label>Repository URL <span className="required">*</span></label>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Vulnerability Type <span className="required">*</span></label>
                <select
                  value={vulnerabilityType}
                  onChange={(e) => setVulnerabilityType(e.target.value)}
                  disabled={loading}
                >
                  {vulnerabilityTypes.map((type) => (
                    <option key={type} value={type}>
                      {type.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Affected File <span className="required">*</span></label>
                <input
                  type="text"
                  value={affectedFile}
                  onChange={(e) => setAffectedFile(e.target.value)}
                  placeholder="e.g., main.py, app.js"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label>Line Number (optional)</label>
                <input
                  type="number"
                  value={affectedLine}
                  onChange={(e) => setAffectedLine(e.target.value)}
                  placeholder="e.g., 42"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group full-width">
                <label>GitHub Token (for private repos)</label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxx (optional)"
                  disabled={loading}
                />
                <small>Only used for accessing private repositories</small>
              </div>
            </div>

            {error && (
              <div className="error-alert">
                <span>âš ï¸ Error:</span> {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-analyze"
              disabled={loading || !repoUrl}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing... (this may take 1-2 minutes)
                </>
              ) : (
                'â–¶ Start Analysis'
              )}
            </button>
          </form>
        </div>

        {/* Results Section */}
        {results && (
          <div className="analysis-results-section">
            <h2>ðŸ“Š Analysis Results</h2>

            {results.status === 'completed' ? (
              <>
                {/* Severity Badge */}
                <div className="severity-section">
                  <div className={`severity-badge ${getSeverityClass(results.severity)}`}>
                    <div className="severity-value">{results.severity}</div>
                    <div className="severity-score">CVSS {results.score?.toFixed(1)}/10.0</div>
                  </div>
                </div>

                {/* Key Findings */}
                <div className="findings-grid">
                  <div className="finding-card">
                    <div className="finding-label">Vulnerability Confirmed</div>
                    <div className="finding-value">
                      {results.vulnerable ? '✓ YES' : '✗ NO'}
                    </div>
                  </div>

                  <div className="finding-card">
                    <div className="finding-label">Exploits Tested</div>
                    <div className="finding-value">{results.exploits_tested}</div>
                  </div>

                  <div className="finding-card">
                    <div className="finding-label">Confirmed Vulnerabilities</div>
                    <div className="finding-value">{results.vulnerabilities_confirmed || 0}</div>
                  </div>

                  <div className="finding-card">
                    <div className="finding-label">Confidence Score</div>
                    <div className="finding-value" style={{ color: (results.confidence_score || 0) > 50 ? '#00ff64' : '#ffc800' }}>
                      {results.confidence_score?.toFixed(1) || 0}%
                    </div>
                  </div>

                  <div className="finding-card">
                    <div className="finding-label">Environment Type</div>
                    <div className="finding-value code-text">{results.environment_type || 'auto'}</div>
                  </div>

                  <div className="finding-card">
                    <div className="finding-label">Analysis ID</div>
                    <div className="finding-value code-text">{results.analysis_id.substring(0, 8)}...</div>
                  </div>
                </div>

                {/* Successful Exploit Payloads */}
                {results.successful_payloads && results.successful_payloads.length > 0 && (
                  <div style={{ marginTop: '20px' }}>
                    <h3 style={{ color: '#00ff64', marginBottom: '16px', fontFamily: "'Share Tech Mono', monospace", letterSpacing: 1 }}>
                      ✓ Successful Exploit Payloads ({results.successful_payloads.length})
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {results.successful_payloads.map((payload: any, idx: number) => (
                        <div key={idx} style={{
                          border: '1px solid rgba(0, 255, 100, 0.25)',
                          borderRadius: '4px',
                          padding: '14px',
                          background: 'rgba(0, 255, 100, 0.04)'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: '#00ff64', letterSpacing: 1 }}>
                              [{payload.category}]
                            </span>
                            <span style={{ color: '#00ff64', fontWeight: 'bold', fontSize: '11px', fontFamily: "'Share Tech Mono', monospace" }}>
                              SUCCESS
                            </span>
                          </div>
                          <div style={{
                            fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#f0f0f0',
                            background: 'rgba(0, 0, 0, 0.3)', padding: '10px 12px', borderRadius: 3,
                            wordBreak: 'break-all' as const
                          }}>
                            Payload: {payload.payload}
                          </div>
                          {payload.result && (
                            <div style={{ fontSize: '11px', color: '#888', marginTop: '6px', fontFamily: "'Share Tech Mono', monospace" }}>
                              Result: {payload.result}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* All Exploit Execution Details (includes failed) */}
                {results.exploit_details && results.exploit_details.length > 0 && (
                  <div className="exploit-details-section" style={{ marginTop: '20px' }}>
                    <h3 style={{ color: '#e8001d', marginBottom: '16px' }}>All Payload Execution Results ({results.exploit_details.length})</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {results.exploit_details.map((exploit: any, idx: number) => (
                        <div key={idx} style={{
                          border: `1px solid ${exploit.exploit_success ? 'rgba(0, 255, 100, 0.2)' : 'rgba(232, 0, 29, 0.2)'}`,
                          borderRadius: '4px',
                          padding: '10px 12px',
                          background: exploit.exploit_success ? 'rgba(0, 255, 100, 0.03)' : 'rgba(0, 0, 0, 0.15)',
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        }}>
                          <div style={{ flex: 1 }}>
                            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: '#888', marginRight: 8 }}>
                              [{exploit.payload_category || exploit.exploit_type || 'unknown'}]
                            </span>
                            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 12, color: '#ccc' }}>
                              {(exploit.payload_string || exploit.exploit_type || '').substring(0, 60)}
                            </span>
                          </div>
                          <span style={{
                            color: exploit.exploit_success || exploit.vulnerable ? '#00ff64' : '#e8001d',
                            fontWeight: 'bold', fontSize: '10px', fontFamily: "'Share Tech Mono', monospace",
                            marginLeft: 12,
                          }}>
                            {exploit.exploit_success || exploit.vulnerable ? '✓ VULNERABLE' : '✗ SAFE'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Report Link */}
                {results.report_url && (
                  <div className="report-section">
                    <h3>ðŸ“„ Full Report</h3>
                    <p>Download the detailed security analysis report:</p>
                    <a
                      href={results.report_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-report"
                    >
                      ðŸ“¥ Download HTML Report
                    </a>
                  </div>
                )}

                {/* Additional Actions */}
                <div className="actions-section">
                  <button
                    onClick={() => setResults(null)}
                    className="btn btn-secondary"
                  >
                    New Analysis
                  </button>
                </div>
              </>
            ) : (
              <div className="error-result">
                <h3>âš ï¸ Analysis Failed</h3>
                <p>{results.error || 'An unknown error occurred'}</p>
              </div>
            )}
          </div>
        )}

        {/* Info Section */}
        <div className="info-section">
          <h3>ðŸ“– How It Works</h3>
          <div className="pipeline-steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <strong>Fetch Repository</strong>
                <p>Download source code from GitHub</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <strong>AI Analysis</strong>
                <p>Perform root cause analysis with local LLM</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <strong>Generate Exploits</strong>
                <p>Create realistic vulnerability test cases</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <strong>Execute & Validate</strong>
                <p>Run exploits in isolated Docker sandbox</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">5</div>
              <div className="step-content">
                <strong>Score & Report</strong>
                <p>Calculate CVSS score and generate report</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

