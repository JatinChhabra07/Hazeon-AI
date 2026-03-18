import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Upload, FileText, Users, Trophy,
  BookOpen, BookMarked, Calendar, Archive, LogOut, Layers, BrainCircuit
} from 'lucide-react';

const NAV = [
  {
    section: 'Core',
    items: [
      { id: 'dashboard',   icon: LayoutDashboard, label: 'Dashboard' },
      { id: 'upload',      icon: Upload,          label: 'Evaluate Answer', badge: 'AI' },
      { id: 'submissions', icon: FileText,        label: 'Submissions' },
    ],
  },
  {
    section: 'Institute',
    items: [
      { id: 'students',    icon: Users,           label: 'Students' },
      { id: 'topper',      icon: Trophy,          label: 'Topper Database' },
      { id: 'questions',   icon: BookMarked,      label: 'Question Bank', adminOnly: true },
      { id: 'test-series', icon: Layers,          label: 'Test Series' },
      { id: 'mcq-gen',     icon: BrainCircuit,    label: 'MCQ Generator', badge: 'NEW' },
    ],
  },
  {
    section: 'Preparation',
    items: [
      { id: 'pyq',         icon: BookOpen,        label: 'PYQ Bank' },
      { id: 'planner',     icon: Calendar,        label: 'Study Planner' },
      { id: 'resources',   icon: Archive,         label: 'Resources' },
    ],
  },
];

export default function Sidebar({ user, activePage, setActivePage, onLogout, isOpen, onClose }) {
  const navigate = useNavigate();
  const initials = user?.full_name
    ?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'U';

  const roleLabel = {
    student: 'Student',
    institute_admin: 'Institute Admin',
    super_admin: 'Super Admin',
  }[user?.role] || 'User';

  return (
    <>
    {isOpen && <div className={`sidebar-overlay open`} onClick={onClose} />}
    <aside className={`sidebar${isOpen ? ' open' : ''}`}>
      <div className="sidebar-logo">
        <div className="logo-mark" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">HZ</div>
          <div>
            <div className="logo-text">Hazeon AI</div>
            <div className="logo-sub">UPSC · HCS Evaluator</div>
          </div>
        </div>
      </div>

      {NAV.map(({ section, items }) => (
        <div key={section} className="nav-section">
          <div className="nav-section-label">{section}</div>
          {items.filter(item => !item.adminOnly || ['institute_admin', 'super_admin'].includes(user?.role)).map(({ id, icon: Icon, label, badge }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? 'active' : ''}`}
              onClick={() => setActivePage(id)}
            >
              <Icon size={16} />
              <span style={{ flex: 1 }}>{label}</span>
              {badge && <span className="nav-badge">{badge}</span>}
            </button>
          ))}
        </div>
      ))}

      <div className="sidebar-footer">
        <div className="user-card" onClick={onLogout} title="Click to logout">
          <div className="avatar">{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="user-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.full_name || 'User'}
            </div>
            <div className="user-role">{roleLabel}</div>
          </div>
          <LogOut size={13} style={{ color: 'var(--text-disabled)', flexShrink: 0 }} />
        </div>
      </div>
    </aside>
    </>
  );
}
