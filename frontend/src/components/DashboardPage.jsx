import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  TrendingUp, FileText, Users, ArrowRight, Award,
  Zap, CheckCircle2, Upload, BookOpen, BarChart3,
  ChevronRight, Flame, Star, TrendingDown, Cpu, Activity,
  AlertTriangle, Target
} from 'lucide-react';
import * as api from '../api';

const MOCK_TREND = [
  { date: 'Oct', score: 4.8 }, { date: 'Nov', score: 5.3 },
  { date: 'Dec', score: 5.9 }, { date: 'Jan', score: 6.2 },
  { date: 'Feb', score: 6.8 }, { date: 'Mar', score: 7.2 },
];

const MOCK_ANALYTICS = {
  total_students: 47,
  total_submissions: 312,
  total_evaluated: 289,
  average_score: 6.8,
  subject_performance: { 'GS2': 7.1, 'GS3': 6.4, 'GS1': 6.9, 'GS4': 5.8, 'IR': 6.2 },
  weak_areas: [
    { parameter: 'analysis_score',        avg_score: 5.2 },
    { parameter: 'conclusion_score',      avg_score: 5.8 },
    { parameter: 'diagram_score',         avg_score: 3.1 },
    { parameter: 'keyword_score',         avg_score: 5.9 },
    { parameter: 'multidimensional_score',avg_score: 6.1 },
    { parameter: 'factual_score',         avg_score: 6.3 },
  ],
  top_performers: [
    { student_id: 1, name: 'Priya Sharma',  submissions: 12, avg_score: 8.3 },
    { student_id: 2, name: 'Aman Verma',    submissions: 10, avg_score: 7.9 },
    { student_id: 3, name: 'Neha Gupta',    submissions: 8,  avg_score: 7.6 },
    { student_id: 4, name: 'Rohit Singh',   submissions: 9,  avg_score: 7.1 },
    { student_id: 5, name: 'Kavita Yadav',  submissions: 7,  avg_score: 6.8 },
  ],
};

const MOCK_PROGRESS = {
  total_submissions: 14,
  improvement_rate: 18.4,
  parameter_averages: {
    relevance_score: 7.2, structure_score: 7.8, keyword_score: 6.1,
    analysis_score: 5.9, conclusion_score: 5.4, factual_score: 6.8,
  },
  scores_over_time: MOCK_TREND,
};

const RECENT_ACTIVITY = [
  { question: 'Good Governance in Haryana', subject: 'GS2', score: 7.8, student: 'Priya Sharma', time: '2 hours ago', status: 'evaluated' },
  { question: 'Green Revolution Challenges', subject: 'GS3', score: 6.2, student: 'Aman Verma',   time: '4 hours ago', status: 'evaluated' },
  { question: 'Cooperative Federalism',      subject: 'GS2', score: null, student: 'Neha Gupta',   time: '5 hours ago', status: 'processing' },
  { question: 'Ethics in Civil Services',    subject: 'GS4', score: 8.1, student: 'Rohit Singh',  time: '6 hours ago', status: 'evaluated' },
  { question: 'Water Crisis in Haryana',     subject: 'GS3', score: 5.9, student: 'Kavita Yadav', time: '1 day ago',   status: 'evaluated' },
];

const AI_INSIGHTS = [
  {
    icon: AlertTriangle, color: '#ef4444',
    title: 'Weak Spot Detected',
    desc: '72% of students score below 5.5 in Diagram/Visual Aid. Schedule a diagram-writing workshop.',
  },
  {
    icon: Flame, color: '#f59e0b',
    title: 'Submission Spike',
    desc: '48 answers submitted today — 3× normal rate. Test series likely starting this week.',
  },
  {
    icon: Star, color: '#10b981',
    title: 'Top Performer',
    desc: 'Priya Sharma has improved by 2.1 points in 30 days — highest growth in your batch.',
  },
];

const PARAM_LABELS = {
  relevance_score: 'Relevance', intro_score: 'Introduction', body_score: 'Body',
  keyword_score: 'Keywords', structure_score: 'Structure', factual_score: 'Factual',
  conclusion_score: 'Conclusion', analysis_score: 'Analysis',
  multidimensional_score: 'Multi-Dim', diagram_score: 'Diagram',
};

function scoreColor(score) {
  if (score >= 7.5) return '#10b981';
  if (score >= 5.5) return '#f59e0b';
  return '#ef4444';
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good Morning';
  if (h < 17) return 'Good Afternoon';
  return 'Good Evening';
}

function getDisplayName(fullName) {
  if (!fullName) return 'there';
  const titles = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Shri', 'Smt.'];
  const parts = fullName.trim().split(' ');
  if (titles.some(t => t.toLowerCase() === parts[0].toLowerCase()) && parts.length > 1) {
    return `${parts[0]} ${parts[1]}`;
  }
  return parts[0];
}

/* ── Section Header ─────────────────────────────────── */
function SectionHeader({ title, badge, action, onAction }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#e8edf5', margin: 0 }}>{title}</h3>
        {badge && (
          <span style={{
            fontSize: '0.62rem', fontWeight: 700, padding: '2px 8px', borderRadius: 20,
            background: badge.bg, color: badge.color,
            border: `1px solid ${badge.border}`, textTransform: 'uppercase', letterSpacing: '0.05em',
          }}>{badge.text}</span>
        )}
      </div>
      {action && (
        <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.75rem', color: '#8fa3c0' }} onClick={onAction}>
          {action} <ArrowRight size={12} />
        </button>
      )}
    </div>
  );
}

/* ── Stat Card ──────────────────────────────────────── */
function StatCard({ label, value, icon, color, change, changeUp }) {
  return (
    <div style={{
      background: '#0e1420', border: '1px solid #1e2d45',
      borderTop: `2px solid ${color}`, borderRadius: 12,
      padding: '18px 20px', position: 'relative', overflow: 'hidden',
      transition: 'transform 0.18s, box-shadow 0.18s',
    }}
    onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)'; }}
    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
        <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#5a7a9a', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
        <div style={{ width: 30, height: 30, borderRadius: 8, background: `${color}1a`, border: `1px solid ${color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center', color, flexShrink: 0 }}>
          {icon}
        </div>
      </div>
      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f0f4ff', lineHeight: 1, marginBottom: 8 }}>{value}</div>
      {change && (
        <div style={{ fontSize: '0.73rem', color: changeUp ? '#10b981' : '#8fa3c0', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 4 }}>
          {changeUp && <TrendingUp size={11} />}
          {change}
        </div>
      )}
    </div>
  );
}

/* ── Main Component ─────────────────────────────────── */
export default function DashboardPage({ user, onNavigate }) {
  const isAdmin = user?.role === 'institute_admin' || user?.role === 'super_admin';

  // Pre-fill with mock so the page renders instantly — real data replaces silently
  const [analytics,  setAnalytics]  = useState(MOCK_ANALYTICS);
  const [progress,   setProgress]   = useState(MOCK_PROGRESS);
  const [refreshing, setRefreshing] = useState(true);
  const [usingMock,  setUsingMock]  = useState(false);

  useEffect(() => {
    setRefreshing(true);
    setUsingMock(false);
    const load = async () => {
      try {
        if (isAdmin) {
          const res = await api.getBatchAnalytics();
          setAnalytics(res.data);
        } else {
          const res = await api.getStudentProgress(user?.id);
          setProgress(res.data);
        }
      } catch {
        setUsingMock(true); // keep mock data, show notice
      }
      setRefreshing(false);
    };
    load();
  }, [user?.id, user?.role]); // eslint-disable-line react-hooks/exhaustive-deps

  const displayName = getDisplayName(user?.full_name);
  const data = isAdmin ? analytics : progress;
  const todayStr = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const roleLabel = { student: 'Student', institute_admin: 'Faculty', super_admin: 'Director' }[user?.role] || 'User';

  const adminPills = [
    { label: 'Students',    value: data?.total_students || 0,                             color: '#4f7dff' },
    { label: 'Submissions', value: data?.total_submissions || 0,                          color: '#00d4ff' },
    { label: 'Evaluated',   value: data?.total_evaluated || 0,                            color: '#10b981' },
    { label: 'Avg Score',   value: `${(data?.average_score || 0).toFixed(1)}/10`,         color: '#f59e0b' },
  ];
  const studentPills = [
    { label: 'Answers Written',  value: data?.total_submissions || 0,                     color: '#4f7dff' },
    { label: 'Improvement',      value: `+${(data?.improvement_rate || 0).toFixed(1)}%`,  color: '#10b981' },
    { label: 'Practice Streak',  value: '7 days',                                         color: '#f59e0b' },
  ];
  const pills = isAdmin ? adminPills : studentPills;

  return (
    <div className="animate-in">

      {/* Slim progress bar while live data loads — doesn't block render */}
      {refreshing && (
        <div style={{ height: 2, background: '#1e2d45', borderRadius: 2, marginBottom: 14, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: '60%', background: 'linear-gradient(90deg, #4f7dff, #00d4ff)', borderRadius: 2, animation: 'shimmer 1.2s ease-in-out infinite' }} />
        </div>
      )}

      {/* Mock-data notice — shown when API failed and demo data is being displayed */}
      {usingMock && (
        <div style={{
          background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: 8, padding: '8px 14px', marginBottom: 14,
          fontSize: '0.8rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>⚠</span> Live data unavailable — showing demo figures. Refresh to retry.
          <button onClick={() => { setUsingMock(false); setRefreshing(true); }} style={{
            marginLeft: 'auto', background: 'none', border: '1px solid rgba(245,158,11,0.4)',
            borderRadius: 4, color: '#f59e0b', fontSize: '0.75rem', cursor: 'pointer', padding: '2px 8px',
          }}>Refresh</button>
        </div>
      )}

      {/* ══ WELCOME BANNER ════════════════════════════════════ */}
      <div style={{
        background: 'linear-gradient(135deg, #0d1220 0%, #111827 60%, #0d1220 100%)',
        border: '1px solid #1e2d45',
        borderTop: '2px solid #4f7dff',
        borderRadius: 14, padding: '28px 32px',
        marginBottom: 20, position: 'relative', overflow: 'hidden',
      }}>
        {/* Decorative blobs */}
        <div style={{ position: 'absolute', right: -40, top: -40, width: 220, height: 220, borderRadius: '50%', background: 'radial-gradient(circle, rgba(79,125,255,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', right: 80, bottom: -50, width: 150, height: 150, borderRadius: '50%', background: 'radial-gradient(circle, rgba(0,212,255,0.05) 0%, transparent 70%)', pointerEvents: 'none' }} />

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', position: 'relative' }}>
          <div>
            {/* Status + date row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
                <span style={{ fontSize: '0.7rem', color: '#8fa3c0', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
                  {greeting()}
                </span>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#4a6480', fontFamily: 'monospace' }}>{todayStr}</span>
            </div>

            {/* Name */}
            <h1 style={{ fontSize: '2.1rem', fontWeight: 800, color: '#f0f4ff', marginBottom: 8, letterSpacing: '-0.02em', lineHeight: 1 }}>
              {displayName}
            </h1>

            {/* Role + institute */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
              <span style={{
                fontSize: '0.68rem', fontWeight: 800, padding: '3px 11px', borderRadius: 20,
                background: 'rgba(79,125,255,0.12)', color: '#4f7dff',
                border: '1px solid rgba(79,125,255,0.25)', textTransform: 'uppercase', letterSpacing: '0.07em',
              }}>{roleLabel}</span>
              <span style={{ color: '#4a6480', fontSize: '0.75rem', fontWeight: 500 }}>UPSC · HCS Mains Evaluator</span>
            </div>

            {/* Key metrics row */}
            <div style={{ display: 'flex', gap: 0 }}>
              {pills.map((pill, i) => (
                <div key={pill.label} style={{
                  display: 'flex', flexDirection: 'column', gap: 3,
                  padding: `0 ${i === 0 ? 0 : 24}px 0 ${i === 0 ? 0 : 24}px`,
                  borderLeft: i > 0 ? '1px solid #1e2d45' : 'none',
                  marginLeft: i > 0 ? 0 : 0,
                }}>
                  <span style={{ fontSize: '1.3rem', fontWeight: 800, color: pill.color, lineHeight: 1 }}>{pill.value}</span>
                  <span style={{ fontSize: '0.65rem', color: '#5a7a9a', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 700 }}>{pill.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* CTA buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flexShrink: 0 }}>
            <button className="btn btn-primary" style={{ minWidth: 168, fontWeight: 600 }} onClick={() => onNavigate?.('upload')}>
              <Upload size={14} /> Evaluate Answer
            </button>
            <button className="btn btn-secondary" style={{ minWidth: 168, fontWeight: 600 }} onClick={() => onNavigate?.('submissions')}>
              <FileText size={14} /> View History
            </button>
          </div>
        </div>
      </div>

      {/* ══ QUICK ACTIONS ═════════════════════════════════════ */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 22 }}>
        {[
          { icon: Cpu,      label: 'Evaluate Answer', sub: 'Upload & get AI feedback',  color: '#4f7dff', badge: 'AI',  page: 'upload' },
          { icon: BookOpen, label: 'PYQ Bank',        sub: 'Practice past questions',   color: '#00d4ff', badge: null,  page: 'pyq' },
          { icon: Award,    label: 'Topper Answers',  sub: 'Benchmark answer keys',     color: '#f59e0b', badge: null,  page: 'topper' },
          { icon: BarChart3,label: 'Test Series',     sub: 'Mock tests & schedules',    color: '#10b981', badge: 'New', page: 'test-series' },
        ].map(item => (
          <button key={item.page} onClick={() => onNavigate?.(item.page)} style={{
            background: '#0e1420', border: '1px solid #1e2d45',
            borderBottom: `2px solid ${item.color}`,
            borderRadius: 12, padding: '18px 20px',
            cursor: 'pointer', textAlign: 'left',
            display: 'flex', flexDirection: 'column',
            transition: 'all 0.18s ease',
            fontFamily: 'inherit', position: 'relative',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = '#141b2d'; e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 8px 20px rgba(0,0,0,0.3)`; }}
          onMouseLeave={e => { e.currentTarget.style.background = '#0e1420'; e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
          >
            {item.badge && (
              <span style={{
                position: 'absolute', top: 13, right: 13,
                fontSize: '0.58rem', fontWeight: 800, padding: '2px 7px', borderRadius: 10,
                background: `${item.color}20`, color: item.color,
                border: `1px solid ${item.color}40`, textTransform: 'uppercase', letterSpacing: '0.05em',
              }}>{item.badge}</span>
            )}
            <div style={{
              width: 40, height: 40, borderRadius: 10,
              background: `${item.color}15`, border: `1px solid ${item.color}25`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 14, color: item.color,
            }}>
              <item.icon size={19} />
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#e8edf5', marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: '0.75rem', color: '#6b8aaa', lineHeight: 1.4, marginBottom: 14 }}>{item.sub}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.72rem', color: item.color, fontWeight: 700 }}>
              Open <ChevronRight size={12} />
            </div>
          </button>
        ))}
      </div>

      {/* ══ STATS ROW ═════════════════════════════════════════ */}
      {isAdmin ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 22 }}>
          <StatCard label="Total Students"   value={data?.total_students || 0}   icon={<Users size={15}/>}        color="#4f7dff" change="+3 this month" changeUp />
          <StatCard label="Total Submissions" value={data?.total_submissions || 0} icon={<FileText size={15}/>}   color="#00d4ff" change="Across all batches" />
          <StatCard label="Evaluated"         value={data?.total_evaluated || 0}   icon={<CheckCircle2 size={15}/>} color="#10b981"
            change={`${data?.total_submissions ? Math.round((data.total_evaluated / data.total_submissions) * 100) : 0}% completion rate`} changeUp />
          <StatCard label="Avg Score"         value={`${(data?.average_score || 0).toFixed(1)}/10`} icon={<Award size={15}/>} color="#f59e0b" change="Batch average" />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 22 }}>
          <StatCard label="Answers Written"  value={data?.total_submissions || 0} icon={<FileText size={15}/>}   color="#4f7dff" />
          <StatCard label="Avg Score"        value={`${(Object.values(data?.parameter_averages || {}).reduce((a,b)=>a+b,0) / (Object.values(data?.parameter_averages || {}).length || 1)).toFixed(1)}/10`}
                    icon={<Award size={15}/>} color="#10b981" />
          <StatCard label="Improvement"      value={`${(data?.improvement_rate||0) > 0 ? '+' : ''}${(data?.improvement_rate||0).toFixed(1)}%`} icon={<TrendingUp size={15}/>} color="#f59e0b" changeUp />
          <StatCard label="Practice Streak"  value="7 days" icon={<Flame size={15}/>} color="#ef4444" change="Keep it up!" />
        </div>
      )}

      {isAdmin ? (
        <>
          {/* ══ CHARTS ROW ════════════════════════════════════ */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 22 }}>

            {/* Subject Performance */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader
                title="Subject Performance"
                badge={{ text: 'Avg /10', bg: '#1e2d45', color: '#8fa3c0', border: '#2a3d58' }}
              />
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(data?.subject_performance || {}).map(([s, v]) => ({ subject: s, avg: parseFloat(v.toFixed(1)) }))} barSize={32}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" vertical={false} />
                  <XAxis dataKey="subject" tick={{ fill: '#6b8aaa', fontSize: 11, fontWeight: 600 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 10]} tick={{ fill: '#6b8aaa', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#141b2d', border: '1px solid #1e2d45', borderRadius: 8, color: '#e8edf5', fontSize: '0.8rem' }}
                    cursor={{ fill: 'rgba(79,125,255,0.06)' }}
                    formatter={(v) => [`${v}/10`, 'Avg Score']}
                  />
                  <Bar dataKey="avg" fill="#4f7dff" radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Weak Areas */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader
                title="Weak Areas"
                badge={{ text: 'Needs Attention', bg: 'rgba(239,68,68,0.1)', color: '#ef4444', border: 'rgba(239,68,68,0.25)' }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(data?.weak_areas || []).slice(0, 6).map(wa => (
                  <div key={wa.parameter} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ width: 76, fontSize: '0.75rem', color: '#8fa3c0', fontWeight: 600, flexShrink: 0 }}>
                      {PARAM_LABELS[wa.parameter] || wa.parameter}
                    </span>
                    <div style={{ flex: 1, height: 6, background: '#1e2d45', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${wa.avg_score * 10}%`, height: '100%', background: scoreColor(wa.avg_score), borderRadius: 4, transition: 'width 0.6s ease' }} />
                    </div>
                    <span style={{ width: 28, fontSize: '0.8rem', fontWeight: 700, color: scoreColor(wa.avg_score), textAlign: 'right', flexShrink: 0 }}>
                      {wa.avg_score.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ══ BOTTOM ROW ════════════════════════════════════ */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 22 }}>

            {/* Top Performers */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader title="Top Performers" action="All Students" onAction={() => onNavigate?.('students')} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(data?.top_performers || []).slice(0, 5).map((p, i) => (
                  <div key={p.student_id ?? i} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '10px 12px', borderRadius: 10,
                    background: i === 0 ? 'rgba(79,125,255,0.07)' : '#141b2d',
                    border: i === 0 ? '1px solid rgba(79,125,255,0.2)' : '1px solid transparent',
                  }}>
                    <div style={{ width: 22, textAlign: 'center', fontSize: '0.72rem', fontWeight: 800, color: i < 3 ? '#f59e0b' : '#4a6480', flexShrink: 0 }}>
                      #{i + 1}
                    </div>
                    <div style={{
                      width: 32, height: 32, borderRadius: '50%',
                      background: `linear-gradient(135deg, #4f7dff, #00d4ff)`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.65rem', fontWeight: 800, color: 'white', flexShrink: 0,
                    }}>
                      {p.name.split(' ').map(w => w[0]).join('').slice(0, 2)}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#e8edf5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                      <div style={{ fontSize: '0.7rem', color: '#5a7a9a', marginTop: 1 }}>{p.submissions} submissions</div>
                    </div>
                    <div style={{
                      fontSize: '0.92rem', fontWeight: 800, color: scoreColor(p.avg_score),
                      background: `${scoreColor(p.avg_score)}15`, padding: '2px 10px',
                      borderRadius: 20, border: `1px solid ${scoreColor(p.avg_score)}30`, flexShrink: 0,
                    }}>{p.avg_score.toFixed(1)}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader title="Recent Activity" action="View All" onAction={() => onNavigate?.('submissions')} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {RECENT_ACTIVITY.map((act, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: i < RECENT_ACTIVITY.length - 1 ? '1px solid #1a2540' : 'none' }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: act.status === 'evaluated' ? '#10b981' : '#f59e0b',
                      boxShadow: `0 0 5px ${act.status === 'evaluated' ? '#10b981' : '#f59e0b'}`,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#d4dff0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{act.question}</div>
                      <div style={{ fontSize: '0.7rem', color: '#5a7a9a', marginTop: 2 }}>{act.student} · {act.time}</div>
                    </div>
                    <span style={{
                      fontSize: '0.62rem', fontWeight: 700, padding: '2px 8px', borderRadius: 10,
                      background: 'rgba(79,125,255,0.12)', color: '#4f7dff',
                      border: '1px solid rgba(79,125,255,0.25)', flexShrink: 0,
                    }}>{act.subject}</span>
                    {act.score != null ? (
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, color: scoreColor(act.score), flexShrink: 0, minWidth: 28, textAlign: 'right' }}>{act.score}</span>
                    ) : (
                      <span style={{ fontSize: '0.65rem', color: '#f59e0b', fontWeight: 600, flexShrink: 0 }}>...</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ══ AI INSIGHTS ═══════════════════════════════════ */}
          <div style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Activity size={15} style={{ color: '#4f7dff' }} />
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#e8edf5', margin: 0 }}>AI Insights</h3>
              <span style={{ fontSize: '0.62rem', fontWeight: 700, padding: '2px 8px', borderRadius: 10, background: 'rgba(79,125,255,0.12)', color: '#4f7dff', border: '1px solid rgba(79,125,255,0.25)' }}>Powered by Gemini</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
              {AI_INSIGHTS.map(insight => (
                <div key={insight.title} style={{
                  background: '#0e1420', borderRadius: 12,
                  border: '1px solid #1e2d45', borderLeft: `3px solid ${insight.color}`,
                  padding: '18px 20px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: 8, background: `${insight.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <insight.icon size={14} style={{ color: insight.color }} />
                    </div>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#e8edf5' }}>{insight.title}</span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#7a9ab8', lineHeight: 1.6, margin: 0 }}>{insight.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        /* ══ STUDENT VIEW ═════════════════════════════════════ */
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 22 }}>

            {/* Score Trend */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader
                title="Score Trend"
                badge={{ text: '+18.4% this month', bg: 'rgba(16,185,129,0.1)', color: '#10b981', border: 'rgba(16,185,129,0.25)' }}
              />
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={data?.scores_over_time || MOCK_TREND}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#4f7dff" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#4f7dff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: '#6b8aaa', fontSize: 11, fontWeight: 600 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 10]} tick={{ fill: '#6b8aaa', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#141b2d', border: '1px solid #1e2d45', borderRadius: 8, color: '#e8edf5', fontSize: '0.8rem' }} />
                  <Area type="monotone" dataKey="score" stroke="#4f7dff" strokeWidth={2.5} fill="url(#scoreGrad)" dot={{ fill: '#4f7dff', r: 4, strokeWidth: 2, stroke: '#141b2d' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Parameter Breakdown */}
            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader title="Parameter Breakdown" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {Object.entries(data?.parameter_averages || {
                  relevance_score: 6.2, structure_score: 7.1, keyword_score: 5.8,
                  analysis_score: 6.5, conclusion_score: 5.2
                }).slice(0, 6).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ width: 76, fontSize: '0.75rem', color: '#8fa3c0', fontWeight: 600, flexShrink: 0 }}>
                      {PARAM_LABELS[k] || k}
                    </span>
                    <div style={{ flex: 1, height: 6, background: '#1e2d45', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${v * 10}%`, height: '100%', background: scoreColor(v), borderRadius: 4, transition: 'width 0.6s ease' }} />
                    </div>
                    <span style={{ width: 28, fontSize: '0.8rem', fontWeight: 700, color: scoreColor(v), textAlign: 'right', flexShrink: 0 }}>{v.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Evaluations + Goal Card */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 22 }}>

            <div style={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 12, padding: '20px 22px' }}>
              <SectionHeader title="Recent Evaluations" action="All Submissions" onAction={() => onNavigate?.('submissions')} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {RECENT_ACTIVITY.slice(0, 4).map((act, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: i < 3 ? '1px solid #1a2540' : 'none' }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: act.score >= 7 ? '#10b981' : act.score ? '#f59e0b' : '#00d4ff',
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#d4dff0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{act.question}</div>
                      <div style={{ fontSize: '0.7rem', color: '#5a7a9a', marginTop: 2 }}>{act.time}</div>
                    </div>
                    <span style={{ fontSize: '0.62rem', fontWeight: 700, padding: '2px 8px', borderRadius: 10, background: 'rgba(79,125,255,0.12)', color: '#4f7dff', border: '1px solid rgba(79,125,255,0.25)', flexShrink: 0 }}>{act.subject}</span>
                    {act.score != null && (
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, color: scoreColor(act.score), flexShrink: 0 }}>{act.score}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Goal card */}
            <div style={{
              background: 'linear-gradient(145deg, #0d1a30, #111f38)',
              border: '1px solid rgba(79,125,255,0.2)',
              borderRadius: 12, padding: '22px',
              display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 38, height: 38, background: '#4f7dff', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Target size={18} color="white" />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#e8edf5' }}>Your Next Goal</div>
                    <div style={{ fontSize: '0.7rem', color: '#5a7a9a' }}>Personalised by AI</div>
                  </div>
                </div>
                <p style={{ fontSize: '0.82rem', color: '#8fa3c0', lineHeight: 1.7, margin: 0 }}>
                  You're <strong style={{ color: '#4f7dff' }}>1.2 points</strong> away from the topper average (8.4). Focus on{' '}
                  <strong style={{ color: '#f59e0b' }}>Analysis depth</strong> and{' '}
                  <strong style={{ color: '#f59e0b' }}>Conclusion quality</strong> — your two lowest-scoring parameters.
                </p>
              </div>
              <button className="btn btn-primary" style={{ marginTop: 20, fontWeight: 600 }} onClick={() => onNavigate?.('upload')}>
                <Zap size={14} /> Evaluate Now
              </button>
            </div>
          </div>

          {/* Student AI Insights */}
          <div style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Activity size={15} style={{ color: '#4f7dff' }} />
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#e8edf5', margin: 0 }}>AI Insights</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
              {[
                { icon: TrendingDown, color: '#ef4444', title: 'Weakest Area',  desc: 'Your Conclusion scores average 5.4. Add a structured "Way Forward" paragraph every time.' },
                { icon: AlertTriangle,color: '#f59e0b', title: 'Keyword Gap',   desc: "You're missing 40% of expected keywords on average. Study the PYQ model answers closely." },
                { icon: Star,         color: '#10b981', title: 'Best Subject',  desc: 'GS2 Governance is your strongest — avg 7.8. Use this momentum to boost GS3 Economy.' },
              ].map(insight => (
                <div key={insight.title} style={{
                  background: '#0e1420', borderRadius: 12,
                  border: '1px solid #1e2d45', borderLeft: `3px solid ${insight.color}`,
                  padding: '18px 20px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: 8, background: `${insight.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <insight.icon size={14} style={{ color: insight.color }} />
                    </div>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#e8edf5' }}>{insight.title}</span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#7a9ab8', lineHeight: 1.6, margin: 0 }}>{insight.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
