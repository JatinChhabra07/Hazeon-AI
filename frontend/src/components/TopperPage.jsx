import { useState, useEffect } from 'react';
import { Trophy, Filter, Eye, X } from 'lucide-react';
import * as api from '../api';

export default function TopperPage() {
  const [toppers,  setToppers]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(false);
  const [subject,  setSubject]  = useState('');
  const [viewing,  setViewing]  = useState(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(false);
    api.getTopperAnswers({ subject: subject || undefined })
      .then(r => setToppers(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [subject, retryKey]);

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Trophy size={22} /> Topper Database</h1>
          <p className="page-description">Reference answers from HCS/UPSC toppers — used for AI benchmarking</p>
        </div>
        <div className="flex items-center gap-3">
          <Filter size={14} className="text-muted" />
          <select className="form-input" style={{ width: 180 }} value={subject} onChange={e => setSubject(e.target.value)}>
            <option value="">All Subjects</option>
            {['GS1 - Society','GS2 - Governance','GS2 - Polity','GS3 - Economy','GS3 - Environment','GS4 - Ethics'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: 200 }}>
          <div className="spinner" style={{ width: 24, height: 24 }} />
        </div>
      ) : error ? (
        <div className="card empty-state">
          <X size={40} style={{ opacity: 0.4, color: 'var(--error)' }} />
          <p>Failed to load topper answers.</p>
          <button className="btn btn-primary btn-sm mt-3" onClick={() => setRetryKey(k => k + 1)}>Retry</button>
        </div>
      ) : toppers.length === 0 ? (
        <div className="card empty-state">
          <Trophy size={40} style={{ opacity: 0.2 }} />
          <p>No topper answers loaded yet. Upload answers via the API.</p>
        </div>
      ) : (
        <div className="grid-3 gap-4">
          {toppers.map(t => (
            <div key={t.id} className="card" style={{ cursor: 'pointer' }} onClick={() => setViewing(t)}>
              <div className="flex items-center justify-between mb-3">
                <span className="badge badge-warning">Rank #{t.rank || '?'}</span>
                <span className="badge badge-neutral">{t.exam_type} {t.year}</span>
              </div>
              {t.subject && <div className="badge badge-primary mb-3">{t.subject}</div>}
              <p className="text-sm text-muted" style={{ lineHeight: 1.6, marginBottom: 12 }}>
                {t.ocr_text?.substring(0, 100) || 'No preview available'}...
              </p>
              <div className="flex items-center justify-between">
                <span style={{ color: 'var(--warning)', fontWeight: 700, fontSize: '0.9rem' }}>
                  Score: {t.score?.toFixed(1) || '?'}/10
                </span>
                <button className="btn btn-ghost btn-sm"><Eye size={13} /> View</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {viewing && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: 24
        }} onClick={() => setViewing(null)}>
          <div className="card" style={{ maxWidth: 700, width: '100%', maxHeight: '80vh', overflow: 'auto' }}
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Trophy size={18} color="var(--warning)" />
                <h3>Topper Answer — Rank #{viewing.rank}</h3>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setViewing(null)}><X size={14} /></button>
            </div>
            <div className="flex gap-2 mb-4">
              {viewing.subject && <span className="badge badge-primary">{viewing.subject}</span>}
              <span className="badge badge-warning">Score: {viewing.score?.toFixed(1)}/10</span>
              <span className="badge badge-neutral">{viewing.exam_type} {viewing.year}</span>
            </div>
            <div style={{
              background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)',
              padding: 18, fontSize: '0.875rem', lineHeight: 1.8,
              color: 'var(--text-secondary)', whiteSpace: 'pre-wrap'
            }}>
              {viewing.ocr_text || 'No text available.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
