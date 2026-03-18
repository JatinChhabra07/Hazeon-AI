import { useState, useEffect } from 'react';
import { Eye, FileText, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import * as api from '../api';
import EvaluationResult from './EvaluationResult';

function statusBadge(status) {
  const map = {
    evaluated: ['badge-success', <CheckCircle2 size={10} />],
    processing: ['badge-warning', <Loader2 size={10} />],
    failed:     ['badge-error',   <XCircle size={10} />],
    uploaded:   ['badge-neutral', <Clock size={10} />],
  };
  const [cls, icon] = map[status] || ['badge-neutral', null];
  return <span className={`badge ${cls}`}>{icon}{status}</span>;
}

export default function SubmissionsPage() {
  const [subs,   setSubs]   = useState([]);
  const [loading,setLoading]= useState(true);
  const [error,  setError]  = useState(false);
  const [viewing,setViewing]= useState(null);

  const load = () => {
    setLoading(true);
    setError(false);
    api.getMySubmissions()
      .then(r => setSubs(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (viewing) return (
    <EvaluationResult data={viewing} onBack={() => setViewing(null)} />
  );

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><FileText size={22} /> Submissions</h1>
          <p className="page-description">Your evaluation history — {subs.length} total</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: 200 }}>
          <div className="spinner" style={{ width: 24, height: 24 }} />
        </div>
      ) : error ? (
        <div className="card empty-state">
          <XCircle size={40} style={{ opacity: 0.4, color: 'var(--error)' }} />
          <p>Failed to load submissions.</p>
          <button className="btn btn-primary btn-sm mt-3" onClick={load}>Retry</button>
        </div>
      ) : subs.length === 0 ? (
        <div className="card empty-state">
          <FileText size={40} style={{ opacity: 0.2 }} />
          <p>No submissions yet. Upload your first answer to get AI feedback.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Question</th>
                <th>Subject</th>
                <th>Words</th>
                <th>Score</th>
                <th>Status</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {subs.map((s, i) => {
                const score = s.evaluation?.overall_score;
                const scoreColor = score == null ? 'var(--text-muted)'
                  : score >= 7.5 ? 'var(--success)'
                  : score >= 5.5 ? 'var(--warning)'
                  : 'var(--error)';
                return (
                  <tr key={s.submission?.id || i}>
                    <td className="text-muted text-sm">{i + 1}</td>
                    <td style={{ maxWidth: 260 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.85rem' }}>
                        {s.submission?.question?.text?.substring(0, 60) || '—'}...
                      </div>
                    </td>
                    <td>{s.submission?.question?.subject
                      ? <span className="badge badge-primary">{s.submission.question.subject.split('-')[0].trim()}</span>
                      : '—'}</td>
                    <td className="text-muted text-sm">{s.submission?.word_count ?? '—'}</td>
                    <td>
                      {score != null
                        ? <span style={{ color: scoreColor, fontWeight: 700, fontSize: '0.9rem' }}>{score.toFixed(1)}</span>
                        : '—'}
                    </td>
                    <td>{statusBadge(s.submission?.status)}</td>
                    <td className="text-muted text-sm">
                      {s.submission?.created_at
                        ? new Date(s.submission.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
                        : '—'}
                    </td>
                    <td>
                      {s.evaluation && (
                        <button className="btn btn-ghost btn-sm" onClick={() => setViewing(s)}>
                          <Eye size={14} /> View
                        </button>
                      )}
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
