import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Zap, ArrowLeft, Mail, KeyRound, ShieldCheck } from 'lucide-react';
import * as api from '../api';

// ── Views ──────────────────────────────────────────────────────────────────────
// 'login'   → sign-in form
// 'register' → create-account form
// 'forgot'   → step 1: enter email
// 'verify'   → step 2: enter OTP + new password

export default function AuthPage({ onLogin }) {
  const [view, setView]         = useState('login');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const [showPass, setShowPass] = useState(false);
  const [showNew, setShowNew]   = useState(false);
  const [institutes, setInstitutes] = useState([]);

  // Login / Register form state
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', role: 'student', institute_id: '', phone: '',
  });

  // Forgot-password state
  const [fpEmail, setFpEmail]     = useState('');
  const [fpCode, setFpCode]       = useState('');
  const [fpNewPass, setFpNewPass] = useState('');

  const navigate = useNavigate();

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const reset = () => { setError(''); setSuccess(''); };

  const loadInstitutes = async () => {
    if (institutes.length) return;
    try { const res = await api.getInstitutes(); setInstitutes(res.data); } catch {}
  };

  // ── Login / Register ──────────────────────────────────────────────────────
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    reset(); setLoading(true);
    try {
      if (view === 'login') {
        const res = await api.login(form.email, form.password);
        localStorage.setItem('hazeon_token', res.data.access_token);
        localStorage.setItem('hazeon_user', JSON.stringify(res.data.user));
        onLogin(res.data.user);
        navigate('/dashboard');
      } else {
        await api.register({
          email: form.email, password: form.password,
          full_name: form.full_name, role: form.role,
          institute_id: form.institute_id ? parseInt(form.institute_id) : null,
          phone: form.phone || null,
        });
        setView('login');
        setSuccess('Account created! Please sign in.');
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Try again.');
    }
    setLoading(false);
  };

  // ── Forgot Password: Step 1 — send OTP ───────────────────────────────────
  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    reset(); setLoading(true);
    try {
      await api.forgotPassword(fpEmail);
      setSuccess('Check your email for the 6-digit reset code.');
      setView('verify');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Try again.');
    }
    setLoading(false);
  };

  // ── Forgot Password: Step 2 — verify OTP + set new pass ──────────────────
  const handleResetSubmit = async (e) => {
    e.preventDefault();
    reset();
    if (fpNewPass.length < 8) { setError('Password must be at least 8 characters.'); return; }
    setLoading(true);
    try {
      await api.resetPassword(fpEmail, fpCode, fpNewPass);
      setSuccess('Password updated! You can now sign in.');
      setView('login');
      setFpEmail(''); setFpCode(''); setFpNewPass('');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid or expired code. Try again.');
    }
    setLoading(false);
  };

  // ── Helpers ───────────────────────────────────────────────────────────────
  const goBack = (target) => { reset(); setView(target); };

  const title = {
    login:    'Welcome back',
    register: 'Create account',
    forgot:   'Reset password',
    verify:   'Enter reset code',
  }[view];

  const subtitle = {
    login:    'Sign in to your institute dashboard',
    register: 'Join your coaching institute on Hazeon',
    forgot:   "Enter your email and we'll send a reset code",
    verify:   `Code sent to ${fpEmail} — check your inbox`,
  }[view];

  return (
    <div className="auth-container">
      <div className="auth-card animate-in">

        {/* Logo */}
        <div className="flex items-center gap-3 mb-6">
          <div className="logo-icon">HZ</div>
          <div>
            <div className="logo-text">Hazeon AI</div>
            <div className="logo-sub">UPSC · HCS Evaluator</div>
          </div>
        </div>

        {/* Back arrow for forgot / verify */}
        {(view === 'forgot' || view === 'verify') && (
          <button
            onClick={() => goBack(view === 'verify' ? 'forgot' : 'login')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '0.85rem', padding: '0 0 12px',
            }}
          >
            <ArrowLeft size={14} /> Back
          </button>
        )}

        <h2 className="mb-1">{title}</h2>
        <p className="text-muted text-sm mb-6">{subtitle}</p>

        {/* Alerts */}
        {error && (
          <div className="mb-4" style={{
            background: 'var(--error-subtle)', border: '1px solid rgba(255,77,106,0.3)',
            borderRadius: 'var(--radius-md)', padding: '10px 14px',
            fontSize: '0.85rem', color: 'var(--error)',
          }}>
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4" style={{
            background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: 'var(--radius-md)', padding: '10px 14px',
            fontSize: '0.85rem', color: '#4ade80',
          }}>
            {success}
          </div>
        )}

        {/* ── LOGIN FORM ─────────────────────────────────────────────────── */}
        {view === 'login' && (
          <form onSubmit={handleAuthSubmit} className="flex-col gap-4 flex">
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" placeholder="you@institute.com"
                value={form.email} onChange={set('email')} required />
            </div>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                Password
                <button type="button" onClick={() => { reset(); setFpEmail(form.email); setView('forgot'); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer',
                           color: 'var(--primary)', fontWeight: 500, fontSize: '0.82rem' }}>
                  Forgot password?
                </button>
              </label>
              <div style={{ position: 'relative' }}>
                <input className="form-input" type={showPass ? 'text' : 'password'}
                  placeholder="••••••••" value={form.password} onChange={set('password')}
                  required style={{ paddingRight: 40 }} />
                <button type="button" onClick={() => setShowPass(p => !p)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', padding: 0,
                }}>
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button className="btn btn-primary btn-lg w-full mt-2" type="submit" disabled={loading}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Signing in...</>
                       : 'Sign In'}
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ──────────────────────────────────────────────── */}
        {view === 'register' && (
          <form onSubmit={handleAuthSubmit} className="flex-col gap-4 flex">
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" placeholder="Priya Sharma"
                value={form.full_name} onChange={set('full_name')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" placeholder="you@institute.com"
                value={form.email} onChange={set('email')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <div style={{ position: 'relative' }}>
                <input className="form-input" type={showPass ? 'text' : 'password'}
                  placeholder="Min 8 characters" value={form.password} onChange={set('password')}
                  required style={{ paddingRight: 40 }} />
                <button type="button" onClick={() => setShowPass(p => !p)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', padding: 0,
                }}>
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Role</label>
              <select className="form-input" value={form.role} onChange={set('role')}>
                <option value="student">Student</option>
                <option value="institute_admin">Institute Admin</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Institute</label>
              <select className="form-input" value={form.institute_id}
                onChange={set('institute_id')} onFocus={loadInstitutes}>
                <option value="">Select your institute</option>
                {institutes.map(i => (
                  <option key={i.id} value={i.id}>{i.name} — {i.city}</option>
                ))}
              </select>
            </div>
            <button className="btn btn-primary btn-lg w-full mt-2" type="submit" disabled={loading}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Creating...</>
                       : 'Create Account'}
            </button>
          </form>
        )}

        {/* ── FORGOT PASSWORD: Step 1 — Enter email ──────────────────────── */}
        {view === 'forgot' && (
          <form onSubmit={handleForgotSubmit} className="flex-col gap-4 flex">
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Mail size={13} /> Email Address
              </label>
              <input className="form-input" type="email" placeholder="you@institute.com"
                value={fpEmail} onChange={e => setFpEmail(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-lg w-full mt-2" type="submit" disabled={loading}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Sending...</>
                       : 'Send Reset Code'}
            </button>
          </form>
        )}

        {/* ── FORGOT PASSWORD: Step 2 — OTP + new password ───────────────── */}
        {view === 'verify' && (
          <form onSubmit={handleResetSubmit} className="flex-col gap-4 flex">
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <KeyRound size={13} /> 6-Digit Code
              </label>
              <input
                className="form-input"
                placeholder="000000"
                value={fpCode}
                onChange={e => setFpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required
                maxLength={6}
                style={{ letterSpacing: '6px', fontSize: '1.25rem', textAlign: 'center', fontFamily: 'monospace' }}
              />
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Code expires in 15 minutes.{' '}
                <button type="button" onClick={() => { reset(); setView('forgot'); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer',
                           color: 'var(--primary)', fontSize: '0.78rem' }}>
                  Resend
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldCheck size={13} /> New Password
              </label>
              <div style={{ position: 'relative' }}>
                <input className="form-input" type={showNew ? 'text' : 'password'}
                  placeholder="Min 8 characters" value={fpNewPass}
                  onChange={e => setFpNewPass(e.target.value)} required style={{ paddingRight: 40 }} />
                <button type="button" onClick={() => setShowNew(p => !p)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', padding: 0,
                }}>
                  {showNew ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button className="btn btn-primary btn-lg w-full mt-2" type="submit"
              disabled={loading || fpCode.length < 6}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Resetting...</>
                       : 'Set New Password'}
            </button>
          </form>
        )}

        {/* ── Toggle Login / Register ─────────────────────────────────────── */}
        {(view === 'login' || view === 'register') && (
          <>
            <div className="divider" style={{ margin: '20px 0' }} />
            <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {view === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button onClick={() => { reset(); setView(view === 'login' ? 'register' : 'login'); }}
                style={{ background: 'none', border: 'none', cursor: 'pointer',
                         color: 'var(--primary)', fontWeight: 600 }}>
                {view === 'login' ? 'Register' : 'Sign In'}
              </button>
            </div>

            <div className="mt-4" style={{ textAlign: 'center' }}>
              <div className="text-xs text-muted" style={{ display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 6 }}>
                <Zap size={11} style={{ color: 'var(--accent)' }} />
                Demo: admin@hazeon.com / admin123
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
