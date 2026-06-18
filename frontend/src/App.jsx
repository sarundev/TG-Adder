import React, { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      const duration = params.get('duration') || '1_month';
      issueLicenseAfterPayment(duration);
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

  return (
    <div className="app-container">
      {/* Navigation */}
      <nav className="navbar">
        <div className="logo">
          <svg className="logo-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2L2 12L9 15L21 2Z"/>
            <path d="M21 2L13 22L9 15L21 2Z"/>
          </svg>
          TelegramSuite
        </div>
        <div>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
            Documentation
          </a>
        </div>
      </nav>

      {/* Hero */}
      <main className="hero">
        <span className="badge">v2.0 Professional Edition</span>
        <h1 className="title">Advanced Telegram Automation</h1>
        <p className="subtitle">
          The ultimate desktop client built for professionals. Automate, scrape, and manage your Telegram groups and channels securely with zero configuration.
        </p>
        
        <div className="btn-group">
          <a href="/downloads/TELE168_Windows.zip" className="btn btn-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            Download for Windows
          </a>
        </div>
      </main>

      {/* Features */}
      <section className="features-container">
        <div className="features">
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
            </div>
            <h3>Mass Account Management</h3>
            <p>Seamlessly add, monitor, and manage unlimited Telegram sessions from a centralized dashboard. Real-time status indicators ensure all accounts are active.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            <h3>Advanced Data Scraper</h3>
            <p>Extract active members from any target group or channel. Export high-quality target lists for your marketing campaigns with a single click.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <line x1="20" y1="8" x2="20" y2="14"></line>
                <line x1="23" y1="11" x2="17" y2="11"></line>
              </svg>
            </div>
            <h3>Mass Inviter & G2G</h3>
            <p>Bulk invite scraped users into your own groups, or automatically clone members from competitor groups directly to yours (Group-to-Group transferring).</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
              </svg>
            </div>
            <h3>Joiner & Bot Clicker</h3>
            <p>Force all connected accounts to instantly join any public or private group link, or mass-start specific Telegram bots simultaneously.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
            </div>
            <h3>Account Warmup & Security</h3>
            <p>Avoid bans with our intelligent anti-detection warmup protocol. Simulate natural human activity to artificially mature new accounts before mass inviting.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="4 17 10 11 4 5"></polyline>
                <line x1="12" y1="19" x2="20" y2="19"></line>
              </svg>
            </div>
            <h3>Live Terminal Logs</h3>
            <p>Monitor exactly what every account is doing in real-time. Built-in log viewer allows you to track errors, successes, and API limits seamlessly.</p>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="pricing-section">
        <h2 className="section-title" style={{ textAlign: 'center', marginBottom: '3rem', fontSize: '2.5rem' }}>Choose Your License</h2>
        <div className="pricing-cards">
          <div className="price-card">
            <h3>1 Week</h3>
            <div className="price">$5</div>
            <p>Full access for 7 days</p>
            <button className="btn btn-secondary" onClick={() => handleBuy('1_week')} disabled={buying}>
              {buying ? 'Processing...' : 'Buy Now'}
            </button>
          </div>
          <div className="price-card">
            <h3>1 Month</h3>
            <div className="price">$15</div>
            <p>Full access for 30 days</p>
            <button className="btn btn-secondary" onClick={() => handleBuy('1_month')} disabled={buying}>
              {buying ? 'Processing...' : 'Buy Now'}
            </button>
          </div>
          <div className="price-card">
            <h3>3 Months</h3>
            <div className="price">$40</div>
            <p>Full access for 90 days</p>
            <button className="btn btn-secondary" onClick={() => handleBuy('3_months')} disabled={buying}>
              {buying ? 'Processing...' : 'Buy Now'}
            </button>
          </div>
          <div className="price-card popular">
            <div className="popular-badge">Most Popular</div>
            <h3>1 Year</h3>
            <div className="price">$100</div>
            <p>Save money and commit longer</p>
            <button className="btn btn-primary" onClick={() => handleBuy('1_year')} disabled={buying}>
              {buying ? 'Processing...' : 'Buy Now'}
            </button>
          </div>
          <div className="price-card">
            <h3>Lifetime</h3>
            <div className="price">$199</div>
            <p>One-time payment, forever</p>
            <button className="btn btn-secondary" onClick={() => handleBuy('lifetime')} disabled={buying}>
              {buying ? 'Processing...' : 'Buy Now'}
            </button>
          </div>
        </div>
      </section>

      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} TelegramSuite. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
