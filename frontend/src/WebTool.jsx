import React, { useState, useEffect } from 'react';
import './WebTool.css';

export default function WebTool({ onBack }) {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('isLoggedIn') === 'true';
  });
  const [isRegistering, setIsRegistering] = useState(false);
  const [formData, setFormData] = useState(() => {
    const saved = localStorage.getItem('formData');
    return saved ? JSON.parse(saved) : {
      username: '',
      password: '',
      license_key: ''
    };
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [activeTab, setActiveTab] = useState('dashboard');
  const [actionMessage, setActionMessage] = useState('');

  // Module States
  const [botUsername, setBotUsername] = useState('');
  const [botAccount, setBotAccount] = useState('');
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeAccount, setScrapeAccount] = useState('');
  const [scrapeFilters, setScrapeFilters] = useState({
    filter_has_username: false,
    filter_no_bots: true,
    filter_active_recently: false
  });
  const [scrapeCacheId, setScrapeCacheId] = useState(null);

  const [inviteMode, setInviteMode] = useState('group'); // 'group' or 'username'
  const [inviteSource, setInviteSource] = useState('');
  const [inviteTarget, setInviteTarget] = useState('');
  const [invitePrimaryAccount, setInvitePrimaryAccount] = useState('');
  const [inviteSelectedAccounts, setInviteSelectedAccounts] = useState([]);
  const [inviteUsernames, setInviteUsernames] = useState('');
  const [inviteDelay, setInviteDelay] = useState(30);
  const [joinUrl, setJoinUrl] = useState('');
  const [joinAccount, setJoinAccount] = useState('');

  // Poster State
  const [posterMode, setPosterMode] = useState('text'); // 'text' or 'video'
  const [posterSelectedAccounts, setPosterSelectedAccounts] = useState([]);
  const [posterTargets, setPosterTargets] = useState('');
  const [posterMessage, setPosterMessage] = useState('');
  const [posterVideoFolder, setPosterVideoFolder] = useState('');
  const [posterDelay, setPosterDelay] = useState(15);

  // Logs state
  const [logs, setLogs] = useState([]);

  // Telegram Accounts State
  const [accounts, setAccounts] = useState([]);
  const [authPhone, setAuthPhone] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [isCodeRequested, setIsCodeRequested] = useState(false);
  const [isPasswordRequired, setIsPasswordRequired] = useState(false);
  const [loginMode, setLoginMode] = useState('phone'); // 'phone' or 'qr'
  const [qrUrl, setQrUrl] = useState('');
  const [qrUuid, setQrUuid] = useState('');
  const [qrPolling, setQrPolling] = useState(false);

  const fetchAccounts = async () => {
    try {
      const res = await fetch(`/api/web/user/accounts?username=${formData.username}`);
      const data = await res.json();
      if (data.status === 'success') {
        setAccounts(data.accounts || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let logInterval;
    if (isLoggedIn && activeTab === 'logs') {
      const fetchLogs = async () => {
        try {
          const res = await fetch('/api/logs');
          if (res.ok) {
            const data = await res.json();
            const logObj = data.logs || {};
            const unifiedLogs = [];
            for (const [task, lines] of Object.entries(logObj)) {
              if (Array.isArray(lines)) {
                for (const line of lines) {
                  unifiedLogs.push(`[${task}] ${line}`);
                }
              }
            }
            setLogs(unifiedLogs);
          }
        } catch(e) {}
      };
      fetchLogs();
      logInterval = setInterval(fetchLogs, 1000);
    }
    return () => clearInterval(logInterval);
  }, [isLoggedIn, activeTab]);

  useEffect(() => {
    if (isLoggedIn) {
      fetchAccounts();
    }
  }, [isLoggedIn, activeTab]);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    if (!formData.username || !formData.password || !formData.license_key) {
      setError('Please fill in all fields.');
      return;
    }
    setLoading(true);
    setError('');

    const endpoint = isRegistering ? '/api/web/register' : '/api/web/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
          license_key: formData.license_key
        })
      });
      const data = await res.json();
      if (res.ok) {
        setIsLoggedIn(true);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('formData', JSON.stringify(formData));
        fetchAccounts();
      } else {
        setError(data.detail || 'Authentication failed.');
      }
    } catch (err) {
      setError('Could not connect to server.');
    }
    setLoading(false);
  };

  const handleRequestCode = async () => {
    if (!authPhone) return;
    setActionMessage('Requesting code...');
    try {
      const res = await fetch('/api/accounts/login/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: authPhone, web_username: formData.username })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.status === 'authorized') {
          setActionMessage('✅ This account is already connected!');
          fetchAccounts();
        } else {
          setIsCodeRequested(true);
          setActionMessage('Code sent to your Telegram app!');
        }
      } else {
        setActionMessage(data.detail || 'Failed to request code.');
      }
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handleConfirmCode = async () => {
    if (!authCode) return;
    setActionMessage('Verifying code...');
    try {
      const res = await fetch('/api/accounts/login/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: authPhone, code: authCode, password: authPassword, web_username: formData.username })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.status === 'password_required') {
          setIsPasswordRequired(true);
          setActionMessage('2FA Password required.');
        } else {
          setActionMessage('✅ Account successfully added!');
          setAuthPhone('');
          setAuthCode('');
          setAuthPassword('');
          setIsCodeRequested(false);
          setIsPasswordRequired(false);
          fetchAccounts();
        }
      } else {
        setActionMessage(data.detail || 'Failed to verify code.');
      }
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const requestQRLogin = async () => {
    setActionMessage('Generating secure QR Code...');
    try {
      const res = await fetch('/api/accounts/login/qr/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ web_username: formData.username })
      });
      const data = await res.json();
      if (res.ok) {
        setQrUrl(data.url);
        setQrUuid(data.uuid);
        setQrPolling(true);
        setActionMessage('Scan the QR code with your Telegram app.');
      } else {
        setActionMessage(data.detail || 'Failed to generate QR.');
      }
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  useEffect(() => {
    let interval;
    if (qrPolling && qrUuid) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('/api/accounts/login/qr/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uuid: qrUuid, password: authPassword })
          });
          const data = await res.json();
          if (res.ok) {
            if (data.status === 'success') {
              setQrPolling(false);
              setActionMessage('✅ Account successfully added via QR!');
              setQrUrl('');
              setQrUuid('');
              setAuthPassword('');
              setIsPasswordRequired(false);
              fetchAccounts();
            } else if (data.status === 'password_required') {
              setIsPasswordRequired(true);
              setActionMessage('2FA Password required.');
              setQrPolling(false); // Stop polling until they enter password
            }
          }
        } catch (e) {
          // ignore network errors while polling
        }
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [qrPolling, qrUuid, authPassword]);

  const handleBotStart = async () => {
    if (!botUsername || !botAccount) {
      setActionMessage('Please select an account and enter a bot username.');
      return;
    }
    setActionMessage('Sending /start to ' + botUsername + '...');
    try {
      const res = await fetch('/api/bot/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account: botAccount, bot_username: botUsername, delay: 0 })
      });
      const data = await res.json();
      if (res.ok) setActionMessage('✅ Command executed successfully.');
      else setActionMessage(data.detail || 'Failed to execute command.');
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handleScrape = async () => {
    if (!scrapeUrl || !scrapeAccount) return setActionMessage('Missing inputs.');
    setActionMessage('Initiating scrape protocol...');
    setScrapeCacheId(null);
    try {
      const res = await fetch('/api/scraper/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          account: scrapeAccount, 
          group_url: scrapeUrl,
          ...scrapeFilters
        })
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage(`✅ Scrape successful! Extracted ${data.total_scraped} members.`);
        if (data.cache_id) setScrapeCacheId(data.cache_id);
      }
      else setActionMessage(data.detail || 'Failed to scrape.');
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handleInvite = async () => {
    if (!inviteTarget) return setActionMessage('Missing target group.');
    if (inviteSelectedAccounts.length === 0) return setActionMessage('Please select at least one account to invite with.');
    
    setActionMessage('Starting inviter threads in background...');
    try {
      let res;
      if (inviteMode === 'group') {
        if (!inviteSource || !invitePrimaryAccount) return setActionMessage('Missing inputs for Group to Group.');
        res = await fetch('/api/inviter/invite-group', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            accounts: inviteSelectedAccounts, 
            primary_account: invitePrimaryAccount, 
            source_group: inviteSource, 
            target_group: inviteTarget, 
            delay: Number(inviteDelay) 
          })
        });
      } else {
        const usernameList = inviteUsernames.split(/[\n,]+/).map(u => u.trim()).filter(u => u.length > 0);
        if (usernameList.length === 0) return setActionMessage('No usernames provided.');
        res = await fetch('/api/inviter/invite-by-username', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            accounts: inviteSelectedAccounts, 
            target_group: inviteTarget, 
            usernames: usernameList, 
            delay: Number(inviteDelay) 
          })
        });
      }

      const data = await res.json();
      if (res.ok) setActionMessage('✅ Mass Inviter is now running in the background!');
      else setActionMessage(data.detail || 'Failed to start inviter.');
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handleJoin = async () => {
    if (!joinUrl || !joinAccount) return setActionMessage('Missing inputs.');
    setActionMessage('Attempting to join...');
    try {
      const res = await fetch('/api/joiner/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account: joinAccount, group_url: joinUrl, delay: 5 })
      });
      const data = await res.json();
      if (res.ok) setActionMessage('✅ ' + data.message);
      else setActionMessage(data.detail || 'Failed to join.');
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handlePoster = async () => {
    if (posterSelectedAccounts.length === 0) return setActionMessage('Select at least one account.');
    if (!posterTargets) return setActionMessage('Enter at least one target.');

    setActionMessage('Starting Auto Poster in background...');
    try {
      let res;
      if (posterMode === 'text') {
        if (!posterMessage) return setActionMessage('Enter a message to post.');
        const targetList = posterTargets.split(/[\n,]+/).map(t => t.trim()).filter(t => t.length > 0);
        if (targetList.length === 0) return setActionMessage('No valid targets.');
        
        res = await fetch('/api/poster/post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            accounts: posterSelectedAccounts,
            targets: targetList,
            message: posterMessage,
            delay: Number(posterDelay)
          })
        });
      } else {
        if (!posterVideoFolder) return setActionMessage('Enter a video folder path.');
        const targetList = posterTargets.split(/[\n,]+/).map(t => t.trim()).filter(t => t.length > 0);
        
        res = await fetch('/api/media/auto-post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            accounts: posterSelectedAccounts,
            target_chat: targetList[0], // Video poster currently only supports one target in the backend
            folder_path: posterVideoFolder,
            delay_sec: Number(posterDelay)
          })
        });
      }
      
      const data = await res.json();
      if (res.ok) setActionMessage('✅ Auto Poster started! Check logs.');
      else setActionMessage(data.detail || 'Failed to start poster.');
    } catch (e) {
      setActionMessage('Server error.');
    }
  };

  const handleBrowseFolder = async () => {
    try {
      const res = await fetch('/api/utils/browse-folder');
      const data = await res.json();
      if (data.folder) {
        setPosterVideoFolder(data.folder);
      } else if (data.error) {
        setActionMessage('Error browsing folder: ' + data.error);
      }
    } catch (e) {
      setActionMessage('Could not open folder dialog.');
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="webtool-container">
        <div className="webtool-bg"></div>
        <button onClick={onBack} className="webtool-back-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
          Back to Home
        </button>
        <div className="login-box">
          <div className="login-header">
            <svg className="login-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 2L2 12L9 15L21 2Z" />
              <path d="M21 2L13 22L9 15L21 2Z" />
            </svg>
            <h2>{isRegistering ? 'Create Web Account' : 'Web Tool Access'}</h2>
            <p>{isRegistering ? 'Register with your purchased license key' : 'Login with your credentials and license key'}</p>
          </div>
          
          {error && <div className="login-error">{error}</div>}

          <form onSubmit={handleAuth} className="login-form">
            <div className="input-group">
              <label>Username</label>
              <input type="text" name="username" value={formData.username} onChange={handleInputChange} placeholder="Enter username" />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input type="password" name="password" value={formData.password} onChange={handleInputChange} placeholder="Enter password" />
            </div>
            <div className="input-group">
              <label>License Key</label>
              <input type="text" name="license_key" value={formData.license_key} onChange={handleInputChange} placeholder="TLG-XXXX-XXXX-XXXX" />
            </div>
            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (isRegistering ? 'Registering...' : 'Authenticating...') : (isRegistering ? 'Register Account' : 'Access Dashboard')}
            </button>
            <div className="auth-toggle">
              {isRegistering ? (
                <p>Already have an account? <span onClick={() => {setIsRegistering(false); setError('');}}>Login here</span></p>
              ) : (
                <p>Don't have an account? <span onClick={() => {setIsRegistering(true); setError('');}}>Register now</span></p>
              )}
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="web-dashboard">
      <aside className="web-sidebar">
        <div className="sidebar-header">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2L2 12L9 15L21 2Z" />
            <path d="M21 2L13 22L9 15L21 2Z" />
          </svg>
          <span className="sidebar-title">TelegramSuite</span>
        </div>
        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
            Overview
          </button>
          <button className={`nav-item ${activeTab === 'accounts' ? 'active' : ''}`} onClick={() => setActiveTab('accounts')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            Manage Accounts
          </button>
          <button className={`nav-item ${activeTab === 'bot' ? 'active' : ''}`} onClick={() => setActiveTab('bot')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 16 16 12 12 8"></polyline><line x1="8" y1="12" x2="16" y2="12"></line></svg>
            Bot Starter
          </button>
          <button className={`nav-item ${activeTab === 'scraper' ? 'active' : ''}`} onClick={() => setActiveTab('scraper')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Group Scraper
          </button>
          <button className={`nav-item ${activeTab === 'inviter' ? 'active' : ''}`} onClick={() => setActiveTab('inviter')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
            Mass Inviter
          </button>
          <button className={`nav-item ${activeTab === 'poster' ? 'active' : ''}`} onClick={() => setActiveTab('poster')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13"></path><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            Auto Poster
          </button>
          <button className={`nav-item ${activeTab === 'joiner' ? 'active' : ''}`} onClick={() => setActiveTab('joiner')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h6v6"></path><path d="M10 14L21 3"></path><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path></svg>
            Auto Joiner
          </button>
          <button className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
            Process Logs
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">{formData.username.charAt(0).toUpperCase()}</div>
            <div className="user-info">
              <span className="username">{formData.username}</span>
              <span className="license-badge">Pro License</span>
            </div>
          </div>
          <button onClick={() => { 
            setIsLoggedIn(false); 
            localStorage.removeItem('isLoggedIn'); 
            localStorage.removeItem('formData'); 
          }} className="logout-btn">Logout</button>
        </div>
      </aside>
      <main className="web-main">
        <header className="main-header">
          <h1>
            {activeTab === 'dashboard' && 'Dashboard Overview'}
            {activeTab === 'accounts' && 'Account Management'}
            {activeTab === 'bot' && 'Auto Bot Clicker'}
            {activeTab === 'scraper' && 'Advanced Data Scraper'}
            {activeTab === 'inviter' && 'Mass Inviter'}
            {activeTab === 'poster' && 'Auto Poster'}
            {activeTab === 'joiner' && 'Auto Group Joiner'}
            {activeTab === 'logs' && 'Live Process Logs'}
          </h1>
          <button onClick={onBack} className="btn-exit">Exit Tool</button>
        </header>
        <div className="main-content">
          {actionMessage && <div className="action-alert">{actionMessage}</div>}
          
          {activeTab === 'dashboard' && (
            <div className="dashboard-grid">
              <div className="dash-card">
                <h3>License Status</h3>
                <div className="status-value active">Active</div>
                <p>Key: {formData.license_key.substring(0, 7)}***</p>
              </div>
              <div className="dash-card">
                <h3>Sessions Connected</h3>
                <div className="status-value">{accounts.length} / 10</div>
                <p>{accounts.length > 0 ? `${accounts.length} active Telegram sessions.` : 'No active Telegram sessions.'}</p>
              </div>
              <div className="dash-card action-card">
                <h3>Start Campaign</h3>
                <p>Ready to automate your workflow?</p>
                <button onClick={() => setActiveTab('bot')} className="dash-action-btn">Launch Automation</button>
              </div>
            </div>
          )}

          {activeTab === 'accounts' && (
            <div className="tool-module">
              <h2>Account Management</h2>
              <p>Your connected Telegram accounts ({accounts.length})</p>
              
              {accounts.length > 0 && (
                <div className="accounts-list" style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  {accounts.map((acc, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                      <span>📱 {acc.phone}</span>
                      <span style={{ color: 'var(--accent-blue)' }}>Active</span>
                    </div>
                  ))}
                </div>
              )}

              <h3>Add New Session</h3>
              <div className="tg-login-card">
                <div className="tg-login-header">
                  <div className="tg-logo-circle">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"></path></svg>
                  </div>
                  <h4>{loginMode === 'phone' ? 'Log in to Telegram' : 'Log in by QR Code'}</h4>
                  <p>{loginMode === 'phone' ? 'Please confirm your country code and enter your phone number.' : 'Go to Settings > Devices > Link Desktop Device'}</p>
                </div>

                {loginMode === 'phone' && (
                  <div className="tg-login-body">
                    <div className="tg-input-wrap">
                      <label>Phone Number</label>
                      <input className="tg-input" type="text" placeholder="+1 (234) 567-8900" value={authPhone} onChange={(e) => setAuthPhone(e.target.value)} disabled={isCodeRequested} />
                    </div>
                    
                    {isCodeRequested && (
                      <div className="tg-input-wrap animate-fade">
                        <label>Login Code</label>
                        <input className="tg-input" type="text" placeholder="Code" value={authCode} onChange={(e) => setAuthCode(e.target.value)} />
                      </div>
                    )}

                    {isPasswordRequired && (
                      <div className="tg-input-wrap animate-fade">
                        <label>2FA Password</label>
                        <input className="tg-input" type="password" placeholder="Password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} />
                      </div>
                    )}

                    <div className="tg-actions">
                      {!isCodeRequested ? (
                        <button className="tg-btn-primary" onClick={handleRequestCode}>NEXT</button>
                      ) : (
                        <button className="tg-btn-primary" onClick={handleConfirmCode}>CONFIRM</button>
                      )}
                    </div>
                  </div>
                )}

                {loginMode === 'qr' && (
                  <div className="tg-login-body" style={{ textAlign: 'center' }}>
                    {!qrUrl ? (
                      <button className="tg-btn-primary" onClick={requestQRLogin}>Generate QR</button>
                    ) : (
                      <div className="tg-qr-wrap animate-fade">
                        <div className="tg-qr-box">
                          <img src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrUrl)}`} alt="Telegram QR" />
                        </div>
                        {isPasswordRequired ? (
                          <div className="tg-input-wrap" style={{ textAlign: 'left', marginTop: '1.5rem' }}>
                            <label>2FA Password</label>
                            <input className="tg-input" type="password" placeholder="Password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} />
                            <button className="tg-btn-primary" style={{ marginTop: '1rem' }} onClick={() => setQrPolling(true)}>SUBMIT</button>
                          </div>
                        ) : (
                          <p className="tg-subtext">Waiting for scan...</p>
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="tg-login-footer">
                  <button className="tg-btn-link" onClick={() => {
                    setLoginMode(loginMode === 'phone' ? 'qr' : 'phone');
                    setQrUrl('');
                    setIsCodeRequested(false);
                    setQrPolling(false);
                  }}>
                    {loginMode === 'phone' ? 'LOG IN BY QR CODE' : 'LOG IN BY PHONE NUMBER'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'bot' && (
            <div className="tool-module">
              <h2>Auto Bot Clicker</h2>
              <div className="tg-login-card" style={{ maxWidth: '400px' }}>
                <div className="tg-login-header">
                  <h4>Send /start Command</h4>
                  <p>Trigger any telegram bot automatically.</p>
                </div>
                <div className="tg-login-body">
                  <div className="tg-input-wrap">
                    <label>Select Session</label>
                    <select className="tg-input" value={botAccount} onChange={(e) => setBotAccount(e.target.value)}>
                      <option value="">-- Choose Account --</option>
                      {accounts.map((a, i) => <option key={i} value={a.session_filename}>{a.phone}</option>)}
                    </select>
                  </div>
                  <div className="tg-input-wrap">
                    <label>Target Bot Username</label>
                    <input className="tg-input" type="text" placeholder="@YourTargetBot" value={botUsername} onChange={(e) => setBotUsername(e.target.value)} />
                  </div>
                  <div className="tg-actions">
                    <button className="tg-btn-primary" onClick={handleBotStart}>START CAMPAIGN</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scraper' && (
            <div className="tool-module">
              <h2>Group Scraper</h2>
              <div className="tg-login-card" style={{ maxWidth: '400px' }}>
                <div className="tg-login-header">
                  <h4>Extract Members</h4>
                  <p>Scrape active users from public or private groups.</p>
                </div>
                <div className="tg-login-body">
                  <div className="tg-input-wrap">
                    <label>Select Session</label>
                    <select className="tg-input" value={scrapeAccount} onChange={(e) => setScrapeAccount(e.target.value)}>
                      <option value="">-- Choose Account --</option>
                      {accounts.map((a, i) => <option key={i} value={a.session_filename}>{a.phone}</option>)}
                    </select>
                  </div>
                  <div className="tg-input-wrap">
                    <label>Target Group Link</label>
                    <input className="tg-input" type="text" placeholder="https://t.me/target_group" value={scrapeUrl} onChange={(e) => setScrapeUrl(e.target.value)} />
                  </div>
                  
                  <div className="tg-filters">
                    <label style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', marginBottom: '8px'}}>
                      <input type="checkbox" checked={scrapeFilters.filter_has_username} onChange={e => setScrapeFilters({...scrapeFilters, filter_has_username: e.target.checked})} />
                      Only Users with @Username
                    </label>
                    <label style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', marginBottom: '8px'}}>
                      <input type="checkbox" checked={scrapeFilters.filter_no_bots} onChange={e => setScrapeFilters({...scrapeFilters, filter_no_bots: e.target.checked})} />
                      Exclude Bots
                    </label>
                    <label style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', marginBottom: '16px'}}>
                      <input type="checkbox" checked={scrapeFilters.filter_active_recently} onChange={e => setScrapeFilters({...scrapeFilters, filter_active_recently: e.target.checked})} />
                      Only Recently Active
                    </label>
                  </div>

                  <div className="tg-actions">
                    <button className="tg-btn-primary" onClick={handleScrape}>START SCRAPER</button>
                  </div>

                  {scrapeCacheId && (
                    <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
                      <button className="tg-btn-secondary" style={{flex: 1, padding: '10px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', color: 'white', cursor: 'pointer', fontWeight: 600}} onClick={() => window.open(`/api/scraper/export/${scrapeCacheId}`, '_blank')}>📥 CSV</button>
                      <button className="tg-btn-secondary" style={{flex: 1, padding: '10px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', color: 'white', cursor: 'pointer', fontWeight: 600}} onClick={() => window.open(`/api/scraper/export-txt/${scrapeCacheId}`, '_blank')}>📥 TXT</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'inviter' && (
            <div className="tool-module">
              <h2>Mass Inviter</h2>
              <div className="tg-login-card" style={{ maxWidth: '400px' }}>
                <div className="tg-login-header">
                  <h4>Invite Users</h4>
                  <p>Bulk invite members using ALL your active connected accounts ({accounts.length} available) to bypass rate limits.</p>
                </div>
                <div className="tg-login-body">
                  <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                    <button 
                      className={`tg-btn-secondary ${inviteMode === 'group' ? 'active' : ''}`}
                      style={{ flex: 1, padding: '10px', borderRadius: '8px', cursor: 'pointer', border: 'none', background: inviteMode === 'group' ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', color: 'white', fontWeight: 600 }}
                      onClick={() => setInviteMode('group')}
                    >
                      Group to Group
                    </button>
                    <button 
                      className={`tg-btn-secondary ${inviteMode === 'username' ? 'active' : ''}`}
                      style={{ flex: 1, padding: '10px', borderRadius: '8px', cursor: 'pointer', border: 'none', background: inviteMode === 'username' ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', color: 'white', fontWeight: 600 }}
                      onClick={() => setInviteMode('username')}
                    >
                      By Username
                    </button>
                  </div>

                  <div className="tg-input-wrap">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <label style={{ margin: 0 }}>Select Inviter Accounts ({inviteSelectedAccounts.length}/{accounts.length})</label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="tg-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem', borderRadius: '4px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', cursor: 'pointer' }} onClick={() => setInviteSelectedAccounts(accounts.map(a => a.session_filename))}>Select All</button>
                        <button className="tg-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem', borderRadius: '4px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', cursor: 'pointer' }} onClick={() => setInviteSelectedAccounts([])}>Clear</button>
                      </div>
                    </div>
                    <div style={{ maxHeight: '150px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                      {accounts.map((a, i) => (
                        <label key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9rem', cursor: 'pointer' }}>
                          <input 
                            type="checkbox" 
                            checked={inviteSelectedAccounts.includes(a.session_filename)}
                            onChange={(e) => {
                              if (e.target.checked) setInviteSelectedAccounts([...inviteSelectedAccounts, a.session_filename]);
                              else setInviteSelectedAccounts(inviteSelectedAccounts.filter(s => s !== a.session_filename));
                            }}
                          />
                          📱 {a.phone}
                        </label>
                      ))}
                    </div>
                  </div>

                  {inviteMode === 'group' && (
                    <>
                      <div className="tg-input-wrap">
                        <label>Select Primary Scraper Session</label>
                        <select className="tg-input" value={invitePrimaryAccount} onChange={(e) => setInvitePrimaryAccount(e.target.value)}>
                          <option value="">-- Choose Account --</option>
                          {accounts.map((a, i) => <option key={i} value={a.session_filename}>{a.phone}</option>)}
                        </select>
                      </div>
                      <div className="tg-input-wrap">
                        <label>Source Group (Where to scrape from)</label>
                        <input className="tg-input" type="text" placeholder="https://t.me/source_group" value={inviteSource} onChange={(e) => setInviteSource(e.target.value)} />
                      </div>
                    </>
                  )}

                  {inviteMode === 'username' && (
                    <div className="tg-input-wrap">
                      <label>Usernames (comma or newline separated)</label>
                      <textarea className="tg-input" style={{ minHeight: '100px', resize: 'vertical', paddingTop: '12px' }} placeholder="@user1, @user2&#10;@user3" value={inviteUsernames} onChange={(e) => setInviteUsernames(e.target.value)} />
                    </div>
                  )}

                  <div className="tg-input-wrap">
                    <label>Target Group (Where to invite to)</label>
                    <input className="tg-input" type="text" placeholder="https://t.me/my_group" value={inviteTarget} onChange={(e) => setInviteTarget(e.target.value)} />
                  </div>
                  <div className="tg-input-wrap">
                    <label>Delay Between Invites (Seconds)</label>
                    <input className="tg-input" type="number" placeholder="30" value={inviteDelay} onChange={(e) => setInviteDelay(e.target.value)} />
                  </div>
                  <div className="tg-actions">
                    <button className="tg-btn-primary" onClick={handleInvite}>START MASS INVITING</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'poster' && (
            <div className="tool-module">
              <h2>Auto Poster</h2>
              <div className="tg-login-card" style={{ maxWidth: '400px' }}>
                <div className="tg-login-header">
                  <h4>Broadcast Messages</h4>
                  <p>Send messages to multiple groups or users automatically.</p>
                </div>
                <div className="tg-login-body">
                  <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                    <button 
                      className={`tg-btn-secondary ${posterMode === 'text' ? 'active' : ''}`}
                      style={{ flex: 1, padding: '10px', borderRadius: '8px', cursor: 'pointer', border: 'none', background: posterMode === 'text' ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', color: 'white', fontWeight: 600 }}
                      onClick={() => setPosterMode('text')}
                    >
                      Text Message
                    </button>
                    <button 
                      className={`tg-btn-secondary ${posterMode === 'video' ? 'active' : ''}`}
                      style={{ flex: 1, padding: '10px', borderRadius: '8px', cursor: 'pointer', border: 'none', background: posterMode === 'video' ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', color: 'white', fontWeight: 600 }}
                      onClick={() => setPosterMode('video')}
                    >
                      Video Folder
                    </button>
                  </div>

                  <div className="tg-input-wrap">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <label style={{ margin: 0 }}>Select Sender Accounts ({posterSelectedAccounts.length}/{accounts.length})</label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="tg-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem', borderRadius: '4px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', cursor: 'pointer' }} onClick={() => setPosterSelectedAccounts(accounts.map(a => a.session_filename))}>All</button>
                        <button className="tg-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem', borderRadius: '4px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', cursor: 'pointer' }} onClick={() => setPosterSelectedAccounts([])}>Clear</button>
                      </div>
                    </div>
                    <div style={{ maxHeight: '150px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                      {accounts.map((a, i) => (
                        <label key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9rem', cursor: 'pointer' }}>
                          <input 
                            type="checkbox" 
                            checked={posterSelectedAccounts.includes(a.session_filename)}
                            onChange={(e) => {
                              if (e.target.checked) setPosterSelectedAccounts([...posterSelectedAccounts, a.session_filename]);
                              else setPosterSelectedAccounts(posterSelectedAccounts.filter(s => s !== a.session_filename));
                            }}
                          />
                          📱 {a.phone}
                        </label>
                      ))}
                    </div>
                  </div>
                  
                  <div className="tg-input-wrap">
                    <label>{posterMode === 'text' ? 'Target Groups/Users (comma or newline separated)' : 'Target Group/User'}</label>
                    <textarea className="tg-input" style={{ minHeight: '60px', resize: 'vertical', paddingTop: '12px' }} placeholder="@group1, @user2&#10;https://t.me/joinchat/..." value={posterTargets} onChange={(e) => setPosterTargets(e.target.value)} />
                  </div>
                  
                  {posterMode === 'text' && (
                    <div className="tg-input-wrap">
                      <label>Message Text</label>
                      <textarea className="tg-input" style={{ minHeight: '120px', resize: 'vertical', paddingTop: '12px' }} placeholder="Hello! This is an automated message." value={posterMessage} onChange={(e) => setPosterMessage(e.target.value)} />
                    </div>
                  )}

                  {posterMode === 'video' && (
                    <div className="tg-input-wrap">
                      <label>Local Folder Path (containing .mp4 videos)</label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input className="tg-input" type="text" placeholder="/Users/name/Downloads/Videos" value={posterVideoFolder} onChange={(e) => setPosterVideoFolder(e.target.value)} style={{ flex: 1 }} />
                        <button className="tg-btn-secondary" style={{ padding: '0 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.05)', color: 'white', cursor: 'pointer', whiteSpace: 'nowrap' }} onClick={handleBrowseFolder}>
                          Browse...
                        </button>
                      </div>
                    </div>
                  )}
                  
                  <div className="tg-input-wrap">
                    <label>Delay Between Posts (Seconds)</label>
                    <input className="tg-input" type="number" placeholder="15" value={posterDelay} onChange={(e) => setPosterDelay(e.target.value)} />
                  </div>
                  
                  <div className="tg-actions">
                    <button className="tg-btn-primary" onClick={handlePoster}>START POSTING</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'joiner' && (
            <div className="tool-module">
              <h2>Auto Group Joiner</h2>
              <div className="tg-login-card" style={{ maxWidth: '400px' }}>
                <div className="tg-login-header">
                  <h4>Join Groups</h4>
                  <p>Automatically join groups/channels with a specific account.</p>
                </div>
                <div className="tg-login-body">
                  <div className="tg-input-wrap">
                    <label>Select Session</label>
                    <select className="tg-input" value={joinAccount} onChange={(e) => setJoinAccount(e.target.value)}>
                      <option value="">-- Choose Account --</option>
                      {accounts.map((a, i) => <option key={i} value={a.session_filename}>{a.phone}</option>)}
                    </select>
                  </div>
                  <div className="tg-input-wrap">
                    <label>Group Link</label>
                    <input className="tg-input" type="text" placeholder="https://t.me/my_group" value={joinUrl} onChange={(e) => setJoinUrl(e.target.value)} />
                  </div>
                  <div className="tg-actions">
                    <button className="tg-btn-primary" onClick={handleJoin}>JOIN GROUP</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="tool-module">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2>Backend Terminal</h2>
                <button 
                  onClick={async () => { await fetch('/api/logs/clear', {method: 'POST'}); setLogs([]); }}
                  style={{ padding: '8px 16px', background: 'rgba(255,100,100,0.2)', color: '#ff6b6b', border: '1px solid rgba(255,100,100,0.4)', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Clear Logs
                </button>
              </div>
              <p>Monitor your background tasks (Inviter, Scraper, Joiner) in real time.</p>
              <div style={{ 
                background: '#111', 
                border: '1px solid #333', 
                borderRadius: '8px', 
                padding: '16px', 
                fontFamily: 'monospace', 
                height: '400px', 
                overflowY: 'auto',
                color: '#00ff00',
                lineHeight: '1.5',
                display: 'flex',
                flexDirection: 'column'
              }}>
                {logs.length === 0 ? (
                  <div style={{ color: '#888', fontStyle: 'italic' }}>Waiting for output...</div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{log}</div>
                  ))
                )}
                {/* Auto-scroll anchor */}
                <div style={{ float: 'left', clear: 'both' }} ref={(el) => { el && el.scrollIntoView({ behavior: 'smooth' }) }}></div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
