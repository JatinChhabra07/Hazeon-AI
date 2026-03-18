import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Search, Bell, Zap, Menu } from 'lucide-react';
import './index.css';

import LandingPage    from './components/LandingPage';
import AuthPage       from './components/AuthPage';
import Sidebar        from './components/Sidebar';
import DashboardPage  from './components/DashboardPage';
import UploadPage     from './components/UploadPage';
import SubmissionsPage from './components/SubmissionsPage';
import StudentsPage   from './components/StudentsPage';
import TopperPage     from './components/TopperPage';
import TestSeriesPage from './components/TestSeriesPage';
import PYQPage        from './components/PYQPage';
import PlannerPage    from './components/PlannerPage';
import ResourcesPage  from './components/ResourcesPage';
import MCQGeneratorPage from './components/MCQGeneratorPage';
import QuestionsPage   from './components/QuestionsPage';

export default function App() {
  const [user, setUser]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [activePage, setActivePage]   = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications]               = useState(3);

  useEffect(() => {
    const saved = localStorage.getItem('hazeon_user');
    if (saved) { try { setUser(JSON.parse(saved)); } catch {} }
    setLoading(false);
  }, []);

  if (loading) return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-base)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, var(--primary), var(--accent))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: 'white', margin: '0 auto 12px', fontSize: '0.9rem' }}>HZ</div>
        <div className="spinner" style={{ width: 20, height: 20, margin: '0 auto' }} />
      </div>
    </div>
  );

  const handleLogin  = (u) => { setUser(u); setActivePage('dashboard'); };
  const handleLogout = () => {
    localStorage.removeItem('hazeon_token');
    localStorage.removeItem('hazeon_user');
    setUser(null);
    setActivePage('dashboard');
  };

  const PAGE_NAMES = {
    dashboard:    'Dashboard',
    upload:       'Evaluate Answer',
    submissions:  'Submissions',
    students:     'Students',
    topper:       'Topper Database',
    'test-series':'Test Series',
    'mcq-gen':    'MCQ Generator',
    questions:    'Question Bank',
    pyq:          'PYQ Bank',
    planner:      'Study Planner',
    resources:    'Resources',
  };

  const renderPage = () => {
    const nav = setActivePage;
    switch (activePage) {
      case 'dashboard':    return <DashboardPage  user={user} onNavigate={nav} />;
      case 'upload':       return <UploadPage     onEvaluated={() => nav('submissions')} onNavigate={nav} />;
      case 'submissions':  return <SubmissionsPage onNavigate={nav} />;
      case 'students':     return <StudentsPage   onNavigate={nav} />;
      case 'topper':       return <TopperPage     onNavigate={nav} />;
      case 'test-series':  return <TestSeriesPage onNavigate={nav} />;
      case 'pyq':          return <PYQPage        onNavigate={nav} />;
      case 'planner':      return <PlannerPage    onNavigate={nav} />;
      case 'resources':    return <ResourcesPage    onNavigate={nav} />;
      case 'mcq-gen':      return <MCQGeneratorPage onNavigate={nav} />;
      case 'questions':    return <QuestionsPage    user={user} onNavigate={nav} />;
      default:             return <DashboardPage    user={user} onNavigate={nav} />;
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={
          user ? <Navigate to="/dashboard" /> : <AuthPage onLogin={handleLogin} />
        } />

        <Route path="/dashboard" element={
          user ? (
            <div className="app-shell">
              <Sidebar
                user={user}
                activePage={activePage}
                setActivePage={(p) => { setActivePage(p); setSidebarOpen(false); }}
                onLogout={handleLogout}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
              />
              <div className="main-content">
                <header className="topbar">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button className="hamburger-btn" onClick={() => setSidebarOpen(true)}>
                      <Menu size={20} />
                    </button>
                    <div className="topbar-breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Hazeon</span>
                      <span style={{ color: 'var(--text-muted)' }}>/</span>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{PAGE_NAMES[activePage]}</span>
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }} className="topbar-page-title">
                      {PAGE_NAMES[activePage]}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div className="search-box">
                      <Search size={13} style={{ color: 'var(--text-muted)' }} />
                      <input type="text" placeholder="Search..." />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }} className="badge badge-accent">
                      <Zap size={11} /><span>AI Ready</span>
                    </div>
                    <button className="btn btn-ghost" style={{ padding: 6, minHeight: 'auto', position: 'relative' }}>
                      <Bell size={16} />
                      {notifications > 0 && (
                        <span style={{
                          position: 'absolute', top: 2, right: 2,
                          width: 8, height: 8, borderRadius: '50%',
                          background: 'var(--error)', border: '2px solid var(--bg-surface)'
                        }} />
                      )}
                    </button>
                  </div>
                </header>

                <main className="scroll-area animate-in">
                  {renderPage()}
                </main>
              </div>
            </div>
          ) : <Navigate to="/login" />
        } />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
