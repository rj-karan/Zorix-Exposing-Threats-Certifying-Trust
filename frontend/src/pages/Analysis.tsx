import { useState } from 'react'
import './Analysis.css'

export default function Analysis() {
  const [repoUrl, setRepoUrl] = useState('')
  const [vulnerabilityType, setVulnerabilityType] = useState('SQL_INJECTION')
  const [affectedFile, setAffectedFile] = useState('main.py')
  const [affectedLine, setAffectedLine] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
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
        <h1>🔍 Vulnerability Analysis</h1>
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
                <span>⚠️ Error:</span> {error}
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
                '▶ Start Analysis'
              )}
            </button>
          </form>
        </div>

        {/* Results Section */}
        {results && (
          <div className="analysis-results-section">
            <h2>📊 Analysis Results</h2>

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
                    <div className="finding-label">Analysis ID</div>
                    <div className="finding-value code-text">{results.analysis_id.substring(0, 8)}...</div>
                  </div>
                </div>

                {/* Report Link */}
                {results.report_url && (
                  <div className="report-section">
                    <h3>📄 Full Report</h3>
                    <p>Download the detailed security analysis report:</p>
                    <a
                      href={results.report_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-report"
                    >
                      📥 Download HTML Report
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
                <h3>⚠️ Analysis Failed</h3>
                <p>{results.error || 'An unknown error occurred'}</p>
              </div>
            )}
          </div>
        )}

        {/* Info Section */}
        <div className="info-section">
          <h3>📖 How It Works</h3>
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
