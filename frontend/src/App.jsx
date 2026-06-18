import React from 'react';
import './index.css';

function App() {
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
          <a href="/downloads/TelegramSuite.zip" className="btn btn-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Download for macOS
          </a>
          <a href="/downloads/TelegramSuite_Windows.zip" className="btn btn-secondary">
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
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
            </div>
            <h3>High Performance</h3>
            <p>Engineered with optimized asynchronous routines, allowing you to execute mass operations instantly without hitting rate limits.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
            </div>
            <h3>Enterprise Security</h3>
            <p>Built-in intelligent delay systems and strict session management policies ensure your accounts remain perfectly secure and active.</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
            </div>
            <h3>Intuitive Interface</h3>
            <p>Leave the command line behind. Manage all your configurations and tasks from a clean, beautifully crafted graphical user interface.</p>
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
