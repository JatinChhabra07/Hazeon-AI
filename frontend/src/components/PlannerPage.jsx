import { useState } from 'react';
import { Calendar, Clock, CheckCircle2, Circle, Plus, Target, Flame, TrendingUp, BookOpen, Zap } from 'lucide-react';

const INITIAL_TASKS = [
  { id: 1, text: 'Write answer on Good Governance (GS2)',  done: true,  subject: 'GS2', time: '30 min', priority: 'high' },
  { id: 2, text: 'Revise Economy notes — Chapter 5',       done: true,  subject: 'GS3', time: '45 min', priority: 'medium' },
  { id: 3, text: 'Submit Ethics case study answer',        done: false, subject: 'GS4', time: '25 min', priority: 'high' },
  { id: 4, text: 'Read The Hindu — Editorial analysis',    done: false, subject: 'Current Affairs', time: '30 min', priority: 'medium' },
  { id: 5, text: 'Mock test — GS1 Society section',        done: false, subject: 'GS1', time: '60 min', priority: 'low' },
];

const SCHEDULE = [
  { day: 'Mon', focus: 'GS1 — History & Society',    status: 'done' },
  { day: 'Tue', focus: 'GS2 — Governance & Polity',  status: 'done' },
  { day: 'Wed', focus: 'GS3 — Economy & Env',        status: 'today' },
  { day: 'Thu', focus: 'GS4 — Ethics',               status: 'pending' },
  { day: 'Fri', focus: 'Current Affairs Review',     status: 'pending' },
  { day: 'Sat', focus: 'Full Mock Test',             status: 'pending' },
  { day: 'Sun', focus: 'Revision + Answer Writing',  status: 'pending' },
];

const GOALS = [
  { subject: 'GS2 Governance', target: 8.0, current: 7.1, color: 'var(--primary)' },
  { subject: 'GS3 Economy',    target: 7.5, current: 6.4, color: 'var(--accent)' },
  { subject: 'GS4 Ethics',     target: 7.0, current: 5.9, color: 'var(--warning)' },
  { subject: 'GS1 Society',    target: 7.5, current: 6.9, color: 'var(--success)' },
];

const PRIORITY_COLOR = { high: 'var(--error)', medium: 'var(--warning)', low: 'var(--text-muted)' };

export default function PlannerPage({ onNavigate }) {
  const [tasks, setTasks]         = useState(INITIAL_TASKS);
  const [showAdd, setShowAdd]     = useState(false);
  const [newTask, setNewTask]     = useState('');
  const [newSubject, setNewSubject] = useState('GS1');
  const [newTime, setNewTime]     = useState('30 min');

  const done = tasks.filter(t => t.done).length;
  const pct  = Math.round((done / tasks.length) * 100);

  const toggleTask = (id) => setTasks(ts => ts.map(t => t.id === id ? { ...t, done: !t.done } : t));

  const addTask = () => {
    if (!newTask.trim()) return;
    setTasks(ts => [...ts, { id: Date.now(), text: newTask, done: false, subject: newSubject, time: newTime, priority: 'medium' }]);
    setNewTask(''); setShowAdd(false);
  };

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Calendar size={22} /> Study Planner</h1>
          <p className="page-description">Track your daily preparation — {done}/{tasks.length} tasks done today</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(s => !s)}>
          <Plus size={14} /> Add Task
        </button>
      </div>

      {/* Add Task Panel */}
      {showAdd && (
        <div className="card mb-4 fade-in" style={{ borderLeft: '3px solid var(--primary)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div className="form-label" style={{ marginBottom: 6 }}>Task</div>
              <input className="form-input" placeholder="e.g. Write answer on Federalism..." value={newTask} onChange={e => setNewTask(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addTask()} autoFocus />
            </div>
            <div>
              <div className="form-label" style={{ marginBottom: 6 }}>Subject</div>
              <select className="form-input" style={{ width: 130 }} value={newSubject} onChange={e => setNewSubject(e.target.value)}>
                {['GS1','GS2','GS3','GS4','Current Affairs','Optional'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <div className="form-label" style={{ marginBottom: 6 }}>Time</div>
              <select className="form-input" style={{ width: 110 }} value={newTime} onChange={e => setNewTime(e.target.value)}>
                {['15 min','30 min','45 min','60 min','90 min','2 hours'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={addTask}>Add</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Progress banner */}
      <div className="card mb-6" style={{ background: 'linear-gradient(135deg, var(--primary-subtle), var(--accent-subtle))', border: '1px solid rgba(79,125,255,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 2 }}>Today's Progress</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{done}/{tasks.length} tasks · {tasks.filter(t=>!t.done).length} remaining</div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: pct >= 80 ? 'var(--success)' : pct >= 50 ? 'var(--primary)' : 'var(--warning)' }}>
            {pct}%
          </div>
        </div>
        <div className="score-bar" style={{ height: 8 }}>
          <div className="score-bar-fill" style={{ width: `${pct}%`, background: pct >= 80 ? 'var(--success)' : 'var(--primary)' }} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Today's Tasks */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3>Today's Tasks</h3>
            <span className="badge badge-neutral">{tasks.filter(t=>!t.done).length} left</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {tasks.map(t => (
              <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', cursor: 'pointer', opacity: t.done ? 0.55 : 1, transition: 'all 0.15s' }}
                onClick={() => toggleTask(t.id)}>
                {t.done
                  ? <CheckCircle2 size={18} style={{ color: 'var(--success)', flexShrink: 0 }} />
                  : <Circle size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                }
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 500, textDecoration: t.done ? 'line-through' : 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.text}</div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 3 }}>
                    <span className="badge badge-neutral" style={{ fontSize: '0.62rem' }}>{t.subject}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Clock size={10} />{t.time}
                    </span>
                  </div>
                </div>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: PRIORITY_COLOR[t.priority], flexShrink: 0 }} title={`${t.priority} priority`} />
              </div>
            ))}
          </div>
          <button className="btn btn-ghost btn-sm w-full mt-3" onClick={() => onNavigate?.('upload')}>
            <Zap size={13} /> Evaluate an answer now
          </button>
        </div>

        {/* Weekly Schedule */}
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Weekly Schedule</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {SCHEDULE.map(s => (
              <div key={s.day} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: s.status === 'today' ? 'var(--primary-subtle)' : 'var(--bg-elevated)',
                border: s.status === 'today' ? '1px solid rgba(79,125,255,0.2)' : '1px solid transparent',
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 'var(--radius-sm)', flexShrink: 0,
                  background: s.status === 'done' ? 'var(--success-subtle)' : s.status === 'today' ? 'var(--primary)' : 'var(--bg-hover)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.7rem', fontWeight: 700,
                  color: s.status === 'done' ? 'var(--success)' : s.status === 'today' ? 'white' : 'var(--text-muted)',
                }}>{s.day}</div>
                <div style={{ flex: 1, fontSize: '0.85rem', fontWeight: s.status === 'today' ? 600 : 400 }}>{s.focus}</div>
                {s.status === 'done'    && <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />}
                {s.status === 'today'  && <span className="badge badge-primary" style={{ fontSize: '0.62rem' }}>Today</span>}
                {s.status === 'pending' && <Clock size={13} style={{ color: 'var(--text-disabled)' }} />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Goals */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
          <Target size={16} style={{ color: 'var(--primary)' }} />
          <h3>Subject Score Goals</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {GOALS.map(g => {
            const pct = Math.min((g.current / g.target) * 100, 100);
            const gap = g.target - g.current;
            return (
              <div key={g.subject} className="card-flat" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>{g.subject}</div>
                <div style={{ position: 'relative', width: 72, height: 72, margin: '0 auto 12px' }}>
                  <svg width={72} height={72} style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx={36} cy={36} r={30} fill="none" stroke="var(--bg-elevated)" strokeWidth={6} />
                    <circle cx={36} cy={36} r={30} fill="none" stroke={g.color} strokeWidth={6}
                      strokeDasharray={`${pct * 1.885} 188.5`} strokeLinecap="round" style={{ transition: 'stroke-dasharray 0.8s ease' }} />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: g.color }}>{g.current}</span>
                  </div>
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Target: {g.target}</div>
                <div style={{ fontSize: '0.7rem', color: gap <= 0.3 ? 'var(--success)' : 'var(--warning)', marginTop: 3 }}>
                  {gap <= 0 ? '✓ Achieved!' : `${gap.toFixed(1)} pts to go`}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
