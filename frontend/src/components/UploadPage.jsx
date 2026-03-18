import { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle2, Cpu, Brain, BarChart3, Sparkles, Clock, BookOpen } from 'lucide-react';
import * as api from '../api';
import EvaluationResult from './EvaluationResult';

const PIPELINE_STEPS = [
  { icon: Upload,     label: 'File Received',         desc: 'Saving your answer sheet...' },
  { icon: Brain,      label: 'OCR Extraction',        desc: 'Gemini Vision reading handwriting...' },
  { icon: Cpu,        label: 'LangGraph Analysis',    desc: 'Structural analysis + RAG retrieval...' },
  { icon: BarChart3,  label: 'Groq Evaluation',       desc: 'Scoring 11 parameters via LLM...' },
  { icon: Sparkles,   label: 'Feedback Generated',    desc: 'Results ready!' },
];

function stepState(pipeStep, idx) {
  if (pipeStep > idx + 1) return 'done';
  if (pipeStep === idx + 1) return 'running';
  return 'pending';
}

export default function UploadPage({ onEvaluated }) {
  const [questions,      setQuestions]      = useState([]);
  const [questionsError, setQuestionsError] = useState(false);
  const [selectedQ,      setSelectedQ]      = useState('');
  const [file,           setFile]           = useState(null);
  const [uploading,      setUploading]      = useState(false);
  const [pipeStep,       setPipeStep]       = useState(0);
  const [result,         setResult]         = useState(null);
  const [error,          setError]          = useState('');

  const loadQuestions = () => {
    setQuestionsError(false);
    api.getQuestions()
      .then(r => setQuestions(r.data))
      .catch(() => setQuestionsError(true));
  };

  useEffect(() => { loadQuestions(); }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => { if (files[0]) setFile(files[0]); },
    accept: { 'image/*': ['.jpg','.jpeg','.png'], 'application/pdf': ['.pdf'] },
    maxFiles: 1, maxSize: 15 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (!file || !selectedQ) return;
    setError(''); setUploading(true); setPipeStep(1);

    const t1 = setTimeout(() => setPipeStep(2), 1800);
    const t2 = setTimeout(() => setPipeStep(3), 5000);
    const t3 = setTimeout(() => setPipeStep(4), 9000);

    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('question_id', selectedQ);
      const res = await api.uploadAnswer(fd);
      setPipeStep(5);
      setTimeout(() => { setResult(res.data); if (onEvaluated) onEvaluated(); }, 700);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Evaluation failed. Check your API keys and try again.');
      setPipeStep(0);
    }
    clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
    setUploading(false);
  };

  if (result) return (
    <EvaluationResult
      data={result}
      onBack={() => { setResult(null); setFile(null); setSelectedQ(''); setPipeStep(0); setError(''); }}
    />
  );

  const activeQ = questions.find(q => String(q.id) === String(selectedQ));

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Cpu size={22} /> Answer Evaluation Pipeline</h1>
          <p className="page-description">Upload → OCR → AI Analysis → Structured Feedback in &lt;30s</p>
        </div>
        <div className="badge badge-accent" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
          <Brain size={12} /> Groq + Gemini Powered
        </div>
      </div>

      <div className="grid-2 gap-6">
        {/* Left: Upload form */}
        <div className="flex-col gap-4 flex">

          {/* Step 1: Select question */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.68rem', fontWeight: 700, color: 'white' }}>1</div>
              <h3>Select Question</h3>
            </div>
            {questionsError ? (
              <div className="flex items-center gap-2" style={{ color: 'var(--error)', fontSize: '0.85rem' }}>
                Failed to load questions.{' '}
                <button onClick={loadQuestions} style={{ textDecoration: 'underline', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}>
                  Retry
                </button>
              </div>
            ) : (
              <select
                className="form-input"
                value={selectedQ}
                onChange={e => setSelectedQ(e.target.value)}
                disabled={uploading}
              >
                <option value="">— Choose from question repository —</option>
                {questions.map(q => (
                  <option key={q.id} value={q.id}>
                    [{q.exam_type}] {q.subject} · {q.text.substring(0, 70)}...
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Step 2: Upload file */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.68rem', fontWeight: 700, color: 'var(--bg-base)' }}>2</div>
              <h3>Upload Answer Sheet</h3>
            </div>

            <div
              {...getRootProps()}
              className={`dropzone ${isDragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
            >
              <input {...getInputProps()} />
              <div style={{ marginBottom: 12 }}>
                {file
                  ? <CheckCircle2 size={36} color="var(--success)" />
                  : <Upload size={36} color="var(--text-muted)" />
                }
              </div>
              {file ? (
                <>
                  <div className="font-semibold" style={{ color: 'var(--success)' }}>{file.name}</div>
                  <div className="text-sm text-muted mt-2">{(file.size/1024).toFixed(1)} KB · Click to replace</div>
                </>
              ) : (
                <>
                  <div className="font-semibold">Drag & drop PDF or Image</div>
                  <div className="text-sm text-muted mt-2">Hindi + English handwriting supported · Max 15MB</div>
                </>
              )}
            </div>

            {error && (
              <div className="mt-3" style={{
                background: 'var(--error-subtle)', border: '1px solid rgba(255,77,106,0.3)',
                borderRadius: 'var(--radius-md)', padding: '10px 14px',
                fontSize: '0.82rem', color: 'var(--error)'
              }}>{error}</div>
            )}

            <button
              className="btn btn-primary btn-lg w-full mt-4"
              disabled={!file || !selectedQ || uploading}
              onClick={handleUpload}
            >
              {uploading
                ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Evaluating...</>
                : <><Cpu size={16} /> Run Evaluation Pipeline</>
              }
            </button>
          </div>

          {/* Pipeline status */}
          {uploading && (
            <div className="card fade-in">
              <h4 className="mb-4">Pipeline Running</h4>
              <div className="pipeline">
                {PIPELINE_STEPS.map((s, i) => {
                  const state = stepState(pipeStep, i);
                  return (
                    <div key={i} className={`pipeline-step ${state}`}>
                      <div className={`step-indicator ${state}`}>
                        {state === 'done' ? <CheckCircle2 size={14} /> : <s.icon size={13} />}
                      </div>
                      <div className="step-content">
                        <div className="step-name" style={{ opacity: state === 'pending' ? 0.4 : 1 }}>{s.label}</div>
                        {state === 'running' && <div className="step-desc">{s.desc}</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right: Question context */}
        <div className="flex-col gap-4 flex">
          {activeQ ? (
            <>
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <span className="badge badge-primary">{activeQ.subject}</span>
                  <div className="flex gap-2">
                    <span className="badge badge-neutral">{activeQ.marks} Marks</span>
                    <span className="badge badge-accent">{activeQ.exam_type}</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.925rem', lineHeight: 1.7, color: 'var(--text-primary)', marginBottom: 16 }}>
                  "{activeQ.text}"
                </p>
                <div className="flex gap-4 text-sm text-muted">
                  <span><Clock size={12} style={{ marginRight: 4, display: 'inline' }} />Word limit: {activeQ.word_limit}</span>
                  <span>Difficulty: {activeQ.difficulty}</span>
                </div>
              </div>

              {activeQ.model_answer_points?.length > 0 && (
                <div className="card" style={{ borderLeft: '3px solid var(--warning)' }}>
                  <h4 className="mb-3" style={{ color: 'var(--warning)' }}>Key Points to Cover</h4>
                  {activeQ.model_answer_points.slice(0,5).map((pt, i) => (
                    <div key={i} className="flex items-start gap-2 mb-2">
                      <CheckCircle2 size={13} style={{ color: 'var(--warning)', marginTop: 2, flexShrink: 0 }} />
                      <span className="text-sm text-secondary">{pt}</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="card card-flat">
                <h4 className="mb-3">Evaluation Parameters</h4>
                <div className="flex flex-wrap gap-2">
                  {['Relevance','Introduction','Keywords','Structure','Factual','Analysis','Conclusion','Dimensions'].map(p => (
                    <span key={p} className="badge badge-neutral">{p}</span>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="card" style={{ height: '100%', minHeight: 280 }}>
              <div className="empty-state">
                <BookOpen size={40} />
                <p>Select a question to see evaluation criteria, key points, and scoring guidelines here.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
