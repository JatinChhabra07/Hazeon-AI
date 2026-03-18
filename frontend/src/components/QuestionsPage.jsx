import { useState, useEffect, useMemo } from 'react';
import {
  BookOpen, Plus, Pencil, Trash2, X, Save, Search,
  ChevronDown, ChevronUp, AlertTriangle, CheckCircle2,
} from 'lucide-react';
import * as api from '../api';

// ── Constants ─────────────────────────────────────────────────────────────────
const SUBJECTS = [
  'GS1 - Society', 'GS1 - History', 'GS1 - Geography',
  'GS2 - Governance', 'GS2 - Polity', 'GS2 - IR', 'GS2 - Social Justice',
  'GS3 - Economy', 'GS3 - Environment', 'GS3 - Science & Tech', 'GS3 - Security',
  'GS4 - Ethics', 'Essay', 'Optional',
];
const EXAM_TYPES  = ['HCS', 'UPSC', 'HPSC', 'UPPSC', 'MPPSC', 'RPSC', 'Other'];
const DIFFICULTIES = ['easy', 'moderate', 'hard'];

const EMPTY_FORM = {
  text: '', subject: 'GS2 - Governance', topic: '', exam_type: 'HCS',
  year: new Date().getFullYear(), marks: 15, word_limit: 250,
  difficulty: 'moderate', model_answer_points: [''],
};

function diffBadge(d) {
  const map = { easy: ['badge-success', 'Easy'], moderate: ['badge-warning', 'Moderate'], hard: ['badge-error', 'Hard'] };
  const [cls, label] = map[d] || ['badge-neutral', d];
  return <span className={`badge ${cls}`} style={{ fontSize: '0.65rem' }}>{label}</span>;
}

// ── Form Panel ────────────────────────────────────────────────────────────────
function QuestionForm({ initial, onSave, onCancel, saving, error }) {
  const [form, setForm] = useState(initial || EMPTY_FORM);

  // reset when `initial` changes (switching between edit targets)
  useEffect(() => { setForm(initial || EMPTY_FORM); }, [initial]);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const setNum = (k) => (e) => setForm(f => ({ ...f, [k]: parseInt(e.target.value) || 0 }));

  const setPoint = (i, val) => setForm(f => {
    const pts = [...f.model_answer_points];
    pts[i] = val;
    return { ...f, model_answer_points: pts };
  });
  const addPoint    = () => setForm(f => ({ ...f, model_answer_points: [...f.model_answer_points, ''] }));
  const removePoint = (i) => setForm(f => ({
    ...f,
    model_answer_points: f.model_answer_points.filter((_, idx) => idx !== i),
  }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      year: form.year || null,
      model_answer_points: form.model_answer_points.filter(p => p.trim()),
    };
    onSave(payload);
  };

  const isEdit = !!(initial?.id);

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          {isEdit ? 'Edit Question' : 'Add New Question'}
        </h3>
        <button type="button" onClick={onCancel} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}>
          <X size={18} />
        </button>
      </div>

      {error && (
        <div style={{ background: 'var(--error-subtle)', border: '1px solid rgba(255,77,106,0.3)', borderRadius: 8, padding: '10px 14px', fontSize: '0.82rem', color: 'var(--error)', display: 'flex', gap: 8 }}>
          <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} /> {error}
        </div>
      )}

      {/* Question text */}
      <div className="form-group">
        <label className="form-label">Question Text <span style={{ color: 'var(--error)' }}>*</span></label>
        <textarea
          className="form-input"
          rows={4}
          placeholder="Write the full question here…"
          value={form.text}
          onChange={set('text')}
          required
          style={{ resize: 'vertical', minHeight: 90 }}
        />
      </div>

      {/* Subject + Exam Type */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Subject <span style={{ color: 'var(--error)' }}>*</span></label>
          <select className="form-input" value={form.subject} onChange={set('subject')} required>
            {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Exam Type</label>
          <select className="form-input" value={form.exam_type} onChange={set('exam_type')}>
            {EXAM_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {/* Topic + Year */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Topic</label>
          <input className="form-input" placeholder="e.g. Federalism" value={form.topic || ''} onChange={set('topic')} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Year</label>
          <input className="form-input" type="number" placeholder="2025" value={form.year || ''} onChange={setNum('year')} min={1990} max={2030} />
        </div>
      </div>

      {/* Marks + Word Limit + Difficulty */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Marks</label>
          <input className="form-input" type="number" value={form.marks} onChange={setNum('marks')} min={5} max={250} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Word Limit</label>
          <input className="form-input" type="number" value={form.word_limit} onChange={setNum('word_limit')} min={50} max={2000} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Difficulty</label>
          <select className="form-input" value={form.difficulty} onChange={set('difficulty')}>
            {DIFFICULTIES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
          </select>
        </div>
      </div>

      {/* Model Answer Key Points */}
      <div className="form-group" style={{ margin: 0 }}>
        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Model Answer Key Points</span>
          <button type="button" onClick={addPoint} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 4, cursor: 'pointer', color: 'var(--primary)', fontSize: '0.75rem', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Plus size={11} /> Add Point
          </button>
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {form.model_answer_points.map((pt, i) => (
            <div key={i} style={{ display: 'flex', gap: 6 }}>
              <input
                className="form-input"
                placeholder={`Point ${i + 1}`}
                value={pt}
                onChange={e => setPoint(i, e.target.value)}
                style={{ flex: 1 }}
              />
              {form.model_answer_points.length > 1 && (
                <button type="button" onClick={() => removePoint(i)} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 6, cursor: 'pointer', color: 'var(--error)', padding: '0 8px', flexShrink: 0 }}>
                  <X size={13} />
                </button>
              )}
            </div>
          ))}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
          These guide the AI evaluator. Blank points are ignored.
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, paddingTop: 4 }}>
        <button className="btn btn-primary" type="submit" disabled={saving} style={{ flex: 1 }}>
          {saving
            ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Saving…</>
            : <><Save size={14} /> {isEdit ? 'Save Changes' : 'Add Question'}</>}
        </button>
        <button className="btn btn-ghost" type="button" onClick={onCancel} style={{ width: 80 }}>
          Cancel
        </button>
      </div>
    </form>
  );
}

// ── Delete Confirm ─────────────────────────────────────────────────────────────
function DeleteConfirm({ question, onConfirm, onCancel, deleting }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--error-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Trash2 size={16} color="var(--error)" />
        </div>
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>Delete Question?</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>This cannot be undone.</div>
        </div>
      </div>
      <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '10px 12px', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        {question.text.substring(0, 120)}…
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-ghost" onClick={onCancel} style={{ flex: 1 }} disabled={deleting}>Cancel</button>
        <button onClick={onConfirm} disabled={deleting} style={{ flex: 1, background: 'var(--error)', color: '#fff', border: 'none', borderRadius: 8, padding: '10px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
          {deleting ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Trash2 size={14} />}
          Delete
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function QuestionsPage({ user }) {
  const [questions, setQuestions] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [search,    setSearch]    = useState('');
  const [filterSub, setFilterSub] = useState('');
  const [filterExam,setFilterExam]= useState('');
  const [panel,     setPanel]     = useState(null);   // null | 'add' | { ...question }
  const [delTarget, setDelTarget] = useState(null);
  const [saving,    setSaving]    = useState(false);
  const [deleting,  setDeleting]  = useState(false);
  const [formError, setFormError] = useState('');
  const [toast,     setToast]     = useState('');
  const [expanded,  setExpanded]  = useState(null);  // expanded row id

  const isAdmin = user?.role === 'institute_admin' || user?.role === 'super_admin';

  const load = () => {
    setLoading(true);
    api.getQuestions()
      .then(r => setQuestions(r.data))
      .catch(() => setQuestions([]))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000); };

  // Filtered list
  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return questions.filter(qn => {
      const matchText = !q || qn.text?.toLowerCase().includes(q) || qn.topic?.toLowerCase().includes(q);
      const matchSub  = !filterSub  || qn.subject === filterSub;
      const matchExam = !filterExam || qn.exam_type === filterExam;
      return matchText && matchSub && matchExam;
    });
  }, [questions, search, filterSub, filterExam]);

  const uniqueSubjects = useMemo(() => [...new Set(questions.map(q => q.subject))].sort(), [questions]);
  const uniqueExams    = useMemo(() => [...new Set(questions.map(q => q.exam_type))].sort(), [questions]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSave = async (payload) => {
    setSaving(true); setFormError('');
    try {
      if (panel?.id) {
        await api.updateQuestion(panel.id, payload);
        showToast('Question updated.');
      } else {
        await api.createQuestion(payload);
        showToast('Question added to question bank.');
      }
      setPanel(null);
      load();
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save. Please try again.');
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!delTarget) return;
    setDeleting(true);
    try {
      await api.deleteQuestion(delTarget.id);
      setDelTarget(null);
      showToast('Question deleted.');
      load();
    } catch (err) {
      setDelTarget(null);
      showToast('Delete failed: ' + (err?.response?.data?.detail || 'Unknown error'));
    }
    setDeleting(false);
  };

  const openEdit = (q) => { setFormError(''); setPanel({ ...q, model_answer_points: q.model_answer_points?.length ? q.model_answer_points : [''] }); };
  const openAdd  = ()  => { setFormError(''); setPanel('add'); };
  const closePanel = () => { setPanel(null); setFormError(''); };

  // ── Layout ─────────────────────────────────────────────────────────────────
  const showPanel = panel !== null;

  return (
    <div className="animate-in">
      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 10, boxShadow: '0 8px 24px rgba(0,0,0,0.4)', zIndex: 9999, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
          <CheckCircle2 size={15} style={{ color: 'var(--success)', flexShrink: 0 }} /> {toast}
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title"><BookOpen size={22} /> Question Bank</h1>
          <p className="page-description">{questions.length} questions · Add and manage your institute's question repository</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary btn-sm" onClick={openAdd}>
            <Plus size={14} /> Add Question
          </button>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: showPanel ? '1fr 420px' : '1fr', gap: 20, alignItems: 'start' }}>

        {/* ── Left: Table ───────────────────────────────────────────────────── */}
        <div>
          {/* Filters */}
          <div className="card mb-4" style={{ padding: '12px 16px' }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <div className="search-box" style={{ flex: 1, minWidth: 180 }}>
                <Search size={13} style={{ color: 'var(--text-muted)' }} />
                <input placeholder="Search questions or topics…" value={search} onChange={e => setSearch(e.target.value)} />
              </div>
              <select className="form-input" style={{ width: 180 }} value={filterSub} onChange={e => setFilterSub(e.target.value)}>
                <option value="">All Subjects</option>
                {uniqueSubjects.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select className="form-input" style={{ width: 120 }} value={filterExam} onChange={e => setFilterExam(e.target.value)}>
                <option value="">All Exams</option>
                {uniqueExams.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
              {(search || filterSub || filterExam) && (
                <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setFilterSub(''); setFilterExam(''); }}>
                  <X size={12} /> Clear
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center" style={{ height: 200 }}>
              <div className="spinner" style={{ width: 24, height: 24 }} />
            </div>
          ) : filtered.length === 0 ? (
            <div className="card empty-state">
              <BookOpen size={40} style={{ opacity: 0.2 }} />
              <p>{questions.length === 0 ? 'No questions yet. Add your first question.' : 'No questions match your filters.'}</p>
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {filtered.map((q, i) => {
                const isExpanded = expanded === q.id;
                return (
                  <div key={q.id} style={{ borderBottom: i < filtered.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    {/* Row */}
                    <div style={{ padding: '14px 18px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      {/* Index */}
                      <div style={{ width: 22, height: 22, borderRadius: 6, background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', flexShrink: 0, marginTop: 1 }}>
                        {i + 1}
                      </div>

                      {/* Content */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 6 }}>
                          <span className="badge badge-primary" style={{ fontSize: '0.62rem' }}>{q.subject}</span>
                          <span className="badge badge-neutral" style={{ fontSize: '0.62rem' }}>{q.exam_type}</span>
                          {diffBadge(q.difficulty)}
                          <span className="badge badge-neutral" style={{ fontSize: '0.62rem' }}>{q.marks}M · {q.word_limit}W</span>
                          {q.year && <span className="badge badge-neutral" style={{ fontSize: '0.62rem' }}>{q.year}</span>}
                        </div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.55 }}>
                          {isExpanded ? q.text : `${q.text.substring(0, 120)}${q.text.length > 120 ? '…' : ''}`}
                        </div>
                        {q.topic && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>Topic: {q.topic}</div>
                        )}

                        {/* Key points (expanded) */}
                        {isExpanded && q.model_answer_points?.length > 0 && (
                          <div style={{ marginTop: 10, padding: '10px 12px', background: 'var(--bg-elevated)', borderRadius: 8, borderLeft: '3px solid var(--warning)' }}>
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--warning)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Key Points to Cover</div>
                            {q.model_answer_points.map((pt, pi) => (
                              <div key={pi} style={{ display: 'flex', gap: 6, marginBottom: 4, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                <span style={{ color: 'var(--warning)', flexShrink: 0 }}>•</span> {pt}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                        <button onClick={() => setExpanded(isExpanded ? null : q.id)} className="btn btn-ghost btn-sm" title={isExpanded ? 'Collapse' : 'Expand'} style={{ padding: '4px 6px' }}>
                          {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                        </button>
                        {isAdmin && (
                          <>
                            <button onClick={() => openEdit(q)} className="btn btn-ghost btn-sm" title="Edit" style={{ padding: '4px 8px' }}>
                              <Pencil size={13} />
                            </button>
                            <button onClick={() => setDelTarget(q)} className="btn btn-ghost btn-sm" title="Delete" style={{ padding: '4px 8px', color: 'var(--error)' }}>
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Right: Form / Delete Panel ────────────────────────────────────── */}
        {showPanel && (
          <div className="card" style={{ position: 'sticky', top: 20 }}>
            {delTarget ? (
              <DeleteConfirm
                question={delTarget}
                onConfirm={handleDelete}
                onCancel={() => setDelTarget(null)}
                deleting={deleting}
              />
            ) : (
              <QuestionForm
                initial={panel === 'add' ? null : panel}
                onSave={handleSave}
                onCancel={closePanel}
                saving={saving}
                error={formError}
              />
            )}
          </div>
        )}
      </div>

      {/* Delete confirm (when panel is closed, show as overlay card) */}
      {delTarget && !showPanel && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" style={{ width: 420, maxWidth: '90vw' }}>
            <DeleteConfirm
              question={delTarget}
              onConfirm={handleDelete}
              onCancel={() => setDelTarget(null)}
              deleting={deleting}
            />
          </div>
        </div>
      )}
    </div>
  );
}
