import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, Users, Database, ShieldCheck, Settings, Bell, 
  Activity, TrendingUp, Search, Plus, Terminal
} from 'lucide-react';
import './index.css';

const API_BASE = 'http://127.0.0.1:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [accounts, setAccounts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Login State
  const [loginPhone, setLoginPhone] = useState('');
  const [loginCode, setLoginCode] = useState('');
  const [loginStep, setLoginStep] = useState(0); 

  // Scraper State
  const [scrapeAccount, setScrapeAccount] = useState('');
  const [scrapeGroup, setScrapeGroup] = useState('');
  const [scrapeResult, setScrapeResult] = useState(null);
  const [scrapeCacheId, setScrapeCacheId] = useState(null);
  
  const [scrapeGroupsResult, setScrapeGroupsResult] = useState(null);
  const [scrapeGroupsCacheId, setScrapeGroupsCacheId] = useState(null);

  // Scrape & Add State
  const [saSourceGroup, setSaSourceGroup] = useState('');
  const [saTargetGroup, setSaTargetGroup] = useState('');
  const [saDelay, setSaDelay] = useState(5.0);
  const [saPrimaryAccount, setSaPrimaryAccount] = useState('');

  // Inviter State
  const [inviteGroup, setInviteGroup] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  
  useEffect(() => {
    fetchAccounts();
    const interval = setInterval(() => fetchLogs(), 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchAccounts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/accounts`);
      setAccounts(res.data.accounts.map((acc, idx) => ({
        id: idx, phone: acc, status: 'Active', lastActivity: 'Live'
      })));
      if (res.data.accounts.length > 0) {
        if (!scrapeAccount) setScrapeAccount(res.data.accounts[0]);
        if (!saPrimaryAccount) setSaPrimaryAccount(res.data.accounts[0]);
      }
    } catch (err) { console.error(err); }
  };

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/logs`);
      setLogs(res.data.logs.slice(-20)); 
    } catch (err) { console.error(err); }
  };

  const handleRequestCode = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/accounts/login/request`, { phone: loginPhone });
      setLoginStep(1);
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Failed to send code'); }
    setLoading(false);
  };

  const handleConfirmLogin = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/accounts/login/confirm`, { phone: loginPhone, code: loginCode });
      setLoginStep(0); setLoginPhone(''); setLoginCode('');
      fetchAccounts(); setActiveTab('Dashboard');
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Invalid code'); }
    setLoading(false);
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg(''); setScrapeResult(null); setScrapeCacheId(null);
    try {
      const res = await axios.post(`${API_BASE}/scraper/scrape`, {
        account: scrapeAccount,
        group_url: scrapeGroup
      });
      setScrapeResult(`Successfully scraped ${res.data.count} members!`);
      setScrapeCacheId(res.data.cache_id);
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Scraping failed'); }
    setLoading(false);
  };

  const handleScrapeGroups = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg(''); setScrapeGroupsResult(null); setScrapeGroupsCacheId(null);
    try {
      const res = await axios.post(`${API_BASE}/scraper/groups`, {
        account: scrapeAccount
      });
      setScrapeGroupsResult(`Successfully scraped ${res.data.count} groups!`);
      setScrapeGroupsCacheId(res.data.cache_id);
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Scraping groups failed'); }
    setLoading(false);
  };

  const handleScrapeAndAdd = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg('');
    try {
      if (accounts.length === 0) throw new Error("No active accounts available");
      if (!saPrimaryAccount) throw new Error("Please select a primary account to scrape with");
      
      await axios.post(`${API_BASE}/inviter/invite-group`, {
        accounts: accounts.map(a => a.phone),
        primary_account: saPrimaryAccount,
        source_group: saSourceGroup,
        target_group: saTargetGroup,
        delay: parseFloat(saDelay)
      });
      setActiveTab('Terminal Logs'); // Jump to logs to see it working!
    } catch (err) { setErrorMsg(err.response?.data?.detail || err.message || 'Scrape & Add failed'); }
    setLoading(false);
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!csvFile) { setErrorMsg("Please upload a CSV file"); return; }
    setLoading(true); setErrorMsg('');
    try {
      const formData = new FormData();
      formData.append("target_group", inviteGroup);
      formData.append("accounts", JSON.stringify(accounts.map(a => a.phone)));
      formData.append("delay", 5.0);
      formData.append("file", csvFile);
      
      await axios.post(`${API_BASE}/inviter/invite-csv`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setActiveTab('Terminal Logs'); // Jump to logs to see it working!
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Inviter failed'); }
    setLoading(false);
  };

  return (
    <div className="app-container">
      <aside className="sidebar glass-panel" style={{ borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none' }}>
        <div className="sidebar-logo">
          <Send size={28} strokeWidth={2.5} /> TeleMaster
        </div>
        <nav>
          {['Dashboard', 'Add Account', 'Scraper', 'Scrape & Add', 'Inviter', 'Terminal Logs'].map((item) => (
            <div 
              key={item} 
              className={`nav-item ${activeTab === item ? 'active' : ''}`}
              onClick={() => { setActiveTab(item); setErrorMsg(''); }}
            >
              {item === 'Dashboard' && <Activity size={20} />}
              {item === 'Add Account' && <Plus size={20} />}
              {item === 'Scraper' && <Database size={20} />}
              {item === 'Scrape & Add' && <TrendingUp size={20} />}
              {item === 'Inviter' && <Send size={20} />}
              {item === 'Terminal Logs' && <Terminal size={20} />}
              {item}
            </div>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="page-title animate-fade-in">
            <h1>{activeTab} Overview</h1>
            <p>Your Telegram Suite operations control center.</p>
          </div>
          <div className="user-profile">
            <button className="notification-btn" onClick={fetchAccounts}><Activity size={20} /></button>
            <div className="avatar">TM</div>
          </div>
        </header>

        {activeTab === 'Dashboard' && (
          <div className="animate-fade-in">
            <div className="stats-grid">
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>Saved Accounts</span><div className="stat-icon blue"><Users /></div>
                </div>
                <div className="stat-value">{accounts.length}</div>
              </div>
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>System Health</span><div className="stat-icon green"><Activity /></div>
                </div>
                <div className="stat-value">Online</div>
              </div>
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>Pending Logs</span><div className="stat-icon purple"><Terminal /></div>
                </div>
                <div className="stat-value" onClick={() => setActiveTab('Terminal Logs')} style={{cursor: 'pointer'}}>{logs.length}</div>
              </div>
            </div>

            <div className="data-table-container glass-panel">
              <div className="table-header">
                <h2>Managed Telegram Accounts</h2>
                <button className="glass-button" onClick={() => setActiveTab('Add Account')}>+ Add New</button>
              </div>
              {accounts.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px' }}>No accounts found. Add one to get started.</p>
              ) : (
                <table className="data-table">
                  <thead><tr><th>PHONE / SESSION</th><th>STATUS</th><th>LAST ACTIVITY</th></tr></thead>
                  <tbody>
                    {accounts.map((acc) => (
                      <tr key={acc.id}>
                        <td style={{ fontWeight: 500 }}>{acc.phone}</td>
                        <td><span className={`status-badge active`}>{acc.status}</span></td>
                        <td style={{ color: 'var(--text-secondary)' }}>{acc.lastActivity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'Add Account' && (
          <div className="animate-fade-in">
            <div className="glass-panel" style={{ padding: '30px', maxWidth: '500px', margin: '0 auto' }}>
              <h2 style={{ marginBottom: '20px' }}>Login New Account</h2>
              {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}
              {loginStep === 0 ? (
                <form onSubmit={handleRequestCode}>
                  <div className="form-group">
                    <label className="form-label">Phone Number (with +)</label>
                    <input type="text" className="glass-input" placeholder="+1234567890" value={loginPhone} onChange={(e) => setLoginPhone(e.target.value)} required />
                  </div>
                  <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading}>{loading ? 'Requesting...' : 'Request Code'}</button>
                </form>
              ) : (
                <form onSubmit={handleConfirmLogin}>
                  <div className="form-group">
                    <label className="form-label">Login Code sent to {loginPhone}</label>
                    <input type="text" className="glass-input" placeholder="12345" value={loginCode} onChange={(e) => setLoginCode(e.target.value)} required />
                  </div>
                  <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading}>{loading ? 'Verifying...' : 'Verify & Login'}</button>
                </form>
              )}
            </div>
          </div>
        )}

        {activeTab === 'Scraper' && (
          <>
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '600px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '20px' }}>Scrape Group Members</h2>
            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}
            {scrapeResult && (
              <div style={{ color: 'var(--accent-green)', marginBottom: '15px', padding: '15px', background: 'rgba(16,185,129,0.1)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <span>{scrapeResult}</span>
                {scrapeCacheId && (
                  <a href={`${API_BASE}/scraper/export/${scrapeCacheId}`} target="_blank" rel="noreferrer" style={{textDecoration: 'none'}}>
                    <button type="button" className="glass-button secondary" style={{ width: '100%' }}>Download CSV File</button>
                  </a>
                )}
              </div>
            )}
            
            <form onSubmit={handleScrape}>
              <div className="form-group">
                <label className="form-label">Select Account to Scrape With</label>
                <select className="glass-input" value={scrapeAccount} onChange={(e) => setScrapeAccount(e.target.value)} required>
                  <option value="" disabled>Select an account</option>
                  {accounts.map(a => <option key={a.id} value={a.phone}>{a.phone}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Target Group Username or URL</label>
                <input type="text" className="glass-input" placeholder="https://t.me/example_group" value={scrapeGroup} onChange={(e) => setScrapeGroup(e.target.value)} required />
              </div>
              <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading || accounts.length === 0}>
                {loading ? 'Scraping...' : 'Start Scraping Members'}
              </button>
            </form>
          </div>
          
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '600px', margin: '30px auto' }}>
            <h2 style={{ marginBottom: '20px' }}>Scrape My Joined Groups</h2>
            {scrapeGroupsResult && (
              <div style={{ color: 'var(--accent-green)', marginBottom: '15px', padding: '15px', background: 'rgba(16,185,129,0.1)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <span>{scrapeGroupsResult}</span>
                {scrapeGroupsCacheId && (
                  <a href={`${API_BASE}/scraper/export-groups/${scrapeGroupsCacheId}`} target="_blank" rel="noreferrer" style={{textDecoration: 'none'}}>
                    <button type="button" className="glass-button secondary" style={{ width: '100%' }}>Download Groups CSV</button>
                  </a>
                )}
              </div>
            )}
            
            <form onSubmit={handleScrapeGroups}>
              <div className="form-group">
                <label className="form-label">Select Account to Scrape With</label>
                <select className="glass-input" value={scrapeAccount} onChange={(e) => setScrapeAccount(e.target.value)} required>
                  <option value="" disabled>Select an account</option>
                  {accounts.map(a => <option key={a.id} value={a.phone}>{a.phone}</option>)}
                </select>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                This will retrieve a complete list of all Telegram groups and channels that this account has joined.
              </p>
              <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading || accounts.length === 0}>
                {loading ? 'Scraping...' : 'Scrape Joined Groups'}
              </button>
            </form>
          </div>
          </>
        )}

        {activeTab === 'Scrape & Add' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '600px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '20px' }}>Scrape & Add (Group to Group)</h2>
            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}
            
            <form onSubmit={handleScrapeAndAdd}>
              <div className="form-group">
                <label className="form-label">Primary Account (Used to Scrape Source)</label>
                <select className="glass-input" value={saPrimaryAccount} onChange={(e) => setSaPrimaryAccount(e.target.value)} required>
                  <option value="" disabled>Select an account</option>
                  {accounts.map(a => <option key={a.id} value={a.phone}>{a.phone}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Source Group (Scrape From)</label>
                <input type="text" className="glass-input" placeholder="https://t.me/source_group" value={saSourceGroup} onChange={(e) => setSaSourceGroup(e.target.value)} required />
              </div>
              <div className="form-group">
                <label className="form-label">Target Group (Add To)</label>
                <input type="text" className="glass-input" placeholder="https://t.me/target_group" value={saTargetGroup} onChange={(e) => setSaTargetGroup(e.target.value)} required />
              </div>
              <div className="form-group">
                <label className="form-label">Action Delay (seconds between adds)</label>
                <input type="number" step="0.5" min="1" className="glass-input" value={saDelay} onChange={(e) => setSaDelay(e.target.value)} required />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                This will use your selected Primary Account to scrape the Source Group, and then use <b>ALL {accounts.length}</b> active accounts to distribute the workload of adding members to the Target Group.
              </p>
              <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading || accounts.length === 0}>
                {loading ? 'Starting Auto-Bot...' : 'Start Scrape & Add'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'Inviter' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '600px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '20px' }}>Mass Inviter (From CSV)</h2>
            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}
            <form onSubmit={handleInvite}>
              <div className="form-group">
                <label className="form-label">Upload Users CSV</label>
                <input type="file" accept=".csv" className="glass-input" onChange={(e) => setCsvFile(e.target.files[0])} required style={{padding: '10px'}} />
              </div>
              <div className="form-group">
                <label className="form-label">Target Group to Invite Users To</label>
                <input type="text" className="glass-input" placeholder="https://t.me/your_group" value={inviteGroup} onChange={(e) => setInviteGroup(e.target.value)} required />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                This will automatically distribute the workload across all <b>{accounts.length}</b> active accounts.
              </p>
              <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading || accounts.length === 0}>
                {loading ? 'Starting...' : 'Start Mass Inviter'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'Terminal Logs' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '20px', minHeight: '400px' }}>
            <h2 style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between' }}>
              System Logs 
              <button className="glass-button secondary" style={{ padding: '4px 10px', fontSize: '0.8rem' }} onClick={() => axios.post(`${API_BASE}/logs/clear`)}>Clear Logs</button>
            </h2>
            <div style={{ background: '#000', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '14px', height: '400px', overflowY: 'auto' }}>
              {logs.length === 0 ? (
                <div style={{ color: 'var(--text-secondary)' }}>Waiting for activity...</div>
              ) : (
                logs.map((log, i) => <div key={i} style={{ color: '#0f0', marginBottom: '4px', wordBreak: 'break-all' }}>{log}</div>)
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
