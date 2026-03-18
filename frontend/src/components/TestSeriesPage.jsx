import { useState } from 'react';
import { Layers, Calendar, FileText, Clock, ArrowRight, CheckCircle2, Lock, Users, Target, Zap, BarChart3 } from 'lucide-react';

const SERIES = [
  {
    id: 1, name: 'HCS Mains Mock — Series 1', papers: 4, questions: 20,
    date: 'Mar 20, 2026', status: 'upcoming', students: 38, subject: 'GS1–GS4',
    desc: 'Full-length mock covering all GS papers. Same difficulty as HCS Mains 2026.',
  },
  {
    id: 2, name: 'HCS Mains Mock — Series 2', papers: 4, questions: 20,
    date: 'Apr 3, 2026', status: 'upcoming', students: 41, subject: 'GS1–GS4',
    desc: 'Second full-length mock with updated current affairs integration.',
  },
  {
    id: 3, name: 'GS Full Length Test 1', papers: 1, questions: 10,
    date: 'Feb 28, 2026', status: 'completed', students: 45, subject: 'GS2',
    desc: 'Governance, Polity, IR focused test. 10 questions, 150 marks total.',
    avgScore: 6.4,
  },
  {
    id: 4, name: 'Ethics Special — Series 1', papers: 2, questions: 12,
    date: 'Mar 10, 2026', status: 'completed', students: 33, subject: 'GS4',
    desc: 'Case studies + conceptual questions. Ethics, Integrity, Aptitude.',
    avgScore: 5.9,
  },
  {
    id: 5, name: 'Economy Sprint Test', papers: 1, questions: 8,
    date: 'Mar 5, 2026', status: 'completed', students: 29, subject: 'GS3',
    desc: 'Indian Economy, Budget 2025–26, and Haryana economic policy.',
    avgScore: 6.1,
  },
];

const UPCOMING_SCHEDULE = [
  { date: 'Mar 20', event: 'HCS Mock Series 1 — Paper 1 (GS1)',      time: '10:00 AM' },
  { date: 'Mar 21', event: 'HCS Mock Series 1 — Paper 2 (GS2)',      time: '10:00 AM' },
  { date: 'Mar 27', event: 'HCS Mock Series 1 — Papers 3 & 4 (GS3+GS4)', time: '10:00 AM' },
  { date: 'Apr 3',  event: 'HCS Mock Series 2 — Paper 1 (GS1)',      time: '10:00 AM' },
];

export default function TestSeriesPage({ onNavigate }) {
  const [tab, setTab] = useState('all');

  const displayed = tab === 'all' ? SERIES
    : tab === 'upcoming' ? SERIES.filter(s => s.status === 'upcoming')
    : SERIES.filter(s => s.status === 'completed');

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Layers size={22} /> Test Series</h1>
          <p className="page-description">HCS Mains mock tests with AI evaluation for every answer</p>
        </div>
        <span className="badge badge-warning"><Clock size={11} /> 2 Upcoming</span>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total Series',    value: SERIES.length,                                          color: 'var(--primary)', icon: Layers },
          { label: 'Completed',       value: SERIES.filter(s=>s.status==='completed').length,        color: 'var(--success)', icon: CheckCircle2 },
          { label: 'Upcoming',        value: SERIES.filter(s=>s.status==='upcoming').length,         color: 'var(--warning)', icon: Clock },
          { label: 'Total Questions', value: SERIES.reduce((a,s)=>a+s.questions,0),                 color: 'var(--accent)',  icon: FileText },
        ].map(s => (
          <div key={s.label} className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</span>
              <s.icon size={14} style={{ color: s.color, opacity: 0.7 }} />
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        {/* Series List */}
        <div>
          <div className="tabs mb-4">
            {[['all','All Tests'],['upcoming','Upcoming'],['completed','Completed']].map(([id, label]) => (
              <button key={id} className={`tab ${tab===id?'active':''}`} onClick={() => setTab(id)}>{label}</button>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {displayed.map(s => (
              <div key={s.id} className="card">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 'var(--radius-md)', flexShrink: 0,
                    background: s.status === 'completed' ? 'var(--success-subtle)' : 'var(--primary-subtle)',
                    border: `1px solid ${s.status === 'completed' ? 'rgba(0,200,150,0.2)' : 'rgba(79,125,255,0.2)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: s.status === 'completed' ? 'var(--success)' : 'var(--primary)',
                  }}>
                    {s.status === 'completed' ? <CheckCircle2 size={20} /> : <Lock size={20} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600 }}>{s.name}</span>
                      <span className={`badge ${s.status === 'completed' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                        {s.status}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 10, lineHeight: 1.5 }}>{s.desc}</p>
                    <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                      <span><FileText size={11} style={{ display: 'inline', marginRight: 4 }} />{s.papers} papers · {s.questions} questions</span>
                      <span><Calendar size={11} style={{ display: 'inline', marginRight: 4 }} />{s.date}</span>
                      <span><Users size={11} style={{ display: 'inline', marginRight: 4 }} />{s.students} students enrolled</span>
                      {s.avgScore && <span style={{ color: s.avgScore >= 7 ? 'var(--success)' : 'var(--warning)' }}>
                        <BarChart3 size={11} style={{ display: 'inline', marginRight: 4 }} />Batch avg: {s.avgScore}/10
                      </span>}
                    </div>
                  </div>
                  <button
                    className={`btn btn-sm ${s.status === 'completed' ? 'btn-secondary' : 'btn-ghost'}`}
                    style={{ flexShrink: 0 }}
                    disabled={s.status === 'upcoming'}
                    onClick={() => s.status === 'completed' && onNavigate?.('submissions')}
                  >
                    {s.status === 'completed' ? <><ArrowRight size={13} /> Results</> : <><Lock size={12} /> Locked</>}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Upcoming Schedule */}
          <div className="card">
            <h4 style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={15} style={{ color: 'var(--primary)' }} /> Upcoming Schedule
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {UPCOMING_SCHEDULE.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 10 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 'var(--radius-sm)', flexShrink: 0,
                    background: 'var(--primary-subtle)', border: '1px solid rgba(79,125,255,0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.6rem', fontWeight: 700, color: 'var(--primary)', textAlign: 'center', lineHeight: 1.1
                  }}>{item.date.split(' ').map((w,j) => <span key={j} style={{ display: 'block' }}>{w}</span>)}</div>
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 500, lineHeight: 1.4 }}>{item.event}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="card" style={{ background: 'var(--primary-subtle)', border: '1px solid rgba(79,125,255,0.2)', textAlign: 'center', padding: 22 }}>
            <Zap size={28} style={{ color: 'var(--primary)', margin: '0 auto 10px' }} />
            <div style={{ fontWeight: 600, marginBottom: 6, fontSize: '0.9rem' }}>Practice Anytime</div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 14, lineHeight: 1.5 }}>
              Don't wait for test series. Upload and evaluate any answer now.
            </p>
            <button className="btn btn-primary btn-sm w-full" onClick={() => onNavigate?.('upload')}>
              <Zap size={13} /> Evaluate Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
