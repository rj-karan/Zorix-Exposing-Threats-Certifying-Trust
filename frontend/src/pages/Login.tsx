import { useState, FormEvent } from 'react'
import './Auth.css'

interface LoginProps {
  onLoginSuccess?: () => void
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')

  const doLogin = async (loginEmail: string, loginPassword: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginEmail, password: loginPassword }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed')
    }

    // Store token and user info
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user_email', loginEmail)
    localStorage.setItem('user_role', 'admin')

    if (onLoginSuccess) onLoginSuccess()
  }

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await doLogin(email, password)
    } catch (err) {
      setError((err as Error).message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccessMsg('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      // Auto-login after successful registration
      await doLogin(email, password)
    } catch (err) {
      setError((err as Error).message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async () => {
    setError('')
    setLoading(true)

    try {
      // First try to register the demo account (ignore if already exists)
      try {
        await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'demo@zorix.local', password: 'demo1234' }),
        })
      } catch {
        // Ignore registration errors (account may already exist)
      }

      // Now login with demo credentials
      await doLogin('demo@zorix.local', 'demo1234')
    } catch (err) {
      setError((err as Error).message || 'Demo login failed')
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (newMode: 'login' | 'register') => {
    setMode(newMode)
    setError('')
    setSuccessMsg('')
    setConfirmPassword('')
  }

  return (
    <div className="auth-container">
      {/* Background Effects */}
      <div className="radial-bg" />
      <div className="grid-bg" />

      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-title">
            🛡️ ZORIX
          </div>
          <div className="auth-subtitle">
            {mode === 'login' ? 'Exposing Threats, Certifying Trust' : 'Create Your Security Account'}
          </div>
        </div>

        {mode === 'login' ? (
          <>
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
                  placeholder="••••••••"
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
              {loading ? 'Connecting...' : 'Try Demo Credentials'}
            </button>

            <div className="auth-footer">
              <p>Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); switchMode('register') }}>Register here</a></p>
            </div>
          </>
        ) : (
          <>
            <form onSubmit={handleRegister} className="auth-form">
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
                  placeholder="••••••••"
                  required
                  disabled={loading}
                />
                <small>Minimum 8 characters</small>
              </div>

              <div className="form-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                />
              </div>

              {error && <div className="error-message">{error}</div>}
              {successMsg && <div className="error-message" style={{ borderLeftColor: '#00ff64', color: '#00ff64', background: 'rgba(0,255,100,.1)' }}>{successMsg}</div>}

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Create Account & Login'}
              </button>
            </form>

            <div className="auth-footer">
              <p>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); switchMode('login') }}>Log in here</a></p>
            </div>
          </>
        )}
      </div>

      {/* Animated background elements */}
      <div className="floating-element top-left" />
      <div className="floating-element top-right" />
      <div className="floating-element bottom-left" />
      <div className="floating-element bottom-right" />
    </div>
  )
}
