import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const navStyles = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    height: '72px',
    display: 'flex',
    alignItems: 'center',
    padding: '0 5%',
    backgroundColor: scrolled ? 'rgba(255, 255, 255, 0.9)' : 'transparent',
    backdropFilter: scrolled ? 'blur(12px)' : 'none',
    borderBottom: scrolled ? '1px solid var(--border)' : '1px solid transparent',
    transition: 'all 0.2s ease',
    zIndex: 100
  };

  return (
    <nav style={navStyles}>
      <Link to="/" className="brand" onClick={() => setMobileOpen(false)}>
        <div className="brand-icon">H</div>
        <span>Hazeon</span>
      </Link>

      <div className="pub-nav-links" style={{ display: 'flex' }}>
        <a href="#product" className="pub-link text-sm font-medium pr-4">Product</a>
        <a href="#infrastructure" className="pub-link text-sm font-medium pr-4">Infrastructure</a>
        <a href="#customers" className="pub-link text-sm font-medium pr-8">Customers</a>
        
        <div style={{ width: '1px', height: '20px', background: 'var(--border)', margin: '0 16px' }}></div>
        
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/login')}>
          Sign In
        </button>
        <button className="btn btn-primary btn-sm ml-2" onClick={() => navigate('/login')}>
          Start Free Trial
        </button>
      </div>
    </nav>
  );
}
