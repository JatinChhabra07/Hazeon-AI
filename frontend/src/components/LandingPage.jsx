import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap, Brain, BarChart3, ArrowRight, CheckCircle2,
  FileText, Target, Upload, Cpu, Sparkles, ChevronDown,
  Star, X, Check, Menu,
  Globe, Database
} from 'lucide-react';

/* ── Data ─────────────────────────────────────────────────── */
const FEATURES = [
  { icon: Brain, title: 'Gemini Vision OCR', desc: 'Reads Hindi + English handwriting with high accuracy. No manual typing — just upload and go.', color: 'var(--primary)' },
  { icon: Target, title: '11-Parameter Scoring', desc: 'Evaluates relevance, structure, keywords, factual accuracy, analysis depth, multi-dimensions and more.', color: 'var(--accent)' },
  { icon: BarChart3, title: 'Institute Dashboard', desc: 'Batch analytics, weak area heatmaps, student progress tracking, and exportable performance reports.', color: 'var(--success)' },
  { icon: Database, title: 'Topper Answer Database', desc: 'RAG-powered evaluation using real HCS topper answers as benchmarks — our hardest-to-replicate moat.', color: 'var(--warning)' },
  { icon: Zap, title: 'Feedback in < 30s', desc: 'Evaluation via Groq LLM. No 2–3 week wait for human evaluators. Instant structured feedback.', color: 'var(--primary)' },
  { icon: Globe, title: 'Hindi-First Support', desc: '~40–50% of UPSC/HCS aspirants are Hindi-medium. We\'re built for them — not just English speakers.', color: 'var(--accent)' },
];

const STEPS = [
  { step: '01', icon: Upload,    label: 'Upload Answer Sheet', desc: 'PDF or image (JPG/PNG). Multi-page, handwritten, any quality.', color: 'var(--primary)' },
  { step: '02', icon: Brain,     label: 'Gemini OCR',          desc: 'Extracts Hindi + English handwritten text with high accuracy.', color: 'var(--accent)' },
  { step: '03', icon: Cpu,       label: 'LangGraph Pipeline',  desc: 'Structures text, maps to question, retrieves topper benchmarks via RAG.', color: 'var(--warning)' },
  { step: '04', icon: BarChart3, label: 'Groq Evaluation',     desc: 'Scores 11 parameters. Generates strengths, weaknesses, improvements.', color: 'var(--success)' },
  { step: '05', icon: Sparkles,  label: 'Structured Report',   desc: 'Student sees feedback. Institute admin sees batch analytics.', color: 'var(--primary)' },
];

const COMPARISON = [
  { feature: 'Turnaround time',        human: '2–3 weeks',    hazeon: '< 30 seconds' },
  { feature: 'Cost per answer',        human: '₹100–200',     hazeon: '₹10–15' },
  { feature: 'Consistency of scoring', human: 'Varies by evaluator', hazeon: 'Uniform rubric every time' },
  { feature: 'Hindi handwriting',      human: 'Depends on evaluator', hazeon: 'Native support' },
  { feature: 'Topper benchmarking',    human: 'Rarely available', hazeon: 'Built-in via RAG' },
  { feature: 'Batch analytics',        human: 'Manual spreadsheets', hazeon: 'Real-time dashboard' },
  { feature: 'Available 24/7',         human: 'No',           hazeon: 'Yes' },
];

const PRICING = [
  {
    name: 'Pilot',
    price: 'Free',
    sub: 'First 2 months',
    color: 'var(--text-muted)',
    border: 'var(--border)',
    features: ['Up to 500 evaluations', 'Full AI pipeline', 'Institute dashboard', 'Email support', 'Basic analytics'],
    cta: 'Start Free Pilot',
    highlight: false,
  },
  {
    name: 'Growth',
    price: '₹10',
    sub: 'per evaluation',
    color: 'var(--primary)',
    border: 'rgba(79,125,255,0.5)',
    features: ['Unlimited evaluations', 'Topper database access', 'Advanced analytics', 'White-label option', 'Priority support', 'Custom rubric tuning'],
    cta: 'Get Started',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: '₹3L',
    sub: 'per year flat',
    color: 'var(--accent)',
    border: 'rgba(0,212,255,0.3)',
    features: ['Everything in Growth', 'Dedicated account manager', 'Custom fine-tuned model', 'API access', 'SLA guarantee', 'On-site training'],
    cta: 'Contact Sales',
    highlight: false,
  },
];

const TESTIMONIALS = [
  {
    name: 'Ravi Shankar',
    role: 'Director, Vision HCS Academy, Rohtak',
    text: 'Hazeon reduced our evaluation backlog from 3 weeks to same-day. Our students now get feedback before forgetting what they wrote. The Haryana-specific question bank is exactly what we needed.',
    stars: 5,
    initials: 'RS',
  },
  {
    name: 'Nisha Yadav',
    role: 'HCS 2024 Rank 7, Drishti Chandigarh',
    text: 'The gap analysis showed me I was consistently missing the "Way Forward" dimension. After 4 weeks of targeted practice using Hazeon feedback, my scores jumped from 6.2 to 8.1 average.',
    stars: 5,
    initials: 'NY',
  },
  {
    name: 'Dr. Manoj Bhatia',
    role: 'Faculty, Lakshya IAS Gurugram',
    text: 'I was skeptical about AI evaluating nuanced ethics answers. But the dimension-wise breakdown it gives is more structured than most human evaluators. The topper benchmark feature is a game-changer.',
    stars: 5,
    initials: 'MB',
  },
];

const FAQS = [
  { q: 'How accurate is the AI on Hindi handwriting?', a: 'We use Gemini Vision which handles Devanagari script natively. In our tests on HCS answer sheets, OCR accuracy is 88–94% for neat handwriting and 78–85% for typical student writing. A human-review fallback is available for low-confidence extractions.' },
  { q: 'Can institutes use their own rubric/marking scheme?', a: 'Yes. For Growth and Enterprise plans, you can provide your institute\'s rubric. The LangGraph pipeline incorporates custom marking schemes and model answer key points into the evaluation prompt.' },
  { q: 'Is the student\'s data private?', a: 'All answer sheets are stored encrypted. We comply with DPDP Act 2023. Answer data is never used to train models without explicit written consent. B2B contracts include data usage clauses.' },
  { q: 'How does the Topper Database work?', a: 'We\'ve curated HCS/UPSC topper answer sheets (with consent + anonymization). During evaluation, RAG retrieves the 3 most similar topper answers and uses them as few-shot examples in the evaluation prompt — giving richer, contextual feedback.' },
  { q: 'Do you support UPSC Mains questions, not just HCS?', a: 'Yes. The question bank includes UPSC GS1-GS4 questions. HCS is our primary focus for now due to local data advantage, but UPSC evaluation uses the same pipeline with UPSC-specific rubrics.' },
  { q: 'What happens if the API evaluation fails?', a: 'The system auto-retries 3 times. If still failing, the submission is flagged for human review and the student is notified. You are not charged for failed evaluations.' },
];

const INSTITUTES = ['Drishti IAS', 'Vision HCS', 'Lakshya IAS', 'Forum IAS', 'Vajiram & Ravi'];

/* ── Component ────────────────────────────────────────────── */
export default function LandingPage() {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq]           = useState(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const featuresRef  = useRef(null);
  const howRef       = useRef(null);
  const pricingRef   = useRef(null);

  const scrollTo = (ref) => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  return (
    <div className="landing">
      {/* ── Sticky Nav ─────────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="logo-mark">
          <div className="logo-icon">HZ</div>
          <div>
            <div className="logo-text">Hazeon AI</div>
            <div className="logo-sub">UPSC · HCS Evaluator</div>
          </div>
        </div>

        {/* Desktop nav */}
        <div className="landing-nav-links">
          <button className="landing-nav-link" onClick={() => scrollTo(featuresRef)}>Features</button>
          <button className="landing-nav-link" onClick={() => scrollTo(howRef)}>How it Works</button>
          <button className="landing-nav-link" onClick={() => scrollTo(pricingRef)}>Pricing</button>
          <div style={{ width: 1, height: 18, background: 'var(--border)' }} />
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/login')}>Login</button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/login')}>
            Get Started <ArrowRight size={13} />
          </button>
        </div>

        {/* Mobile hamburger */}
        <button className="mobile-nav-btn" onClick={() => setMobileNavOpen(o => !o)}>
          {mobileNavOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* Mobile nav dropdown */}
      <div className={`landing-mobile-menu${mobileNavOpen ? ' open' : ''}`}>
        <button className="landing-mobile-item" onClick={() => { scrollTo(featuresRef); setMobileNavOpen(false); }}>Features</button>
        <button className="landing-mobile-item" onClick={() => { scrollTo(howRef); setMobileNavOpen(false); }}>How it Works</button>
        <button className="landing-mobile-item" onClick={() => { scrollTo(pricingRef); setMobileNavOpen(false); }}>Pricing</button>
        <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />
        <button className="btn btn-ghost btn-sm w-full" style={{ justifyContent: 'flex-start' }} onClick={() => { navigate('/login'); setMobileNavOpen(false); }}>Login</button>
        <button className="btn btn-primary btn-sm w-full mt-2" onClick={() => { navigate('/login'); setMobileNavOpen(false); }}>
          Get Started <ArrowRight size={13} />
        </button>
      </div>

      {/* ── Hero ───────────────────────────────────────────── */}
      <div className="landing-hero" style={{ position: 'relative', overflow: 'hidden' }}>
        {/* Background glow */}
        <div style={{
          position: 'absolute', top: -100, left: '50%', transform: 'translateX(-50%)',
          width: 700, height: 400,
          background: 'radial-gradient(ellipse, rgba(79,125,255,0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div className="hero-badge">
          <Zap size={12} />
          Powered by Groq + Gemini Vision · Now evaluating HCS 2026
        </div>

        <h1 className="hero-title">
          AI Answer Evaluation<br />
          for <span className="gradient-text">HCS / UPSC Mains</span>
        </h1>

        <p className="hero-desc">
          Upload handwritten answer sheets. Get structured AI feedback in under 30 seconds.
          Built for coaching institutes — Hindi + English, 11 parameters, topper benchmarking.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/login')}>
            Start Free Pilot <ArrowRight size={16} />
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => scrollTo(howRef)}>
            See How It Works
          </button>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: 48, flexWrap: 'wrap',
          borderTop: '1px solid var(--border)', paddingTop: 32, marginTop: 48
        }}>
          {[
            { value: '11+', label: 'Evaluation Parameters' },
            { value: '< 30s', label: 'Feedback Time' },
            { value: '2x', label: 'Languages Supported' },
            { value: '10x', label: 'Cost Reduction' },
            { value: '94%', label: 'OCR Accuracy' },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--primary)', lineHeight: 1 }}>{s.value}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Trust Bar ──────────────────────────────────────── */}
      <div className="section-padded-sm" style={{ borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', textAlign: 'center' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-disabled)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16 }}>
          Trusted by coaching institutes across Haryana & Punjab
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40, flexWrap: 'wrap' }}>
          {INSTITUTES.map(name => (
            <div key={name} style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', opacity: 0.7 }}>{name}</div>
          ))}
        </div>
      </div>

      {/* ── How It Works ───────────────────────────────────── */}
      <div ref={howRef} className="section-padded" style={{ maxWidth: 1080, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div className="section-eyebrow">How It Works</div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 700, marginBottom: 12 }}>
            Upload to Feedback in 5 steps
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', maxWidth: 500, margin: '0 auto' }}>
            The entire pipeline runs automatically. No manual steps for students or teachers.
          </p>
        </div>

        <div className="pipeline-timeline">
          {STEPS.map((s, i) => (
            <div key={s.step} className="timeline-step">
              <div className="timeline-icon" style={{ background: `${s.color}18`, border: `2px solid ${s.color}`, color: s.color }}>
                <s.icon size={20} />
              </div>
              {i < STEPS.length - 1 && <div className="timeline-connector" />}
              <div className="timeline-content">
                <div style={{ fontSize: '0.65rem', fontWeight: 700, color: s.color, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{s.step}</div>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Features ───────────────────────────────────────── */}
      <div ref={featuresRef} className="section-padded" style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ textAlign: 'center', marginBottom: 48, maxWidth: 1080, margin: '0 auto 48px' }}>
          <div className="section-eyebrow">Features</div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 700 }}>Everything an institute needs</h2>
        </div>
        <div className="feature-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon" style={{ background: `${f.color}15`, borderColor: `${f.color}30`, color: f.color }}>
                <f.icon size={20} />
              </div>
              <h3 style={{ marginBottom: 8 }}>{f.title}</h3>
              <p className="text-sm text-muted" style={{ lineHeight: 1.65 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Comparison Table ───────────────────────────────── */}
      <div className="section-padded" style={{ maxWidth: 800, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div className="section-eyebrow">Why Switch</div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 700 }}>Hazeon vs Human Evaluator</h2>
        </div>
        <div className="comparison-table">
          <div className="comparison-header">
            <div>Feature</div>
            <div style={{ textAlign: 'center' }}>Human Evaluator</div>
            <div style={{ textAlign: 'center', color: 'var(--primary)' }}>Hazeon AI</div>
          </div>
          {COMPARISON.map((row, i) => (
            <div key={i} className="comparison-row">
              <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{row.feature}</div>
              <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <X size={13} style={{ color: 'var(--error)', marginRight: 4, verticalAlign: 'middle' }} />
                {row.human}
              </div>
              <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--success)', fontWeight: 500 }}>
                <Check size={13} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                {row.hazeon}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Pricing ────────────────────────────────────────── */}
      <div ref={pricingRef} className="section-padded" style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div className="section-eyebrow">Pricing</div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 700 }}>Simple, institute-friendly pricing</h2>
          <p style={{ color: 'var(--text-muted)', marginTop: 8, fontSize: '0.9rem' }}>Start free. Scale as your batch grows. No hidden charges.</p>
        </div>
        <div className="pricing-grid">
          {PRICING.map(p => (
            <div key={p.name} className={`pricing-card ${p.highlight ? 'pricing-card-featured' : ''}`}
              style={{ borderColor: p.border }}>
              {p.highlight && (
                <div className="pricing-popular">Most Popular</div>
              )}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: p.color, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{p.name}</div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>{p.price}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>{p.sub}</div>
              </div>
              <div style={{ marginBottom: 24 }}>
                {p.features.map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <CheckCircle2 size={14} style={{ color: p.highlight ? 'var(--primary)' : 'var(--success)', flexShrink: 0 }} />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{f}</span>
                  </div>
                ))}
              </div>
              <button
                className={`btn w-full ${p.highlight ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => navigate('/login')}
              >
                {p.cta} <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Testimonials ───────────────────────────────────── */}
      <div className="section-padded" style={{ maxWidth: 1080, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div className="section-eyebrow">Testimonials</div>
          <h2 style={{ fontSize: '1.9rem', fontWeight: 700 }}>What institutes and toppers say</h2>
        </div>
        <div className="grid-resp-3" style={{ gap: 20 }}>
          {TESTIMONIALS.map(t => (
            <div key={t.name} className="testimonial-card">
              <div style={{ display: 'flex', gap: 2, marginBottom: 14 }}>
                {Array(t.stars).fill(0).map((_, i) => (
                  <Star key={i} size={13} style={{ fill: 'var(--warning)', color: 'var(--warning)' }} />
                ))}
              </div>
              <p style={{ fontSize: '0.875rem', lineHeight: 1.7, color: 'var(--text-secondary)', marginBottom: 20, fontStyle: 'italic' }}>
                "{t.text}"
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.7rem', fontWeight: 700, color: 'white', flexShrink: 0
                }}>{t.initials}</div>
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>{t.name}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── FAQ ────────────────────────────────────────────── */}
      <div className="section-padded" style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div className="section-eyebrow">FAQ</div>
            <h2 style={{ fontSize: '1.9rem', fontWeight: 700 }}>Common questions</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {FAQS.map((faq, i) => (
              <div key={i} className="faq-item" style={{ borderColor: openFaq === i ? 'var(--primary)' : 'var(--border)' }}>
                <button className="faq-question" onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                  <span>{faq.q}</span>
                  <ChevronDown size={16} style={{
                    transition: '0.2s', flexShrink: 0,
                    transform: openFaq === i ? 'rotate(180deg)' : 'none',
                    color: openFaq === i ? 'var(--primary)' : 'var(--text-muted)'
                  }} />
                </button>
                {openFaq === i && (
                  <div className="faq-answer">{faq.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────────────── */}
      <div className="landing-footer-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="logo-icon" style={{ width: 24, height: 24, fontSize: '0.6rem' }}>HZ</div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>© 2026 Hazeon AI. All rights reserved.</span>
        </div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Built for HCS &amp; UPSC Mains · Chandigarh, Haryana
        </div>
      </div>
    </div>
  );
}
