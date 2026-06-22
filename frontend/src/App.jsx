import React, { useState, useEffect } from 'react';
import './index.css';
import AdminDashboard from './AdminDashboard';
import ChatWidget from './ChatWidget';

function App() {
  const [page, setPage] = useState(window.location.hash === '#admin' ? 'admin' : 'home');
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    const onHashChange = () => {
      setPage(window.location.hash === '#admin' ? 'admin' : 'home');
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  if (page === 'admin') {
    return <AdminDashboard onBack={() => { window.location.hash = ''; setPage('home'); }} />;
  }

  const handleBuyAccount = async (accountType) => {
    if (buying) return;
    setBuying(true);
    try {
      const success_url = window.location.origin + window.location.pathname + "?account_success=true&type=" + accountType;
      const res = await fetch('/api/account/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_type: accountType, success_url })
      });
      const data = await res.json();
      if (data.status === 'redirect') {
        window.location.href = data.checkout_url;
      } else {
        alert('Purchase failed: ' + (data.detail || data.message));
      }
    } catch (e) {
      alert('Error connecting to payment server.');
    }
    setBuying(false);
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      const duration = params.get('duration') || '1_month';
      issueLicenseAfterPayment(duration);
    } else if (params.get('account_success') === 'true') {
      const accountType = params.get('type') || 'fresh';
      issueAccountAfterPayment(accountType);
    }
  }, []);

  const issueLicenseAfterPayment = async (duration) => {
    try {
      const res = await fetch('/api/license/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration })
      });
      const data = await res.json();
      if (data.status === 'success') {
        const blob = new Blob([`Your TG TELE168 License Key:\n\n${data.token}\n\nKeep this safe. Enter it in the Desktop app to unlock it.`], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'TG_TELE168_License.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        window.history.replaceState({}, document.title, window.location.pathname);
        alert('Payment Complete! License key downloaded.');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to issue license after payment.');
    }
  };

  const handleBuy = async (duration) => {
    if (buying) return;
    setBuying(true);
    try {
      const success_url = window.location.origin + window.location.pathname + "?success=true&duration=" + duration;
      const res = await fetch('/api/license/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration, success_url })
      });
      const data = await res.json();
      if (data.status === 'redirect') {
        window.location.href = data.checkout_url;
      } else {
        alert('Purchase failed: ' + (data.detail || data.message));
      }
    } catch (e) {
      alert('Error connecting to payment server.');
    }
    setBuying(false);
  };

  const issueAccountAfterPayment = async (accountType) => {
    const typeNames = { 'fresh': 'Fresh Account', 'aged': 'Aged Account', 'admin': 'Admin Account' };
    const name = typeNames[accountType] || 'Telegram Account';
    const orderId = 'ORD_' + Math.floor(Date.now() / 1000);
    const receiptText = `Thank you for your purchase!\n\nOrder ID: ${orderId}\nItem: 1x ${name}\n\nSince TData ZIP files are large, please send this receipt to our Telegram Support (@YourTelegramUsername) to instantly receive your Account ZIP file.`;
    const blob = new Blob([receiptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Receipt_${orderId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    window.history.replaceState({}, document.title, window.location.pathname);
    alert('Payment Complete! Your receipt has been downloaded. Send it to support to get your account.');
  };

  const features = [
    {
      title: 'Mass Account Management',
      desc: 'Seamlessly add, monitor, and manage unlimited Telegram sessions from a centralised dashboard. Real-time status indicators keep every account in check.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      ),
    },
    {
      title: 'Advanced Data Scraper',
      desc: 'Extract active members from any target group or channel. Export high-quality lists for marketing campaigns with a single click.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      ),
    },
    {
      title: 'Mass Inviter & G2G',
      desc: 'Bulk invite scraped users into your own groups, or clone members directly from competitor groups via Group-to-Group transferring.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>
        </svg>
      ),
    },
    {
      title: 'Joiner & Bot Clicker',
      desc: 'Force all connected accounts to instantly join any public or private group link, or mass-start specific Telegram bots simultaneously.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
      ),
    },
    {
      title: 'Account Warmup & Security',
      desc: 'Avoid bans with our intelligent anti-detection protocol. Simulate natural human activity to mature new accounts before mass inviting.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
      ),
    },
    {
      title: 'Live Terminal Logs',
      desc: 'Monitor exactly what every account is doing in real-time. The built-in log viewer tracks errors, successes, and API limits seamlessly.',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
        </svg>
      ),
    },
  ];

  const pricingPlans = [
    { key: '1_week',   label: '1 Week',   price: '$5',   desc: 'Full access · 7 days' },
    { key: '1_month',  label: '1 Month',  price: '$15',  desc: 'Full access · 30 days' },
    { key: '3_months', label: '3 Months', price: '$40',  desc: 'Full access · 90 days' },
    { key: '1_year',   label: '1 Year',   price: '$100', desc: 'Best value for teams', popular: true },
    { key: 'lifetime', label: 'Lifetime', price: '$199', desc: 'One-time · forever' },
  ];

  return (
    <div className="app-container">

      {/* ── Navbar ── */}
      <nav className="navbar" id="navbar">
        <div className="logo">
          <svg className="logo-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2L2 12L9 15L21 2Z"/>
            <path d="M21 2L13 22L9 15L21 2Z"/>
          </svg>
          TelegramSuite
        </div>
        <div className="navbar-right" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <a href="https://t.me/sarun_chann" target="_blank" rel="noreferrer" className="btn" style={{ color: '#0088cc', fontSize: '0.875rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.08-.19-.09-.05-.21-.02-.3.01-.13.04-2.2 1.41-6.22 4.12-.59.4-1.12.6-1.59.59-.51-.01-1.49-.29-2.22-.53-.89-.29-1.6-.44-1.54-.93.03-.25.39-.5.1 1.07.75 1.63 1.25 3.32 1.76.62 1.35 1.27 2.19 2.05 2.45.69.23.95.83.82 1.5-.04.24-.04.53-.1.74-.23.51-.77 2.02-1.52.28 1.49.33 1.61 1.95 2.53 1.13.65 2.16 2.03 2.74 2.37.16.09.34.14.54.14.49 0 .9-.36 1.05-.88z"/>
            </svg>
            Live Support
          </a>
          <a href="#features" className="btn btn-secondary" style={{ padding: '0.5rem 1.125rem', fontSize: '0.875rem' }}>
            Documentation
          </a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <main className="hero" id="hero">
        <span className="badge">Version 1.0.1 · Professional Edition</span>
        <h1 className="title">Advanced Telegram<br/>Automation Suite</h1>
        <p className="subtitle">
          The ultimate desktop client built for professionals. Automate, scrape, and manage your Telegram groups and channels — securely, at scale.
        </p>
        <div className="btn-group">
          <a href="/downloads/TELE168_Windows.zip" className="btn btn-primary" id="download-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            Download for Windows
          </a>
          <a href="#features" className="btn btn-secondary">
            View Features
          </a>
        </div>
      </main>

      {/* ── Features ── */}
      <section className="features-container" id="features">
        <p className="section-label">Capabilities</p>
        <h2 className="section-title">Everything you need, built in</h2>
        <p className="section-subtitle">Six powerful automation modules, designed to work together in one cohesive desktop app.</p>
        <div className="features">
          {features.map((f, i) => (
            <div className="feature-card" key={i}>
              <div className="feature-icon-wrapper">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Pricing ── */}
      <section className="pricing-section" id="pricing">
        <p className="section-label">Pricing</p>
        <h2 className="section-title" style={{ marginBottom: '0.875rem' }}>Choose Your License</h2>
        <p className="section-subtitle">All plans include full feature access. Pay once, use without limits.</p>
        <div className="pricing-cards">
          {pricingPlans.map((plan) => (
            <div key={plan.key} className={`price-card${plan.popular ? ' popular' : ''}`}>
              {plan.popular && <div className="popular-badge">Most Popular</div>}
              <h3>{plan.label}</h3>
              <div className="price">{plan.price}</div>
              <p>{plan.desc}</p>
              <button
                className={`btn ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleBuy(plan.key)}
                disabled={buying}
                id={`buy-${plan.key}`}
              >
                {buying ? 'Processing…' : 'Buy Now'}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer" id="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--gold-400)' }}>
              <path d="M21 2L2 12L9 15L21 2Z"/>
              <path d="M21 2L13 22L9 15L21 2Z"/>
            </svg>
            TelegramSuite
          </div>
          <span className="footer-version">v1.0.1</span>
          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--gray-400)' }}>
            <a href="https://t.me/sarun_chann" target="_blank" rel="noreferrer" style={{ color: 'var(--gold-400)', textDecoration: 'none', fontWeight: 600 }}>Contact 24/7 Telegram Support</a>
          </div>
          <p style={{ marginTop: '1rem' }}>© {new Date().getFullYear()} TelegramSuite. All rights reserved.</p>
        </div>
      </footer>

      <ChatWidget />
    </div>
  );
}

export default App;
