import { useState, FormEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import './Auth.css'

interface LoginProps {
  onLoginSuccess?: () => void
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      // Store token
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user_email', email)

      if (onLoginSuccess) onLoginSuccess()
      navigate('/dashboard')
    } catch (err) {
      setError((err as Error).message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async () => {
    // Demo credentials
    await handleLogin({
      preventDefault: () => {},
      target: {
        email: { value: 'demo@zorix.local' },
        password: { value: 'demo123' },
      },
    } as any)
  }

  return (
    <div className="auth-container">
      {/* Background Effects */}
      <div className="radial-bg" />
      <div className="grid-bg" />

      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-title">
            ðŸ›¡ï¸ ZORIX
          </div>
          <div className="auth-subtitle">
            Exposing Threats, Certifying Trust
          </div>
        </div>

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢"
              required
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className="auth-divider">
          <span>or</span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={handleDemoLogin}
          disabled={loading}
        >
          Try Demo Credentials
        </button>

        <div className="auth-footer">
          <p>Don't have an account? <a href="/register">Register here</a></p>
        </div>
      </div>

      {/* Animated background elements */}
      <div className="floating-element top-left" />
      <div className="floating-element top-right" />
      <div className="floating-element bottom-left" />
      <div className="floating-element bottom-right" />
    </div>
  )
}

