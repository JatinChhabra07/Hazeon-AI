import { Archive, Download, FileText, BookOpen, ExternalLink } from 'lucide-react';

const RESOURCES = [
  {
    category: 'Model Answers',
    items: [
      { title: 'GS2 Governance — Top 20 Questions 2025', type: 'PDF', size: '2.4 MB' },
      { title: 'GS3 Economy — Model Answer Booklet',     type: 'PDF', size: '3.1 MB' },
      { title: 'GS4 Ethics — Case Studies with Answers', type: 'PDF', size: '1.8 MB' },
    ],
  },
  {
    category: 'HCS Syllabus & Strategy',
    items: [
      { title: 'HCS Mains 2026 — Official Syllabus',      type: 'PDF', size: '0.4 MB' },
      { title: 'Subject-wise Preparation Strategy Guide', type: 'PDF', size: '1.2 MB' },
      { title: 'Answer Writing Framework — All GS Papers', type: 'PDF', size: '0.9 MB' },
    ],
  },
  {
    category: 'Current Affairs',
    items: [
      { title: 'February 2026 — Monthly Compilation', type: 'PDF', size: '4.2 MB' },
      { title: 'Haryana-Specific Current Affairs 2025', type: 'PDF', size: '2.7 MB' },
    ],
  },
];

export default function ResourcesPage() {
  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title"><Archive size={22} /> Resources</h1>
          <p className="page-description">Model answers, notes, syllabus, and study material</p>
        </div>
      </div>

      <div className="flex-col gap-6 flex">
        {RESOURCES.map(cat => (
          <div key={cat.category}>
            <h4 className="mb-3">{cat.category}</h4>
            <div className="grid-3 gap-3">
              {cat.items.map(item => (
                <div key={item.title} className="card" style={{ padding: '16px 18px' }}>
                  <div className="flex items-start gap-3">
                    <div style={{
                      width: 36, height: 36, borderRadius: 'var(--radius-md)',
                      background: 'var(--primary-subtle)', display: 'flex',
                      alignItems: 'center', justifyContent: 'center', flexShrink: 0
                    }}>
                      <FileText size={16} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="text-sm font-medium mb-1" style={{ lineHeight: 1.4 }}>{item.title}</div>
                      <div className="flex items-center gap-2">
                        <span className="badge badge-neutral">{item.type}</span>
                        <span className="text-xs text-muted">{item.size}</span>
                      </div>
                    </div>
                  </div>
                  <button className="btn btn-secondary btn-sm w-full mt-3">
                    <Download size={13} /> Download
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="card mt-6" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', textAlign: 'center', padding: 36 }}>
        <BookOpen size={32} style={{ color: 'var(--text-muted)', margin: '0 auto 12px', opacity: 0.4 }} />
        <h3 className="mb-2">More Resources Coming Soon</h3>
        <p className="text-sm text-muted" style={{ maxWidth: 380, margin: '0 auto 16px' }}>
          Video lectures, mind maps, and previous year topper answer booklets will be added here.
        </p>
        <button className="btn btn-ghost btn-sm">
          <ExternalLink size={13} /> Request a Resource
        </button>
      </div>
    </div>
  );
}
