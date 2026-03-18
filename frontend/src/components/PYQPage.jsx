import { useState, useEffect } from 'react';
import {
  BookOpen, Search, Filter, ArrowRight, Clock, Tag, ChevronDown, X,
} from 'lucide-react';
import * as api from '../api';

const DIFFICULTY_COLOR = {
  easy:     'var(--success)',
  moderate: 'var(--warning)',
  hard:     'var(--error)',
};

/* ── Main Page ─────────────────────────────────────────── */
export default function PYQPage({ onNavigate }) {
  const [questions, setQuestions] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(false);
  const [retryKey,  setRetryKey]  = useState(0);
  const [search,    setSearch]    = useState('');
  const [subject,   setSubject]   = useState('');
  const [examType,  setExamType]  = useState('');
  const [expanded,  setExpanded]  = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(false);
    api.getQuestions()
      .then(r => setQuestions(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [retryKey]);

  // ── Filtering ─────────────────────────────────────────
  const filtered = questions.filter(q => {
    const matchSearch  = !search  || q.text.toLowerCase().includes(search.toLowerCase()) ||
                         (q.topic || '').toLowerCase().includes(search.toLowerCase());
    const matchSubject = !subject  || q.subject === subject;
    const matchExam    = !examType || q.exam_type === examType;
    return matchSearch && matchSubject && matchExam;
  });

  const subjects       = [...new Set(questions.map(q => q.subject))];
  const subjectCounts  = filtered.reduce((acc, q) => { acc[q.subject] = (acc[q.subject] || 0) + 1; return acc; }, {});

  return (
    <div className="animate-in">
      {/* ── Page Header ─────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title"><BookOpen size={22} /> PYQ Bank</h1>
          <p className="page-description">{questions.length} previous year questions — HCS &amp; UPSC Mains</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="badge badge-primary">{filtered.filter(q => q.exam_type === 'HCS').length} HCS</span>
          <span className="badge badge-accent">{filtered.filter(q => q.exam_type === 'UPSC').length} UPSC</span>
        </div>
      </div>

      {/* ── Stats Row ───────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Questions', value: questions.length,                                                                                              color: 'var(--primary)' },
          { label: 'Subjects',        value: subjects.length,                                                                                               color: 'var(--accent)' },
          { label: 'Hard Questions',  value: questions.filter(q => q.difficulty === 'hard').length,                                                         color: 'var(--error)' },
          { label: 'Avg Marks',       value: questions.length ? Math.round(questions.reduce((a,q) => a + q.marks, 0) / questions.length) + 'M' : '—',      color: 'var(--warning)' },
        ].map(s => (
          <div key={s.label} className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Filters ─────────────────────────────── */}
      <div className="card mb-4" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div className="search-box" style={{ flex: 1, minWidth: 200 }}>
            <Search size={13} style={{ color: 'var(--text-muted)' }} />
            <input placeholder="Search questions or topics..." value={search} onChange={e => setSearch(e.target.value)} style={{ width: '100%' }} />
          </div>
          <Filter size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <select className="form-input" style={{ width: 170 }} value={subject} onChange={e => setSubject(e.target.value)}>
            <option value="">All Subjects</option>
            {subjects.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="form-input" style={{ width: 130 }} value={examType} onChange={e => setExamType(e.target.value)}>
            <option value="">All Exams</option>
            <option value="HCS">HCS</option>
            <option value="UPSC">UPSC</option>
          </select>
          {(search || subject || examType) && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setSubject(''); setExamType(''); }}>
              <X size={12} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Subject quick-filter tabs ────────────── */}
      {!subject && Object.keys(subjectCounts).length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          {Object.entries(subjectCounts).map(([sub, count]) => (
            <button key={sub} className="btn btn-secondary btn-sm" onClick={() => setSubject(sub)} style={{ fontSize: '0.72rem' }}>
              <Tag size={11} /> {sub.split(' - ')[0]}
              <span className="badge badge-neutral" style={{ marginLeft: 4, fontSize: '0.62rem' }}>{count}</span>
            </button>
          ))}
        </div>
      )}

      {/* ── Content ─────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center" style={{ height: 200 }}>
          <div className="spinner" style={{ width: 24, height: 24 }} />
        </div>
      ) : error ? (
        <div className="card empty-state">
          <BookOpen size={40} style={{ opacity: 0.2 }} />
          <p>Failed to load questions.</p>
          <button className="btn btn-primary btn-sm mt-3" onClick={() => setRetryKey(k => k + 1)}>Retry</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(q => (
            <div
              key={q.id}
              className="card"
              style={{ padding: '16px 20px', cursor: 'pointer', position: 'relative' }}
              onClick={() => setExpanded(expanded === q.id ? null : q.id)}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Badges */}
                  <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span className="badge badge-primary">{q.subject}</span>
                    <span className="badge badge-neutral">{q.exam_type} {q.year}</span>
                    <span className="badge badge-neutral">{q.marks}M</span>
                    <span className="badge" style={{
                      background: `${DIFFICULTY_COLOR[q.difficulty]}18`,
                      color: DIFFICULTY_COLOR[q.difficulty],
                      border: `1px solid ${DIFFICULTY_COLOR[q.difficulty]}30`,
                    }}>{q.difficulty}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: 4 }}>
                      <Clock size={11} /> {q.word_limit} words
                    </span>
                    {q.topic && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        {q.topic}
                      </span>
                    )}
                  </div>

                  {/* Question text */}
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: expanded === q.id ? 'var(--text-primary)' : 'var(--text-secondary)', margin: 0 }}>
                    {q.text}
                  </p>

                  {/* Expanded key points */}
                  {expanded === q.id && q.model_answer_points?.length > 0 && (
                    <div
                      style={{ marginTop: 14, padding: '12px 16px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--warning)' }}
                      onClick={e => e.stopPropagation()}
                    >
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--warning)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                        Key Points to Cover
                      </div>
                      {q.model_answer_points.map((pt, i) => (
                        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                          <span style={{ color: 'var(--warning)', fontWeight: 700, fontSize: '0.75rem', flexShrink: 0 }}>{i + 1}.</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{pt}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action buttons column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => onNavigate?.('upload')}
                  >
                    Practice <ArrowRight size={13} />
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem' }}
                    onClick={() => setExpanded(expanded === q.id ? null : q.id)}>
                    <ChevronDown size={12} style={{ transform: expanded === q.id ? 'rotate(180deg)' : 'none', transition: '0.2s' }} />
                    {expanded === q.id ? 'Hide' : 'Key Points'}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {filtered.length === 0 && !loading && (
            <div className="card empty-state">
              <BookOpen size={36} style={{ opacity: 0.2 }} />
              <p>{questions.length === 0
                ? 'No questions in the bank yet. Contact your admin to add questions.'
                : 'No questions match your filters.'
              }</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
