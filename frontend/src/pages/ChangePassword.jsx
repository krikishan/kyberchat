import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { KeyRound, CheckCircle2, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { api, setToken } from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

export default function ChangePassword() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNext, setShowNext] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const { user, refresh } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (next !== confirm) { setError('New passwords do not match.'); return }
    try {
      const result = await api.changePassword(current, next)
      setToken(result.token)
      setSuccess(true)
      await refresh()
      setTimeout(() => navigate('/'), 1000)
    } catch (err) {
      setError(err.message)
    }
  }

  const isForced = user?.must_change_password

  return (
    <Layout>
      <h1 className="page-title" style={{ marginBottom: 6 }}>
        {isForced ? 'Set Your Password' : 'Change Password'}
      </h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
        {isForced
          ? 'Your account was created with a temporary password. Please set a permanent password before continuing.'
          : 'Choose a strong password. Minimum 10 characters with at least one uppercase letter, lowercase letter, and digit.'}
      </p>

      <div style={{ maxWidth: 420 }}>
        <form className="card" style={{ padding: 24 }} onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="field">
              <label className="label" htmlFor="cp-current">Current password</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  id="cp-current"
                  className="input"
                  type={showCurrent ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={current}
                  onChange={e => setCurrent(e.target.value)}
                  style={{ paddingRight: 40, width: '100%' }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(prev => !prev)}
                  style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)',
                    display: 'flex', alignItems: 'center', padding: 5
                  }}
                  aria-label={showCurrent ? 'Hide password' : 'Show password'}
                >
                  {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div className="field">
              <label className="label" htmlFor="cp-new">New password</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  id="cp-new"
                  className="input"
                  type={showNext ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={next}
                  onChange={e => setNext(e.target.value)}
                  style={{ paddingRight: 40, width: '100%' }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowNext(prev => !prev)}
                  style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)',
                    display: 'flex', alignItems: 'center', padding: 5
                  }}
                  aria-label={showNext ? 'Hide password' : 'Show password'}
                >
                  {showNext ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div className="field">
              <label className="label" htmlFor="cp-confirm">Confirm new password</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  id="cp-confirm"
                  className="input"
                  type={showConfirm ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  style={{ paddingRight: 40, width: '100%' }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(prev => !prev)}
                  style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)',
                    display: 'flex', alignItems: 'center', padding: 5
                  }}
                  aria-label={showConfirm ? 'Hide password' : 'Show password'}
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="alert alert-error" role="alert">
                <AlertCircle size={14} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="alert alert-success" role="status">
                <CheckCircle2 size={14} style={{ flexShrink: 0 }} />
                <span>Password updated — redirecting…</span>
              </div>
            )}

            <button className="btn btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center' }}>
              <KeyRound size={14} />
              {isForced ? 'Set Password' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  )
}
