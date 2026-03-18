import { useState } from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';
import { ArrowLeft, CheckCircle2, XCircle, Lightbulb, Tag, TrendingUp, BookOpen, Target } from 'lucide-react';

const PARAM_LABELS = {
  relevance_score: 'Relevance', intro_score: 'Introduction', body_score: 'Body',
  keyword_score: 'Keywords', structure_score: 'Structure', factual_score: 'Factual',
  conclusion_score: 'Conclusion', word_limit_score: 'Word Limit',
  analysis_score: 'Analysis', diagram_score: 'Diagram', multidimensional_score: 'Multi-Dim',
};

function scoreColor(s) {
  if (s >= 7.5) return 'var(--success)';
  if (s >= 5.5) return 'var(--warning)';
  return 'var(--error)';
}

function ScoreRing({ score, max = 10, size = 110 }) {
  const r = 44, cx = size / 2, cy = size / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(score / max, 1);
  const dash = pct * circ;
  const color = scoreColor(score);
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-elevated)" strokeWidth="8" />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)' }} />
      </svg>
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', textAlign: 'center' }}>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color, lineHeight: 1 }}>{score.toFixed(1)}</div>
        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>/ {max}</div>
      </div>
    </div>
  );
}

export default function EvaluationResult({ data, onBack }) {
  const [tab, setTab] = useState('scores');
  const ev = data?.evaluation;
  const sub = data?.submission;

  if (!ev) return (
    <div className="animate-in">
      <button className="btn btn-ghost mb-4" onClick={onBack}><ArrowLeft size={16} /> Back</button>
      <div className="card empty-state"><p>No evaluation data found.</p></div>
    </div>
  );

  const scoreParams = Object.entries(PARAM_LABELS).map(([k, label]) => ({
    label,
    value: ev[k] ?? 0,
  }));

  const radarData = [
    { subject: 'Relevance',   A: ev.relevance_score ?? 0 },
    { subject: 'Analysis',    A: ev.analysis_score ?? 0 },
    { subject: 'Structure',   A: ev.structure_score ?? 0 },
    { subject: 'Keywords',    A: ev.keyword_score ?? 0 },
    { subject: 'Multi-Dim',   A: ev.multidimensional_score ?? 0 },
    { subject: 'Factual',     A: ev.factual_score ?? 0 },
  ];

  const marks = ev.marks_obtained ?? 0;
  const totalMarks = sub?.question?.marks ?? 15;

  return (
    <div className="animate-in">
      {/* Header */}
      <div className="page-header">
        <button className="btn btn-ghost" onClick={onBack}><ArrowLeft size={16} /> Back</button>
        <div className="flex items-center gap-3">
          <span className="badge badge-success">Evaluation Complete</span>
          {sub?.question && (
            <span className="badge badge-primary">{sub.question.subject}</span>
          )}
        </div>
      </div>

      {/* Score Summary */}
      <div className="card mb-4" style={{ background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%)' }}>
        <div className="flex items-center gap-8">
          <ScoreRing score={ev.overall_score ?? 0} />
          <div style={{ flex: 1 }}>
            <div className="text-muted text-xs font-semibold mb-1" style={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>Overall Score</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 8 }}>
              <span style={{ color: scoreColor(ev.overall_score) }}>{ev.overall_score?.toFixed(1)}/10</span>
              <span className="text-muted text-sm font-medium" style={{ marginLeft: 12 }}>
                {marks.toFixed(1)}/{totalMarks} marks
              </span>
            </div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)', lineHeight: 1.65 }}>
              {ev.feedback_summary}
            </p>
          </div>
          {sub?.question && (
            <div style={{ textAlign: 'right', minWidth: 160 }}>
              <div className="text-xs text-muted mb-2">Question Details</div>
              <div className="badge badge-neutral mb-1" style={{ display: 'block', textAlign: 'center' }}>{sub.question.word_limit} word limit</div>
              <div className="badge badge-neutral" style={{ display: 'block', textAlign: 'center' }}>{sub.word_count} words written</div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs mb-4">
        {[['scores','Scores'], ['feedback','Feedback'], ['keywords','Keywords'], ['dimensions','Dimensions'], ['model','Model Answer']].map(([id, label]) => (
          <button key={id} className={`tab ${tab===id?'active':''}`} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {/* Tab: Scores */}
      {tab === 'scores' && (
        <div className="grid-2 gap-4 animate-in">
          <div className="card">
            <h3 className="mb-4">Parameter Scores</h3>
            {scoreParams.map(({ label, value }) => (
              <div key={label} className="score-param">
                <span className="score-param-name">{label}</span>
                <div className="score-bar flex-1">
                  <div className="score-bar-fill" style={{ width: `${value * 10}%`, background: scoreColor(value) }} />
                </div>
                <span className="score-param-value" style={{ color: scoreColor(value) }}>{value.toFixed(1)}</span>
              </div>
            ))}
          </div>
          <div className="card">
            <h3 className="mb-4">Radar Overview</h3>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Radar name="Score" dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.15} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Tab: Feedback */}
      {tab === 'feedback' && (
        <div className="grid-2 gap-4 animate-in">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 size={16} color="var(--success)" />
              <h3 style={{ color: 'var(--success)' }}>Strengths</h3>
            </div>
            {(ev.strengths || []).map((s, i) => (
              <div key={i} className="flex items-start gap-2 mb-3">
                <CheckCircle2 size={14} style={{ color: 'var(--success)', marginTop: 2, flexShrink: 0 }} />
                <span className="text-sm" style={{ lineHeight: 1.6 }}>{s}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <XCircle size={16} color="var(--error)" />
              <h3 style={{ color: 'var(--error)' }}>Weaknesses</h3>
            </div>
            {(ev.weaknesses || []).map((w, i) => (
              <div key={i} className="flex items-start gap-2 mb-3">
                <XCircle size={14} style={{ color: 'var(--error)', marginTop: 2, flexShrink: 0 }} />
                <span className="text-sm" style={{ lineHeight: 1.6 }}>{w}</span>
              </div>
            ))}
          </div>

          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb size={16} color="var(--warning)" />
              <h3 style={{ color: 'var(--warning)' }}>Improvement Suggestions</h3>
            </div>
            <div className="grid-2 gap-3">
              {(ev.improvements || []).map((imp, i) => (
                <div key={i} className="card-flat flex items-start gap-2">
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%', background: 'var(--warning-subtle)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.65rem', fontWeight: 700, color: 'var(--warning)', flexShrink: 0
                  }}>{i + 1}</div>
                  <span className="text-sm" style={{ lineHeight: 1.6 }}>{imp}</span>
                </div>
              ))}
            </div>
          </div>

          {ev.topper_benchmark && (
            <div className="card" style={{ gridColumn: '1 / -1', borderLeft: '3px solid var(--accent)' }}>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp size={15} color="var(--accent)" />
                <h3 style={{ color: 'var(--accent)' }}>Topper Benchmark</h3>
              </div>
              <p className="text-sm" style={{ lineHeight: 1.7, color: 'var(--text-secondary)' }}>{ev.topper_benchmark}</p>
            </div>
          )}
        </div>
      )}

      {/* Tab: Keywords */}
      {tab === 'keywords' && (
        <div className="grid-2 gap-4 animate-in">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Tag size={15} color="var(--success)" />
              <h3>Keywords Found <span className="badge badge-success ml-2">{(ev.keywords_found||[]).length}</span></h3>
            </div>
            <div className="flex flex-wrap">
              {(ev.keywords_found || []).map(kw => (
                <span key={kw} className="keyword-pill pill-found">{kw}</span>
              ))}
              {!(ev.keywords_found?.length) && <p className="text-sm text-muted">No keywords detected.</p>}
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Tag size={15} color="var(--error)" />
              <h3>Keywords Missed <span className="badge badge-error ml-2">{(ev.keywords_missed||[]).length}</span></h3>
            </div>
            <div className="flex flex-wrap">
              {(ev.keywords_missed || []).map(kw => (
                <span key={kw} className="keyword-pill pill-missed">{kw}</span>
              ))}
              {!(ev.keywords_missed?.length) && <p className="text-sm text-muted">All key terms covered!</p>}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Dimensions */}
      {tab === 'dimensions' && (
        <div className="card animate-in">
          <h3 className="mb-4">Dimensional Coverage</h3>
          <div className="flex flex-wrap gap-3 mb-6">
            {Object.entries(ev.dimension_analysis || {}).map(([dim, covered]) => (
              <div key={dim} className={`dim-tag ${covered ? 'dim-covered' : 'dim-uncovered'}`}>
                {covered ? <CheckCircle2 size={11} /> : <XCircle size={11} />}
                {dim.charAt(0).toUpperCase() + dim.slice(1)}
              </div>
            ))}
          </div>
          <div className="divider" />
          <div className="grid-3 gap-3 mt-4">
            {Object.entries(ev.dimension_analysis || {}).map(([dim, covered]) => (
              <div key={dim} className="card-flat" style={{ borderLeft: `3px solid ${covered ? 'var(--success)' : 'var(--border)'}` }}>
                <div className="flex items-center gap-2 mb-1">
                  {covered
                    ? <CheckCircle2 size={13} color="var(--success)" />
                    : <XCircle size={13} color="var(--text-disabled)" />}
                  <span className="text-sm font-semibold" style={{ color: covered ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {dim.charAt(0).toUpperCase() + dim.slice(1)}
                  </span>
                </div>
                <span className="text-xs" style={{ color: covered ? 'var(--success)' : 'var(--text-disabled)' }}>
                  {covered ? 'Covered' : 'Missing — add this dimension'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Model Answer */}
      {tab === 'model' && (
        <div className="card animate-in">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={16} color="var(--primary)" />
            <h3>Model Answer Outline</h3>
          </div>
          <div style={{
            background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: 20,
            fontSize: '0.9rem', lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap'
          }}>
            {ev.model_answer || 'No model answer available.'}
          </div>
          {ev.topper_benchmark && (
            <div className="mt-4" style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
              <div className="flex items-center gap-2 mb-3">
                <Target size={14} color="var(--accent)" />
                <span className="text-sm font-semibold" style={{ color: 'var(--accent)' }}>Topper Approach</span>
              </div>
              <p className="text-sm" style={{ lineHeight: 1.7, color: 'var(--text-secondary)' }}>{ev.topper_benchmark}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
