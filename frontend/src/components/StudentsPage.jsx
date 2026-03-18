import { useState, useEffect, useMemo } from 'react';
import { Users, Mail, TrendingUp, TrendingDown, FileText, Search, ArrowRight, Award, Minus, XCircle } from 'lucide-react';
import * as api from '../api';

function scoreColor(s) {
  if (s >= 7.5) return 'var(--success)';
  if (s >= 5.5) return 'var(--warning)';
  return 'var(--error)';
}

function TrendIcon({ avg }) {
  if (avg >= 7) return <TrendingUp size={13} style={{ color: 'var(--success)' }} />;
  if (avg >= 5.5) return <Minus size={13} style={{ color: 'var(--warning)' }} />;
  return <TrendingDown size={13} style={{ color: 'var(--error)' }} />;
}

export default function StudentsPage({ onNavigate }) {
  const [students, setStudents] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [search,   setSearch]   = useState('');
  const [sortBy,   setSortBy]   = useState('name');

  useEffect(() => {
    api.getStudents()
      .then(r => setStudents(r.data))
      .catch(err => setError(err?.response?.data?.detail || 'Failed to load students. Please retry.'))
      .finally(() => setLoading(false));
  }, []);

  // Memoised — only recomputes when students/search/sortBy change, not on every render
  const filtered = useMemo(() => students
    .filter(s => {
      const q = search.toLowerCase();
      return s.name?.toLowerCase().includes(q) || s.email?.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      if (sortBy === 'score')       return (b.avg_score || 0) - (a.avg_score || 0);
      if (sortBy === 'submissions') return (b.total_submissions || 0) - (a.total_submissions || 0);
      return (a.name || '').localeCompare(b.name || '');
    }), [students, search, sortBy]);

  const avgScore = useMemo(() =>
    students.length
      ? students.reduce((acc, s) => acc + (s.avg_score || 0), 0) / students.length
      : 0,
    [students]);

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Users size={22} /> Students</h1>
          <p className="page-description">{students.length} enrolled students in your institute</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => onNavigate?.('upload')}>
          <ArrowRight size={13} /> Evaluate Answer
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Students',      value: students.length,  color: 'var(--primary)' },
          { label: 'Avg Batch Score',      value: `${avgScore.toFixed(1)}/10`, color: avgScore >= 7 ? 'var(--success)' : 'var(--warning)' },
          { label: 'On Track (≥6)',        value: students.filter(s => (s.avg_score || 0) >= 6).length, color: 'var(--success)' },
          { label: 'Need Attention (<5.5)', value: students.filter(s => (s.avg_score || 0) < 5.5).length, color: 'var(--error)' },
        ].map(s => (
          <div key={s.label} className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card mb-4" style={{ padding: '12px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="search-box" style={{ flex: 1 }}>
            <Search size={13} style={{ color: 'var(--text-muted)' }} />
            <input placeholder="Search by name or email..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <select className="form-input" style={{ width: 170 }} value={sortBy} onChange={e => setSortBy(e.target.value)}>
            <option value="name">Sort: Name</option>
            <option value="score">Sort: Score (High → Low)</option>
            <option value="submissions">Sort: Submissions</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: 200 }}>
          <div className="spinner" style={{ width: 24, height: 24 }} />
        </div>
      ) : error ? (
        <div className="card empty-state">
          <XCircle size={40} style={{ opacity: 0.4, color: 'var(--error)' }} />
          <p>{error}</p>
          <button className="btn btn-primary btn-sm mt-3" onClick={() => {
            setLoading(true); setError('');
            api.getStudents().then(r => setStudents(r.data)).catch(err => setError(err?.response?.data?.detail || 'Failed to load students.')).finally(() => setLoading(false));
          }}>Retry</button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="card empty-state">
          <Users size={40} style={{ opacity: 0.2 }} />
          <p>No students found.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Student</th>
                <th>Email</th>
                <th>Submissions</th>
                <th>Avg Score</th>
                <th>Trend</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const avg = s.avg_score || 0;
                return (
                  <tr key={s.id}>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{i + 1}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
                          background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.65rem', fontWeight: 700, color: 'white'
                        }}>
                          {s.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
                        </div>
                        <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{s.name}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        <Mail size={11} />{s.email}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        <FileText size={12} style={{ color: 'var(--text-muted)' }} />
                        <span style={{ fontSize: '0.875rem' }}>{s.total_submissions}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ color: scoreColor(avg), fontWeight: 700, fontSize: '0.9rem' }}>{avg.toFixed(1)}</span>
                        <div style={{ width: 48, height: 4, borderRadius: 2, background: 'var(--bg-elevated)', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${avg * 10}%`, background: scoreColor(avg), borderRadius: 2 }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.8rem' }}>
                        <TrendIcon avg={avg} />
                        <span style={{ color: avg >= 7 ? 'var(--success)' : avg >= 5.5 ? 'var(--text-muted)' : 'var(--error)' }}>
                          {avg >= 7 ? 'Strong' : avg >= 5.5 ? 'Average' : 'At Risk'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${avg >= 7 ? 'badge-success' : avg >= 5.5 ? 'badge-warning' : 'badge-error'}`} style={{ fontSize: '0.65rem' }}>
                        {avg >= 7 ? 'On Track' : avg >= 5.5 ? 'Monitor' : 'Needs Help'}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => onNavigate?.('submissions')}>
                        <Award size={13} /> View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
