import { useState, useEffect, useRef } from 'react';
import {
  Upload, FileText, Zap, ChevronDown, ChevronUp, Trash2,
  RefreshCw, CheckCircle, XCircle, Clock, BookOpen,
  AlertCircle, Download, Eye, EyeOff, RotateCcw
} from 'lucide-react';
import {
  uploadMCQDocument, getMCQDocuments, getMCQDocument,
  deleteMCQDocument, regenerateMCQs
} from '../api';

// ── Helpers ────────────────────────────────────────────────────────────────────

const SUBJECT_AREAS = [
  'General Studies', 'History - Ancient', 'History - Medieval',
  'History - Modern & Freedom Struggle', 'Art & Culture',
  'Geography - Physical', 'Geography - Indian', 'Geography - World',
  'Indian Polity & Constitution', 'Governance & Public Policy',
  'Economy & Economic Development', 'Environment & Ecology',
  'Science & Technology', 'Current Affairs', 'International Relations',
  'Social Issues', 'Ethics & Integrity',
];

const TYPE_LABELS = {
  multi_statement:  { label: 'Multi-Statement', color: '#6366f1' },
  assertion_reason: { label: 'Assertion-Reason', color: '#0ea5e9' },
  match_following:  { label: 'Match Following', color: '#10b981' },
  how_many:         { label: 'How Many', color: '#f59e0b' },
  direct:           { label: 'Direct', color: '#8b5cf6' },
  negative:         { label: 'Negative', color: '#ef4444' },
};

const DIFFICULTY_COLORS = {
  easy:     { bg: '#d1fae5', text: '#065f46' },
  moderate: { bg: '#fef3c7', text: '#92400e' },
  hard:     { bg: '#fee2e2', text: '#991b1b' },
};

const STATUS_META = {
  uploaded:   { icon: Clock,        color: '#6b7280', label: 'Queued' },
  processing: { icon: RefreshCw,    color: '#f59e0b', label: 'Processing' },
  generated:  { icon: CheckCircle,  color: '#10b981', label: 'Ready' },
  failed:     { icon: XCircle,      color: '#ef4444', label: 'Failed' },
};

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.uploaded;
  const Icon = meta.icon;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 20,
      background: meta.color + '20', color: meta.color,
      fontSize: '0.7rem', fontWeight: 600,
    }}>
      <Icon size={10} style={status === 'processing' ? { animation: 'spin 1s linear infinite' } : {}} />
      {meta.label}
    </span>
  );
}

// ── MCQ Card ───────────────────────────────────────────────────────────────────

function MCQCard({ q, index, showAnswers }) {
  const typeMeta = TYPE_LABELS[q.question_type] || TYPE_LABELS.direct;
  const diffMeta = DIFFICULTY_COLORS[q.difficulty] || DIFFICULTY_COLORS.moderate;

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
      borderRadius: 10, padding: '16px 18px', marginBottom: 12,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{
          width: 24, height: 24, borderRadius: 6, background: 'var(--bg-elevated)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', flexShrink: 0,
        }}>{index}</span>
        <span style={{
          padding: '2px 8px', borderRadius: 20, fontSize: '0.68rem', fontWeight: 600,
          background: typeMeta.color + '20', color: typeMeta.color,
        }}>{typeMeta.label}</span>
        <span style={{
          padding: '2px 8px', borderRadius: 20, fontSize: '0.68rem', fontWeight: 600,
          background: diffMeta.bg, color: diffMeta.text,
        }}>{q.difficulty}</span>
        {q.topic && (
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {q.topic}
          </span>
        )}
      </div>

      {/* Question text */}
      <p style={{
        fontSize: '0.82rem', lineHeight: 1.65, color: 'var(--text-primary)',
        whiteSpace: 'pre-wrap', marginBottom: 12,
      }}>{q.question_text}</p>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {(q.options || []).map((opt) => {
          const isCorrect = opt.label === q.correct_option;
          const highlight = showAnswers && isCorrect;
          return (
            <div key={opt.label} style={{
              display: 'flex', alignItems: 'flex-start', gap: 8,
              padding: '6px 10px', borderRadius: 6,
              background: highlight ? '#d1fae5' : 'var(--bg-elevated)',
              border: `1px solid ${highlight ? '#6ee7b7' : 'var(--border-subtle)'}`,
              transition: 'all 0.2s',
            }}>
              <span style={{
                flexShrink: 0, width: 18, height: 18, borderRadius: 4,
                background: highlight ? '#10b981' : 'var(--border-subtle)',
                color: highlight ? 'white' : 'var(--text-muted)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.65rem', fontWeight: 700,
              }}>{opt.label.toUpperCase()}</span>
              <span style={{
                fontSize: '0.8rem', lineHeight: 1.5,
                color: highlight ? '#065f46' : 'var(--text-primary)',
                fontWeight: highlight ? 600 : 400,
              }}>{opt.text}</span>
              {highlight && <CheckCircle size={13} style={{ color: '#10b981', flexShrink: 0, marginLeft: 'auto' }} />}
            </div>
          );
        })}
      </div>

      {/* Explanation */}
      {showAnswers && q.explanation && (
        <div style={{
          marginTop: 10, padding: '8px 12px', borderRadius: 6,
          background: '#eff6ff', border: '1px solid #bfdbfe',
          fontSize: '0.75rem', color: '#1e40af', lineHeight: 1.6,
        }}>
          <strong>Explanation:</strong> {q.explanation}
        </div>
      )}
    </div>
  );
}

// ── Document Row ───────────────────────────────────────────────────────────────

function DocumentRow({ doc, onView, onDelete, onRegenerate, isActive }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '12px 16px', borderRadius: 10,
      background: isActive ? 'var(--bg-elevated)' : 'var(--bg-surface)',
      border: `1px solid ${isActive ? 'var(--primary)' : 'var(--border-subtle)'}`,
      marginBottom: 8, cursor: 'pointer', transition: 'all 0.15s',
    }} onClick={() => onView(doc.id)}>
      <div style={{
        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
        background: 'var(--primary)' + '20',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <FileText size={16} style={{ color: 'var(--primary)' }} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>{doc.title || doc.filename}</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 1 }}>
          {doc.subject_area} · {doc.file_type.toUpperCase()}
          {doc.status === 'generated' && ` · ${doc.num_questions} questions`}
        </div>
      </div>

      <StatusBadge status={doc.status} />

      <div style={{ display: 'flex', gap: 4 }} onClick={e => e.stopPropagation()}>
        <button
          className="btn btn-ghost"
          style={{ padding: 5, minHeight: 'auto' }}
          title="Regenerate MCQs"
          onClick={() => onRegenerate(doc)}
        ><RotateCcw size={13} /></button>
        <button
          className="btn btn-ghost"
          style={{ padding: 5, minHeight: 'auto', color: 'var(--error)' }}
          title="Delete"
          onClick={() => onDelete(doc.id)}
        ><Trash2 size={13} /></button>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function MCQGeneratorPage() {
  const [documents, setDocuments]           = useState([]);
  const [activeDoc, setActiveDoc]           = useState(null);
  const [loading, setLoading]               = useState(false);
  const [docsLoading, setDocsLoading]       = useState(true);
  const [showAnswers, setShowAnswers]       = useState(false);
  const [filterType, setFilterType]         = useState('all');
  const [filterDiff, setFilterDiff]         = useState('all');
  const [toast, setToast]                   = useState(null);
  const pollRef                             = useRef(null);
  const activeDocRef                        = useRef(null);

  // Upload form state
  const [file, setFile]                     = useState(null);
  const [title, setTitle]                   = useState('');
  const [subjectArea, setSubjectArea]       = useState('General Studies');
  const [numQuestions, setNumQuestions]     = useState(10);
  const [showUploadForm, setShowUploadForm] = useState(false);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Keep ref in sync with state so interval callbacks always see latest value
  useEffect(() => { activeDocRef.current = activeDoc; }, [activeDoc]);

  const loadDocuments = async () => {
    try {
      const res = await getMCQDocuments();
      setDocuments(res.data);
      // Auto-refresh active doc when it transitions to generated
      const current = activeDocRef.current;
      if (current && current.status !== 'generated') {
        const updated = res.data.find(d => d.id === current.id);
        if (updated?.status === 'generated') {
          const full = await getMCQDocument(current.id);
          setActiveDoc(full.data);
        }
      }
    } catch {
      // silent
    } finally {
      setDocsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Poll for processing documents
  useEffect(() => {
    const processing = documents.find(d => d.status === 'processing' || d.status === 'uploaded');
    if (processing && !pollRef.current) {
      pollRef.current = setInterval(async () => {
        await loadDocuments();
        // loadDocuments() already handles auto-refreshing the active doc via activeDocRef
      }, 3000);
    } else if (!processing && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {};
  }, [documents]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const handleView = async (docId) => {
    if (activeDoc?.id === docId) { setActiveDoc(null); return; }
    try {
      const res = await getMCQDocument(docId);
      setActiveDoc(res.data);
    } catch {
      showToast('Failed to load document', 'error');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) { showToast('Please select a file', 'error'); return; }
    setLoading(true);
    const form = new FormData();
    form.append('file', file);
    form.append('title', title || file.name);
    form.append('subject_area', subjectArea);
    form.append('num_questions', numQuestions);
    try {
      const result = await uploadMCQDocument(form);
      showToast(`Document uploaded! Generating ${numQuestions} UPSC-style MCQs...`);
      setFile(null); setTitle(''); setShowUploadForm(false);
      await loadDocuments();
      // Auto-open the new doc so user sees the processing spinner immediately
      if (result?.data?.id) {
        const docRes = await getMCQDocument(result.data.id);
        setActiveDoc(docRes.data);
      }
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Upload failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Delete this document and all its MCQs?')) return;
    try {
      await deleteMCQDocument(docId);
      if (activeDoc?.id === docId) setActiveDoc(null);
      await loadDocuments();
      showToast('Document deleted');
    } catch {
      showToast('Delete failed', 'error');
    }
  };

  const handleRegenerate = async (doc) => {
    try {
      await regenerateMCQs(doc.id, numQuestions);
      showToast(`Regenerating MCQs for "${doc.title}"...`);
      if (activeDoc?.id === doc.id) setActiveDoc(null);
      await loadDocuments();
    } catch {
      showToast('Regeneration failed', 'error');
    }
  };

  // Filter questions
  const filteredQuestions = (activeDoc?.questions || []).filter(q => {
    if (filterType !== 'all' && q.question_type !== filterType) return false;
    if (filterDiff !== 'all' && q.difficulty !== filterDiff) return false;
    return true;
  });

  // Stats for active doc
  const typeCounts = (activeDoc?.questions || []).reduce((acc, q) => {
    acc[q.question_type] = (acc[q.question_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={{ display: 'flex', gap: 20, height: '100%', minHeight: 0 }}>

      {/* ── Left panel: document list + upload ────────────────────────── */}
      <div style={{ width: 320, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              MCQ Generator
            </h2>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '2px 0 0' }}>
              UPSC-style questions from your documents
            </p>
          </div>
          <button
            className="btn btn-primary"
            style={{ padding: '6px 12px', fontSize: '0.75rem', minHeight: 'auto' }}
            onClick={() => setShowUploadForm(v => !v)}
          >
            <Upload size={12} /> Upload
          </button>
        </div>

        {/* Upload form */}
        {showUploadForm && (
          <form onSubmit={handleUpload} style={{
            background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
            borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
              Upload Document
            </div>

            {/* File drop zone */}
            <label style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
              padding: '16px 10px', borderRadius: 8, cursor: 'pointer',
              border: `2px dashed ${file ? 'var(--primary)' : 'var(--border-subtle)'}`,
              background: file ? 'var(--primary)10' : 'var(--bg-elevated)',
              transition: 'all 0.2s',
            }}>
              <FileText size={20} style={{ color: file ? 'var(--primary)' : 'var(--text-muted)' }} />
              <span style={{ fontSize: '0.72rem', color: file ? 'var(--primary)' : 'var(--text-muted)', textAlign: 'center' }}>
                {file ? file.name : 'Click to select PDF or TXT'}
              </span>
              <input
                type="file" accept=".pdf,.txt" style={{ display: 'none' }}
                onChange={e => setFile(e.target.files[0])}
              />
            </label>

            <input
              className="input" placeholder="Document title (optional)"
              value={title} onChange={e => setTitle(e.target.value)}
              style={{ fontSize: '0.78rem' }}
            />

            <select
              className="input" value={subjectArea}
              onChange={e => setSubjectArea(e.target.value)}
              style={{ fontSize: '0.78rem' }}
            >
              {SUBJECT_AREAS.map(s => <option key={s}>{s}</option>)}
            </select>

            <div>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                Questions to generate: <strong style={{ color: 'var(--text-primary)' }}>{numQuestions}</strong>
              </label>
              <input
                type="range" min={5} max={50} value={numQuestions}
                onChange={e => setNumQuestions(+e.target.value)}
                style={{ width: '100%', accentColor: 'var(--primary)' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-disabled)' }}>
                <span>5</span><span>50</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button
                type="button" className="btn btn-ghost"
                style={{ flex: 1, fontSize: '0.75rem', minHeight: 32 }}
                onClick={() => setShowUploadForm(false)}
              >Cancel</button>
              <button
                type="submit" className="btn btn-primary"
                style={{ flex: 2, fontSize: '0.75rem', minHeight: 32 }}
                disabled={loading || !file}
              >
                {loading ? <><RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} /> Uploading...</> : <><Zap size={11} /> Generate MCQs</>}
              </button>
            </div>
          </form>
        )}

        {/* Document list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {docsLoading ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', marginBottom: 8 }} />
              <div>Loading documents...</div>
            </div>
          ) : documents.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: '40px 20px',
              color: 'var(--text-muted)', fontSize: '0.78rem',
              background: 'var(--bg-surface)', borderRadius: 10,
              border: '1px dashed var(--border-subtle)',
            }}>
              <BookOpen size={28} style={{ marginBottom: 10, opacity: 0.4 }} />
              <div style={{ fontWeight: 600, marginBottom: 4 }}>No documents yet</div>
              <div>Upload a PDF or textbook to generate UPSC-style MCQs</div>
            </div>
          ) : (
            documents.map(doc => (
              <DocumentRow
                key={doc.id}
                doc={doc}
                isActive={activeDoc?.id === doc.id}
                onView={handleView}
                onDelete={handleDelete}
                onRegenerate={handleRegenerate}
              />
            ))
          )}
        </div>
      </div>

      {/* ── Right panel: MCQ viewer ──────────────────────────────────── */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>

        {!activeDoc ? (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: 16,
            background: 'var(--bg-surface)', borderRadius: 12,
            border: '1px dashed var(--border-subtle)', color: 'var(--text-muted)',
          }}>
            <div style={{
              width: 64, height: 64, borderRadius: 16,
              background: 'linear-gradient(135deg, var(--primary)20, var(--accent)20)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <BookOpen size={28} style={{ color: 'var(--primary)' }} />
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: 6 }}>
                UPSC-Style MCQ Generator
              </div>
              <div style={{ fontSize: '0.78rem', maxWidth: 360, lineHeight: 1.6 }}>
                Upload a PDF textbook or notes. Our AI analyzes the content and generates authentic
                UPSC Prelims-style questions including multi-statement, assertion-reason,
                match-the-following, and more — based on 40 years of UPSC pattern analysis.
              </div>
            </div>

            {/* Pattern legend */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center', maxWidth: 400 }}>
              {Object.entries(TYPE_LABELS).map(([k, v]) => (
                <span key={k} style={{
                  padding: '3px 10px', borderRadius: 20, fontSize: '0.68rem', fontWeight: 600,
                  background: v.color + '20', color: v.color,
                }}>{v.label}</span>
              ))}
            </div>
          </div>

        ) : (
          <>
            {/* Doc header */}
            <div style={{
              background: 'var(--bg-surface)', borderRadius: 10, padding: '14px 18px',
              border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 14,
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {activeDoc.title}
                  </span>
                  <StatusBadge status={activeDoc.status} />
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 3 }}>
                  {activeDoc.subject_area} · {activeDoc.file_type.toUpperCase()} · {activeDoc.num_questions} questions generated
                </div>
              </div>

              <button
                className="btn btn-ghost"
                style={{ fontSize: '0.75rem', minHeight: 32, gap: 5 }}
                onClick={() => setShowAnswers(v => !v)}
              >
                {showAnswers ? <EyeOff size={13} /> : <Eye size={13} />}
                {showAnswers ? 'Hide' : 'Show'} Answers
              </button>
            </div>

            {/* Stats row */}
            {activeDoc.status === 'generated' && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {Object.entries(typeCounts).map(([type, count]) => {
                  const meta = TYPE_LABELS[type] || TYPE_LABELS.direct;
                  return (
                    <div key={type} style={{
                      padding: '6px 12px', borderRadius: 8, fontSize: '0.72rem', fontWeight: 600,
                      background: meta.color + '15', color: meta.color,
                      border: `1px solid ${meta.color}30`,
                      cursor: 'pointer',
                      outline: filterType === type ? `2px solid ${meta.color}` : 'none',
                    }} onClick={() => setFilterType(filterType === type ? 'all' : type)}>
                      {meta.label}: {count}
                    </div>
                  );
                })}
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                  {['all', 'easy', 'moderate', 'hard'].map(d => (
                    <button key={d}
                      className={`btn ${filterDiff === d ? 'btn-primary' : 'btn-ghost'}`}
                      style={{ padding: '4px 10px', fontSize: '0.7rem', minHeight: 28 }}
                      onClick={() => setFilterDiff(d)}
                    >{d.charAt(0).toUpperCase() + d.slice(1)}</button>
                  ))}
                </div>
              </div>
            )}

            {/* Processing state */}
            {(activeDoc.status === 'processing' || activeDoc.status === 'uploaded') && (
              <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 12,
                background: 'var(--bg-surface)', borderRadius: 10,
                border: '1px solid var(--border-subtle)',
              }}>
                <RefreshCw size={28} style={{ color: 'var(--primary)', animation: 'spin 1.5s linear infinite' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    Generating UPSC-Style MCQs...
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    AI is analyzing your document and crafting authentic questions. This may take 30–60 seconds.
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  {['Extracting text', 'Analyzing content', 'Generating questions', 'Validating patterns'].map((step, i) => (
                    <span key={step} style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: '0.65rem',
                      background: 'var(--primary)15', color: 'var(--primary)', fontWeight: 500,
                    }}>{step}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Failed state */}
            {activeDoc.status === 'failed' && (
              <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 10,
                background: 'var(--bg-surface)', borderRadius: 10,
                border: '1px solid #fca5a5',
              }}>
                <AlertCircle size={28} style={{ color: '#ef4444' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    Generation Failed
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Could not process this document. Try re-uploading or check the file format.
                  </div>
                </div>
                <button className="btn btn-primary" style={{ fontSize: '0.78rem', minHeight: 34 }}
                  onClick={() => handleRegenerate(activeDoc)}>
                  <RotateCcw size={13} /> Retry Generation
                </button>
              </div>
            )}

            {/* MCQ list */}
            {activeDoc.status === 'generated' && (
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {filteredQuestions.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                    No questions match the current filter.
                  </div>
                ) : (
                  filteredQuestions.map((q, i) => (
                    <MCQCard key={q.id} q={q} index={i + 1} showAnswers={showAnswers} />
                  ))
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Toast ──────────────────────────────────────────────────────── */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
          padding: '10px 18px', borderRadius: 8, fontSize: '0.8rem', fontWeight: 500,
          background: toast.type === 'error' ? '#fef2f2' : '#f0fdf4',
          color: toast.type === 'error' ? '#b91c1c' : '#166534',
          border: `1px solid ${toast.type === 'error' ? '#fca5a5' : '#86efac'}`,
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          {toast.type === 'error' ? <XCircle size={14} /> : <CheckCircle size={14} />}
          {toast.msg}
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .input { background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 7px 10px; color: var(--text-primary); outline: none; width: 100%; box-sizing: border-box; }
        .input:focus { border-color: var(--primary); }
      `}</style>
    </div>
  );
}
