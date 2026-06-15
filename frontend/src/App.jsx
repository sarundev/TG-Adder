import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Users, Database, ShieldCheck, Settings, Bell, 
  Activity, TrendingUp, Search, Plus, Terminal, Flame,
  Key, Eye, EyeOff, Lock, LogOut, CheckCircle, XCircle
} from 'lucide-react';
import './index.css';

// Use relative /api path if running on a production host (not localhost/Vite)
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? (window.location.port === '5173' ? 'http://127.0.0.1:8000/api' : '/api') 
  : '/api';

// ── Hardware ID generation (browser fingerprint) ──
async function generateHWID() {
  const raw = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    navigator.hardwareConcurrency || '',
    navigator.platform || '',
  ].join('|');
  // SHA-256 hash via Web Crypto
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('').slice(0,32);
}

// ── License Gate Component ──
function LicenseGate({ onUnlocked }) {
  const [key, setKey]       = useState('');
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | checking | success | error
  const [errMsg, setErrMsg] = useState('');
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!key.trim()) return;
    setStatus('checking'); setErrMsg('');
    try {
      const hwid = await generateHWID();
      await axios.post(`${API_BASE}/license/verify`, { token: key.trim(), hwid });
      setStatus('success');
      localStorage.setItem('tg_license_key', key.trim());
      setTimeout(() => onUnlocked(), 1200);
    } catch (err) {
      setStatus('error');
      setErrMsg(err.response?.data?.detail || 'Invalid or expired license key.');
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.18) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(168,85,247,0.15) 0%, transparent 55%), #0a0a12',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'Inter', 'Outfit', system-ui, sans-serif"
    }}>
      {/* Animated orbs */}
      {[0,1,2].map(i => (
        <div key={i} style={{
          position: 'absolute',
          width:  [320,200,260][i] + 'px',
          height: [320,200,260][i] + 'px',
          borderRadius: '50%',
          background: ['rgba(99,102,241,0.08)','rgba(168,85,247,0.07)','rgba(59,130,246,0.06)'][i],
          top:  ['15%','60%','30%'][i],
          left: ['10%','70%','55%'][i],
          filter: 'blur(60px)',
          animation: `float-orb ${[12,16,10][i]}s ease-in-out infinite alternate`,
          pointerEvents: 'none'
        }} />
      ))}

      {/* Card */}
      <div style={{
        width: '100%', maxWidth: '440px', margin: '0 20px',
        padding: '44px 40px 36px',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(24px)',
        borderRadius: '24px',
        border: '1px solid rgba(255,255,255,0.1)',
        boxShadow: '0 32px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08)',
        position: 'relative', overflow: 'hidden'
      }}>
        {/* Top shimmer line */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
          background: 'linear-gradient(90deg, transparent, #6366f1, #a855f7, transparent)'
        }} />

        {/* Icon */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '18px', margin: '0 auto 16px',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.3))',
            border: '1px solid rgba(99,102,241,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 30px rgba(99,102,241,0.3)'
          }}>
            <Lock size={28} color="#a5b4fc" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', margin: 0 }}>TG Adder Suite</h1>
          <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: '0.88rem', marginTop: '6px' }}>
            Enter your license key to continue
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
              License Key
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
              <input
                ref={inputRef}
                type={showKey ? 'text' : 'password'}
                value={key}
                onChange={e => { setKey(e.target.value); setStatus('idle'); setErrMsg(''); }}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                spellCheck={false}
                autoComplete="off"
                style={{
                  width: '100%', padding: '13px 46px 13px 42px',
                  background: 'rgba(255,255,255,0.06)',
                  border: status === 'error'   ? '1.5px solid rgba(239,68,68,0.6)'
                        : status === 'success' ? '1.5px solid rgba(16,185,129,0.6)'
                        : '1.5px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px', color: '#fff',
                  fontSize: '1rem', fontFamily: 'monospace', letterSpacing: '0.12em',
                  outline: 'none', boxSizing: 'border-box',
                  transition: 'border-color 0.2s',
                }}
              />
              <button type="button" onClick={() => setShowKey(v => !v)} style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.35)',
                padding: '4px', display: 'flex', alignItems: 'center'
              }}>
                {showKey ? <EyeOff size={16}/> : <Eye size={16}/>}
              </button>
            </div>

            {/* Error message */}
            {status === 'error' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#fca5a5', fontSize: '0.82rem' }}>
                <XCircle size={14} />{errMsg}
              </div>
            )}
            {status === 'success' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#6ee7b7', fontSize: '0.82rem' }}>
                <CheckCircle size={14} />License verified! Unlocking...
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={status === 'checking' || status === 'success' || !key.trim()}
            style={{
              width: '100%', padding: '14px',
              background: status === 'success'
                ? 'linear-gradient(135deg, rgba(16,185,129,0.4), rgba(5,150,105,0.3))'
                : 'linear-gradient(135deg, rgba(99,102,241,0.5), rgba(168,85,247,0.4))',
              border: status === 'success' ? '1px solid rgba(16,185,129,0.5)' : '1px solid rgba(99,102,241,0.5)',
              borderRadius: '12px', color: '#fff', fontSize: '0.95rem', fontWeight: 700,
              cursor: status === 'checking' || status === 'success' ? 'not-allowed' : 'pointer',
              opacity: !key.trim() ? 0.5 : 1,
              transition: 'all 0.3s',
              boxShadow: '0 4px 20px rgba(99,102,241,0.25)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
            }}
          >
            {status === 'checking' ? (
              <><span style={{ fontSize: '0.9rem' }}>⏳</span> Verifying...</>
            ) : status === 'success' ? (
              <><CheckCircle size={18} /> Unlocked!</>
            ) : (
              <><Key size={18} /> Activate License</>
            )}
          </button>
        </form>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '24px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.25)', margin: 0 }}>
            License is bound to this device · Contact admin for support
          </p>
        </div>
      </div>

      {/* Float animation keyframes */}
      <style>{`
        @keyframes float-orb {
          from { transform: translateY(0px) scale(1); }
          to   { transform: translateY(-30px) scale(1.08); }
        }
      `}</style>
    </div>
  );
}

function MainApp({ onLogout }) {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [accounts, setAccounts] = useState([]);
  const [accountDetails, setAccountDetails] = useState({}); // phone -> detail object
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Login State
  const [loginPhone, setLoginPhone] = useState('');
  const [loginCode, setLoginCode] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginStep, setLoginStep] = useState(0); 

  // Scraper State
  const [scrapeAccount, setScrapeAccount] = useState('');
  const [scrapeGroup, setScrapeGroup] = useState('');
  const [scrapeResult, setScrapeResult] = useState(null);
  const [scrapeCacheId, setScrapeCacheId] = useState(null);
  const [scrapeShowFilters, setScrapeShowFilters] = useState(false);
  const [filterHasUsername, setFilterHasUsername] = useState(false);
  const [filterHasPhone, setFilterHasPhone] = useState(false);
  const [filterNoBots, setFilterNoBots] = useState(true);
  const [filterActiveRecently, setFilterActiveRecently] = useState(false);
  const [filterHasName, setFilterHasName] = useState(false);
  
  const [scrapeGroupsResult, setScrapeGroupsResult] = useState(null);
  const [scrapeGroupsCacheId, setScrapeGroupsCacheId] = useState(null);

  // Scrape & Add State
  const [saSourceGroup, setSaSourceGroup] = useState('');
  const [saTargetGroup, setSaTargetGroup] = useState('');
  const [saDelay, setSaDelay] = useState(5.0);
  const [saPrimaryAccount, setSaPrimaryAccount] = useState('');

  // Scrape & Add — Worker Accounts
  const [saWorkerAccounts, setSaWorkerAccounts] = useState([]);
  const [saWorkerSelectAll, setSaWorkerSelectAll] = useState(true);

  // Inviter State
  const [inviteGroup, setInviteGroup] = useState('');
  const [inviterDelay, setInviterDelay] = useState(15);
  const [inviterSelectAll, setInviterSelectAll] = useState(false);
  const [inviterAccounts, setInviterAccounts] = useState([]);

  // Join Group State
  const [joinGroupTarget, setJoinGroupTarget] = useState('');
  const [joinAccounts, setJoinAccounts] = useState([]);
  const [joinSelectAll, setJoinSelectAll] = useState(false);
  const [joinDelay, setJoinDelay] = useState(15);
  
  const [inviterMode, setInviterMode] = useState('csv'); // 'csv' | 'username'
  const [usernameInput, setUsernameInput] = useState('');
  const [csvFile, setCsvFile] = useState(null);

  // Make Account Strong (Warm) State
  const [warmAccounts, setWarmAccounts] = useState([]);
  const [warmDoReact, setWarmDoReact] = useState(true);
  const [warmDoChat, setWarmDoChat] = useState(true);
  const [warmReactionsPerGroup, setWarmReactionsPerGroup] = useState(3);
  const [warmMessagesToSend, setWarmMessagesToSend] = useState(3);
  const [warmReactDelay, setWarmReactDelay] = useState(10);
  const [warmChatDelay, setWarmChatDelay] = useState(20);
  const [warmSelectAll, setWarmSelectAll] = useState(false);
  
  useEffect(() => {
    fetchAccounts();
    const interval = setInterval(() => fetchLogs(), 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchAccounts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/accounts`);
      const mapped = res.data.accounts.map((acc, idx) => ({
        id: idx, phone: acc, status: 'Active', lastActivity: 'Live'
      }));
      setAccounts(mapped);
      const phones = res.data.accounts;
      if (phones.length > 0) {
        if (!scrapeAccount) setScrapeAccount(phones[0]);
        if (!saPrimaryAccount) setSaPrimaryAccount(phones[0]);
        setSaWorkerAccounts(phones);
        setInviterAccounts(phones);
      }
      // Fetch real details for each account (non-blocking)
      fetchAllAccountDetails(phones);
    } catch (err) { console.error(err); }
  };

  const fetchAllAccountDetails = async (phones) => {
    const loadingMap = {};
    phones.forEach(p => { loadingMap[p] = { status: 'checking' }; });
    setAccountDetails(prev => ({ ...prev, ...loadingMap }));

    for (const phone of phones) {
      try {
        const res = await axios.post(`${API_BASE}/accounts/details/${phone}`);
        const d = res.data;
        setAccountDetails(prev => ({
          ...prev,
          [phone]: {
            status:          d.status === 'authorized'  ? 'authorized'
                           : d.status === 'restricted'  ? 'restricted'
                           : 'expired',
            name:            d.name            || '',
            username:        d.username         || '',
            premium:         d.premium          || false,
            groups_count:    d.groups_count     || 0,
            channels_count:  d.channels_count   || 0,
            pms_count:       d.pms_count        || 0,
            is_restricted:   d.is_restricted    || false,
            restrict_reason: d.restrict_reason  || '',
          }
        }));
      } catch {
        setAccountDetails(prev => ({ ...prev, [phone]: { status: 'error' } }));
      }
    }
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
      const payload = { phone: loginPhone, code: loginCode };
      if (loginStep === 2) payload.password = loginPassword;
      
      const res = await axios.post(`${API_BASE}/accounts/login/confirm`, payload);
      
      if (res.data.status === 'password_required') {
        setLoginStep(2);
        setLoading(false);
        return;
      }
      
      setLoginStep(0); setLoginPhone(''); setLoginCode(''); setLoginPassword('');
      fetchAccounts(); setActiveTab('Dashboard');
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Invalid code or password'); }
    setLoading(false);
  };

  const handleTDataUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/accounts/upload-tdata-zip`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchAccounts();
      setActiveTab('Dashboard');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload tdata');
    }
    setLoading(false);
    e.target.value = ''; // reset input
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg(''); setScrapeResult(null); setScrapeCacheId(null);
    try {
      const res = await axios.post(`${API_BASE}/scraper/scrape`, {
        account: scrapeAccount,
        group_url: scrapeGroup,
        filter_has_username: filterHasUsername,
        filter_has_phone: filterHasPhone,
        filter_no_bots: filterNoBots,
        filter_active_recently: filterActiveRecently,
        filter_has_name: filterHasName,
      });
      const { count, total_seen, filtered_out } = res.data;
      setScrapeResult(
        `✅ Scraped ${count} members` +
        (filtered_out > 0 ? ` (${filtered_out} filtered out of ${total_seen} total)` : ` out of ${total_seen} total`)
      );
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
      if (saWorkerAccounts.length === 0) throw new Error('Select at least one worker account');
      if (!saPrimaryAccount) throw new Error('Please select a primary account to scrape with');
      await axios.post(`${API_BASE}/inviter/invite-group`, {
        accounts: saWorkerAccounts,
        primary_account: saPrimaryAccount,
        source_group: saSourceGroup,
        target_group: saTargetGroup,
        delay: parseFloat(saDelay)
      });
      setActiveTab('Terminal Logs');
    } catch (err) { setErrorMsg(err.response?.data?.detail || err.message || 'Scrape & Add failed'); }
    setLoading(false);
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!csvFile) { setErrorMsg('Please upload a CSV file'); return; }
    if (inviterAccounts.length === 0) { setErrorMsg('Select at least one account'); return; }
    setLoading(true); setErrorMsg('');
    try {
      const formData = new FormData();
      formData.append('target_group', inviteGroup);
      formData.append('accounts', JSON.stringify(inviterAccounts));
      formData.append('delay', parseFloat(inviterDelay));
      formData.append('file', csvFile);
      await axios.post(`${API_BASE}/inviter/invite-csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setActiveTab('Terminal Logs');
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Inviter failed'); }
    setLoading(false);
 };

  const handleInviteByUsername = async (e) => {
    e.preventDefault();
    if (inviterAccounts.length === 0) { setErrorMsg('Select at least one account'); return; }
    const lines = usernameInput.split(/[\n,]+/).map(u => u.trim()).filter(Boolean);
    if (lines.length === 0) { setErrorMsg('Please enter at least one username'); return; }
    setLoading(true); setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/inviter/invite-by-username`, {
        accounts: inviterAccounts,
        target_group: inviteGroup,
        usernames: lines,
        delay: parseFloat(inviterDelay),
      });
      setActiveTab('Terminal Logs');
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Invite by username failed'); }
    setLoading(false);
  };

  // Scrape & Add account toggles
  const handleSaToggleAll = (checked) => {
    setSaWorkerSelectAll(checked);
    setSaWorkerAccounts(checked ? accounts.map(a => a.phone) : []);
  };
  const handleSaToggleAccount = (phone, checked) => {
    setSaWorkerAccounts(prev => checked ? [...prev, phone] : prev.filter(p => p !== phone));
  };

  // Inviter account toggles
  const handleInviterToggleAll = (checked) => {
    setInviterSelectAll(checked);
    setInviterAccounts(checked ? accounts.map(a => a.phone) : []);
  };
  const handleInviterToggleAccount = (phone, checked) => {
    setInviterAccounts(prev => checked ? [...prev, phone] : prev.filter(p => p !== phone));
  };

  // Join Group account toggles
  const handleJoinToggleAll = (checked) => {
    setJoinSelectAll(checked);
    setJoinAccounts(checked ? accounts.map(a => a.phone) : []);
  };
  const handleJoinToggleAccount = (phone, checked) => {
    setJoinAccounts(prev => checked ? [...prev, phone] : prev.filter(p => p !== phone));
  };

  const handleJoinGroup = async (e) => {
    e.preventDefault();
    if (joinAccounts.length === 0) { setErrorMsg('Select at least one account'); return; }
    if (!joinGroupTarget) { setErrorMsg('Enter target group or channel'); return; }
    setLoading(true); setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/join-group`, {
        accounts: joinAccounts,
        target_group: joinGroupTarget,
        delay: parseFloat(joinDelay)
      });
      setActiveTab('Terminal Logs');
    } catch (err) { setErrorMsg(err.response?.data?.detail || 'Join group failed'); }
    setLoading(false);
  };

  const handleStopTasks = async () => {
    try {
      await axios.post(`${API_BASE}/inviter/stop`);
      axios.post(`${API_BASE}/logs/clear`); // Optionally clear logs or not
    } catch (err) {
      setErrorMsg('Failed to send stop signal.');
    }
  };

  const handleWarmStart = async (e) => {
    e.preventDefault();
    setLoading(true); setErrorMsg('');
    try {
      if (warmAccounts.length === 0) throw new Error('Select at least one account to warm');
      await axios.post(`${API_BASE}/warm/start`, {
        accounts: warmAccounts,
        do_react: warmDoReact,
        do_chat: warmDoChat,
        reactions_per_group: parseInt(warmReactionsPerGroup),
        messages_to_send: parseInt(warmMessagesToSend),
        react_delay: parseFloat(warmReactDelay),
        chat_delay: parseFloat(warmChatDelay),
      });
      setActiveTab('Terminal Logs');
    } catch (err) { setErrorMsg(err.response?.data?.detail || err.message || 'Warm failed'); }
    setLoading(false);
  };

  const handleWarmToggleAll = (checked) => {
    setWarmSelectAll(checked);
    setWarmAccounts(checked ? accounts.map(a => a.phone) : []);
  };

  const handleWarmToggleAccount = (phone, checked) => {
    setWarmAccounts(prev =>
      checked ? [...prev, phone] : prev.filter(p => p !== phone)
    );
  };

  return (
    <div className="app-container">
      <aside className="sidebar glass-panel" style={{ borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none' }}>
        <div className="sidebar-logo">
          <Send size={28} strokeWidth={2.5} /> TeleMaster
        </div>
        <nav>
          {['Dashboard', 'Add Account', 'Make Account Strong', 'Scraper', 'Join Group', 'Scrape & Add', 'Inviter', 'Terminal Logs'].map((item) => (
            <div 
              key={item} 
              className={`nav-item ${activeTab === item ? 'active' : ''}`}
              onClick={() => { setActiveTab(item); setErrorMsg(''); }}
            >
              {item === 'Dashboard' && <Activity size={20} />}
              {item === 'Add Account' && <Plus size={20} />}
              {item === 'Make Account Strong' && <Flame size={20} />}
              {item === 'Scraper' && <Database size={20} />}
              {item === 'Join Group' && <Users size={20} />}
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
            <button
              title="Logout / Deactivate License"
              onClick={() => {
                if (window.confirm('Log out and deactivate this device?')) {
                  localStorage.removeItem('tg_license_key');
                  onLogout();
                }
              }}
              style={{
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: '8px', padding: '7px 10px', cursor: 'pointer',
                color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '5px',
                fontSize: '0.78rem', fontWeight: 600, transition: 'all 0.2s'
              }}
            >
              <LogOut size={15} /> Logout
            </button>
            <div className="avatar">TM</div>
          </div>
        </header>

        {activeTab === 'Dashboard' && (() => {
          const authorizedCount  = Object.values(accountDetails).filter(d => d.status === 'authorized').length;
          const restrictedCount  = Object.values(accountDetails).filter(d => d.status === 'restricted').length;
          const expiredCount     = Object.values(accountDetails).filter(d => d.status === 'expired').length;
          const checkingCount    = Object.values(accountDetails).filter(d => d.status === 'checking').length;
          const healthStatus = accounts.length === 0 ? 'No accounts'
            : restrictedCount > 0   ? '🚫 Restricted'
            : expiredCount > 0      ? '⚠ Check'
            : authorizedCount === accounts.length ? '✓ All OK'
            : 'Scanning...';
          const healthColor = restrictedCount > 0 ? '#f97316'
            : expiredCount > 0      ? '#f59e0b'
            : authorizedCount === accounts.length && accounts.length > 0 ? '#10b981'
            : 'var(--text-primary)';
          return (
          <div className="animate-fade-in">
            {/* ── Stat Cards ── */}
            <div className="stats-grid">
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>Total Accounts</span><div className="stat-icon blue"><Users /></div>
                </div>
                <div className="stat-value">{accounts.length}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {authorizedCount} active
                  {restrictedCount > 0 && <span style={{ color: '#f97316', marginLeft: '6px' }}>· {restrictedCount} restricted</span>}
                  {expiredCount > 0 && <span style={{ color: '#f59e0b', marginLeft: '6px' }}>· {expiredCount} expired</span>}
                </div>
              </div>
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>System Health</span><div className="stat-icon green"><Activity /></div>
                </div>
                <div className="stat-value" style={{ color: healthColor }}>{healthStatus}</div>
              </div>
              <div className="stat-card glass-panel">
                <div className="stat-header">
                  <span>Pending Logs</span><div className="stat-icon purple"><Terminal /></div>
                </div>
                <div className="stat-value" onClick={() => setActiveTab('Terminal Logs')} style={{cursor: 'pointer'}}>{logs.length}</div>
              </div>
            </div>

            {/* ── Account Cards ── */}
            <div className="data-table-container glass-panel">
              <div className="table-header">
                <h2>Managed Telegram Accounts</h2>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  {checkingCount > 0 && (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      ⏳ Checking {checkingCount} account{checkingCount > 1 ? 's' : ''}...
                    </span>
                  )}
                  <button className="glass-button" onClick={() => {
                    fetchAllAccountDetails(accounts.map(a => a.phone));
                  }} style={{ padding: '6px 14px', fontSize: '0.82rem' }}>↺ Refresh</button>
                  <button className="glass-button" onClick={() => setActiveTab('Add Account')}>+ Add New</button>
                </div>
              </div>

              {accounts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📱</div>
                  <div style={{ fontWeight: 600, marginBottom: '6px' }}>No accounts found</div>
                  <div style={{ fontSize: '0.85rem' }}>Add a Telegram account to get started.</div>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px', padding: '4px 0' }}>
                  {accounts.map((acc) => {
                    const d = accountDetails[acc.phone];
                    const isAuth       = d?.status === 'authorized';
                    const isRestricted = d?.status === 'restricted';
                    const isExpired    = d?.status === 'expired';
                    const isError      = d?.status === 'error';
                    const isCheck      = !d || d?.status === 'checking';

                    // Color theme per status
                    const cardBg     = isAuth       ? 'rgba(16,185,129,0.07)'
                                     : isRestricted ? 'rgba(249,115,22,0.07)'
                                     : isExpired    ? 'rgba(245,158,11,0.07)'
                                     : isError      ? 'rgba(239,68,68,0.07)'
                                     : 'rgba(255,255,255,0.04)';
                    const cardBorder = isAuth       ? '1px solid rgba(16,185,129,0.25)'
                                     : isRestricted ? '1px solid rgba(249,115,22,0.35)'
                                     : isExpired    ? '1px solid rgba(245,158,11,0.25)'
                                     : isError      ? '1px solid rgba(239,68,68,0.25)'
                                     : '1px solid rgba(255,255,255,0.08)';
                    const stripGrad  = isAuth       ? 'linear-gradient(90deg,#10b981,#059669)'
                                     : isRestricted ? 'linear-gradient(90deg,#f97316,#ea580c)'
                                     : isExpired    ? 'linear-gradient(90deg,#f59e0b,#d97706)'
                                     : isError      ? 'linear-gradient(90deg,#ef4444,#dc2626)'
                                     : 'rgba(255,255,255,0.1)';
                    const avatarBg   = isAuth       ? 'linear-gradient(135deg,#10b981,#059669)'
                                     : isRestricted ? 'linear-gradient(135deg,#f97316,#ea580c)'
                                     : isExpired    ? 'linear-gradient(135deg,#f59e0b,#d97706)'
                                     : 'rgba(255,255,255,0.1)';
                    const badgeBg    = isAuth       ? 'rgba(16,185,129,0.2)'
                                     : isRestricted ? 'rgba(249,115,22,0.2)'
                                     : isExpired    ? 'rgba(245,158,11,0.2)'
                                     : isError      ? 'rgba(239,68,68,0.2)'
                                     : 'rgba(255,255,255,0.08)';
                    const badgeColor = isAuth       ? '#6ee7b7'
                                     : isRestricted ? '#fdba74'
                                     : isExpired    ? '#fcd34d'
                                     : isError      ? '#fca5a5'
                                     : 'var(--text-secondary)';
                    const badgeBorder= isAuth       ? '1px solid rgba(16,185,129,0.3)'
                                     : isRestricted ? '1px solid rgba(249,115,22,0.4)'
                                     : isExpired    ? '1px solid rgba(245,158,11,0.3)'
                                     : isError      ? '1px solid rgba(239,68,68,0.3)'
                                     : '1px solid rgba(255,255,255,0.08)';
                    const badgeLabel = isCheck ? '⏳ Checking'
                                     : isAuth       ? '● Active'
                                     : isRestricted ? '🚫 Restricted'
                                     : isExpired    ? '⚠ Expired'
                                     : '✕ Error';

                    return (
                      <div key={acc.id} style={{
                        padding: '18px 20px', borderRadius: '14px',
                        background: cardBg, border: cardBorder,
                        transition: 'all 0.2s', position: 'relative', overflow: 'hidden'
                      }}>
                        {/* Glow strip */}
                        <div style={{
                          position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
                          background: stripGrad
                        }} />

                        {/* Header row */}
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            {/* Avatar */}
                            <div style={{
                              width: '42px', height: '42px', borderRadius: '50%',
                              background: avatarBg,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '1.1rem', fontWeight: 700, color: '#fff', flexShrink: 0
                            }}>
                              {d?.name ? d.name[0].toUpperCase() : '?'}
                            </div>
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {isCheck ? (
                                  <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic', fontSize: '0.85rem' }}>Checking...</span>
                                ) : (
                                  <>{d?.name || acc.phone}
                                    {d?.premium && (
                                      <span style={{
                                        background: 'linear-gradient(135deg,#a855f7,#7c3aed)',
                                        color: '#fff', fontSize: '0.65rem', padding: '1px 6px',
                                        borderRadius: '8px', fontWeight: 700, letterSpacing: '0.04em'
                                      }}>✦ PREMIUM</span>
                                    )}
                                  </>
                                )}
                              </div>
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '1px' }}>
                                {d?.username && d.username !== 'None' ? d.username + ' · ' : ''}
                                <span style={{ fontFamily: 'monospace' }}>+{acc.phone}</span>
                              </div>
                            </div>
                          </div>

                          {/* Status badge */}
                          <div style={{
                            padding: '3px 10px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700,
                            letterSpacing: '0.04em', flexShrink: 0,
                            background: badgeBg, color: badgeColor, border: badgeBorder
                          }}>
                            {badgeLabel}
                          </div>
                        </div>

                        {/* Stats row — only for active/restricted */}
                        {(isAuth || isRestricted) && d && (
                          <div style={{
                            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
                            gap: '8px', marginBottom: '14px'
                          }}>
                            {[
                              { icon: '👥', label: 'Groups',   val: d.groups_count },
                              { icon: '📢', label: 'Channels', val: d.channels_count },
                              { icon: '💬', label: 'DMs',      val: d.pms_count },
                            ].map(({ icon, label, val }) => (
                              <div key={label} style={{
                                textAlign: 'center', padding: '8px 4px', borderRadius: '8px',
                                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)'
                              }}>
                                <div style={{ fontSize: '0.95rem' }}>{icon}</div>
                                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>{val ?? '—'}</div>
                                <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '1px' }}>{label}</div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Restriction warning banner */}
                        {isRestricted && (
                          <div style={{
                            fontSize: '0.78rem', marginBottom: '12px', padding: '9px 12px',
                            background: 'rgba(249,115,22,0.12)', borderRadius: '8px',
                            border: '1px solid rgba(249,115,22,0.3)',
                            borderLeft: '3px solid #f97316'
                          }}>
                            <div style={{ fontWeight: 700, color: '#fdba74', marginBottom: '3px' }}>🚫 Account Restricted by Telegram</div>
                            {d?.restrict_reason && (
                              <div style={{ color: 'rgba(253,186,116,0.8)', fontSize: '0.73rem', lineHeight: 1.4 }}>
                                {d.restrict_reason}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Expired warning */}
                        {isExpired && (
                          <div style={{ fontSize: '0.78rem', color: '#fcd34d', marginBottom: '12px', padding: '7px 10px', background: 'rgba(245,158,11,0.1)', borderRadius: '6px' }}>
                            ⚠️ Session expired — re-login to restore this account.
                          </div>
                        )}

                        {/* Action buttons */}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          {isRestricted && (
                            <button style={{
                              flex: 1, padding: '6px 10px', borderRadius: '7px', fontSize: '0.78rem',
                              border: '1px solid rgba(249,115,22,0.4)', background: 'rgba(249,115,22,0.1)',
                              color: '#fdba74', cursor: 'default', fontWeight: 600
                            }} disabled>🚫 Restricted — limited functions</button>
                          )}
                          {isExpired && (
                            <button onClick={() => setActiveTab('Add Account')} style={{
                              flex: 1, padding: '6px 10px', borderRadius: '7px', fontSize: '0.78rem',
                              border: '1px solid rgba(245,158,11,0.4)', background: 'rgba(245,158,11,0.12)',
                              color: '#fcd34d', cursor: 'pointer', fontWeight: 600
                            }}>🔑 Re-login</button>
                          )}
                          <button onClick={async () => {
                            if (!window.confirm(`Delete account ${acc.phone}?`)) return;
                            await axios.post(`${API_BASE}/accounts/delete/${acc.phone}`);
                            fetchAccounts();
                          }} style={{
                            padding: '6px 12px', borderRadius: '7px', fontSize: '0.78rem',
                            border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.08)',
                            color: '#fca5a5', cursor: 'pointer', fontWeight: 600,
                            marginLeft: (isExpired || isRestricted) ? '0' : 'auto'
                          }}>🗑 Delete</button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
          );
        })()}


        {activeTab === 'Add Account' && (
          <div className="animate-fade-in">
            <div className="glass-panel" style={{ padding: '30px', maxWidth: '500px', margin: '0 auto' }}>
              <h2 style={{ marginBottom: '20px' }}>Login New Account</h2>
              {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}
              {loginStep === 0 && (
                <form onSubmit={handleRequestCode}>
                  <div className="form-group">
                    <label className="form-label">Phone Number (with +)</label>
                    <input type="text" className="glass-input" placeholder="+1234567890" value={loginPhone} onChange={(e) => setLoginPhone(e.target.value)} required />
                  </div>
                  <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading}>{loading ? 'Requesting...' : 'Request Code'}</button>
                </form>
              )}
              {loginStep === 1 && (
                <form onSubmit={handleConfirmLogin}>
                  <div className="form-group">
                    <label className="form-label">Login Code sent to {loginPhone}</label>
                    <input type="text" className="glass-input" placeholder="12345" value={loginCode} onChange={(e) => setLoginCode(e.target.value)} required />
                  </div>
                  <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading}>{loading ? 'Verifying...' : 'Verify & Login'}</button>
                </form>
              )}
              {loginStep === 2 && (
                <form onSubmit={handleConfirmLogin}>
                  <div className="form-group">
                    <label className="form-label">Two-Step Verification (2FA) Password</label>
                    <input type="password" className="glass-input" placeholder="Enter your 2FA password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} required />
                  </div>
                  <button type="submit" className="glass-button" style={{ width: '100%' }} disabled={loading}>{loading ? 'Logging in...' : 'Submit Password'}</button>
                </form>
              )}

              <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '15px' }}>Or Upload TData (.zip)</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '15px' }}>
                  Compress your Telegram Desktop <code>tdata</code> folder into a .zip file and upload it here to login automatically without a code.
                </p>
                <div style={{ position: 'relative' }}>
                  <input 
                    type="file" 
                    accept=".zip"
                    onChange={handleTDataUpload}
                    style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
                    disabled={loading}
                  />
                  <button type="button" className="glass-button secondary" style={{ width: '100%', pointerEvents: 'none' }}>
                    {loading ? 'Uploading & Processing...' : '📁 Select tdata .zip'}
                  </button>
                </div>
              </div>
            </div>

          </div>
        )}

        {activeTab === 'Make Account Strong' && (
          <div className="animate-fade-in">
            <div className="glass-panel" style={{ padding: '30px', maxWidth: '600px', margin: '0 auto' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                <Flame size={28} color="#f97316" />
                <h2 style={{ margin: 0 }}>Make Account Strong</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '24px' }}>
                Warm up your Telegram accounts by auto-reacting to group posts and sending friendly messages to contacts — making them look active and trustworthy.
              </p>
              {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}

              <form onSubmit={handleWarmStart}>
                {/* Account Selection */}
                <div className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label className="form-label" style={{ margin: 0 }}>Select Accounts to Warm</label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={warmSelectAll}
                        onChange={e => handleWarmToggleAll(e.target.checked)}
                        style={{ accentColor: '#f97316' }}
                      />
                      Select All
                    </label>
                  </div>
                  {accounts.length === 0 ? (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', textAlign: 'center', padding: '12px 0' }}>No accounts found. Add one first.</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto', padding: '4px 0' }}>
                      {accounts.map(acc => (
                        <label key={acc.id} style={{
                          display: 'flex', alignItems: 'center', gap: '10px',
                          padding: '10px 14px', borderRadius: '8px',
                          background: warmAccounts.includes(acc.phone) ? 'rgba(249,115,22,0.12)' : 'rgba(255,255,255,0.04)',
                          border: warmAccounts.includes(acc.phone) ? '1px solid rgba(249,115,22,0.4)' : '1px solid rgba(255,255,255,0.08)',
                          cursor: 'pointer', transition: 'all 0.2s'
                        }}>
                          <input
                            type="checkbox"
                            checked={warmAccounts.includes(acc.phone)}
                            onChange={e => handleWarmToggleAccount(acc.phone, e.target.checked)}
                            style={{ accentColor: '#f97316' }}
                          />
                          <span style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{acc.phone}</span>
                          <span className="status-badge active" style={{ marginLeft: 'auto', fontSize: '0.75rem' }}>Active</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="form-group">
                  <label className="form-label">Warm Actions</label>
                  <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                    <label style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '12px 18px', borderRadius: '10px', cursor: 'pointer',
                      background: warmDoReact ? 'rgba(249,115,22,0.15)' : 'rgba(255,255,255,0.05)',
                      border: warmDoReact ? '1px solid rgba(249,115,22,0.5)' : '1px solid rgba(255,255,255,0.1)',
                      transition: 'all 0.2s', flex: 1, minWidth: '140px'
                    }}>
                      <input type="checkbox" checked={warmDoReact} onChange={e => setWarmDoReact(e.target.checked)} style={{ accentColor: '#f97316' }} />
                      <span>⚡ Auto React</span>
                    </label>
                    <label style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '12px 18px', borderRadius: '10px', cursor: 'pointer',
                      background: warmDoChat ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.05)',
                      border: warmDoChat ? '1px solid rgba(99,102,241,0.5)' : '1px solid rgba(255,255,255,0.1)',
                      transition: 'all 0.2s', flex: 1, minWidth: '140px'
                    }}>
                      <input type="checkbox" checked={warmDoChat} onChange={e => setWarmDoChat(e.target.checked)} style={{ accentColor: '#6366f1' }} />
                      <span>💬 Auto Chat</span>
                    </label>
                  </div>
                </div>

                {/* Settings */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {warmDoReact && (
                    <>
                      <div className="form-group">
                        <label className="form-label">Reactions per Group</label>
                        <input type="number" min="1" max="20" className="glass-input" value={warmReactionsPerGroup} onChange={e => setWarmReactionsPerGroup(e.target.value)} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Delay between Reactions (s)</label>
                        <input type="number" min="1" step="0.5" className="glass-input" value={warmReactDelay} onChange={e => setWarmReactDelay(e.target.value)} />
                      </div>
                    </>
                  )}
                  {warmDoChat && (
                    <>
                      <div className="form-group">
                        <label className="form-label">Messages to Send</label>
                        <input type="number" min="1" max="20" className="glass-input" value={warmMessagesToSend} onChange={e => setWarmMessagesToSend(e.target.value)} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Delay between Messages (s)</label>
                        <input type="number" min="1" step="0.5" className="glass-input" value={warmChatDelay} onChange={e => setWarmChatDelay(e.target.value)} />
                      </div>
                    </>
                  )}
                </div>

                <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginBottom: '20px', padding: '12px', background: 'rgba(249,115,22,0.07)', borderRadius: '8px', borderLeft: '3px solid #f97316' }}>
                  🔥 Warming runs in the background. Watch progress in <b>Terminal Logs</b>. It will react to random group posts and send friendly messages to contacts to simulate human-like activity.
                </p>

                <button
                  type="submit"
                  className="glass-button"
                  style={{ width: '100%', background: 'linear-gradient(135deg, rgba(249,115,22,0.3), rgba(234,88,12,0.2))', borderColor: 'rgba(249,115,22,0.5)' }}
                  disabled={loading || accounts.length === 0 || warmAccounts.length === 0}
                >
                  {loading ? '🔥 Starting Warm Session...' : `🔥 Start Warming ${warmAccounts.length} Account(s)`}
                </button>
              </form>
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

              {/* ── Filter Panel ── */}
              <div style={{ marginBottom: '20px' }}>
                <button type="button" onClick={() => setScrapeShowFilters(v => !v)} style={{
                  width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.12)',
                  background: scrapeShowFilters ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.05)',
                  color: scrapeShowFilters ? '#a5b4fc' : 'var(--text-secondary)',
                  cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  transition: 'all 0.2s'
                }}>
                  <span>⚙️ Filters
                    {[filterHasUsername, filterHasPhone, !filterNoBots, filterActiveRecently, filterHasName].filter(Boolean).length > 0 && (
                      <span style={{
                        marginLeft: '8px', background: '#6366f1', color: '#fff',
                        borderRadius: '10px', padding: '1px 7px', fontSize: '0.75rem'
                      }}>
                        {[filterHasUsername, filterHasPhone, !filterNoBots, filterActiveRecently, filterHasName].filter(Boolean).length} active
                      </span>
                    )}
                  </span>
                  <span style={{ fontSize: '0.75rem' }}>{scrapeShowFilters ? '▲ Hide' : '▼ Show'}</span>
                </button>

                {scrapeShowFilters && (
                  <div style={{
                    marginTop: '8px', padding: '16px', borderRadius: '8px',
                    background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)'
                  }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px', margin: '0 0 14px 0' }}>
                      Only scrape members matching ALL selected conditions:
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                      {[
                        { label: '🚫 Exclude Bots',       value: filterNoBots,          setter: setFilterNoBots,          desc: 'Skip bot accounts' },
                        { label: '@ Has Username',         value: filterHasUsername,     setter: setFilterHasUsername,     desc: 'Must have @username' },
                        { label: '📞 Has Phone Number',   value: filterHasPhone,        setter: setFilterHasPhone,        desc: 'Phone visible to you' },
                        { label: '⚡ Active Recently',     value: filterActiveRecently,  setter: setFilterActiveRecently,  desc: 'Online / last week' },
                        { label: '👤 Has Real Name',      value: filterHasName,         setter: setFilterHasName,         desc: 'Has a first name set' },
                      ].map(({ label, value, setter, desc }) => (
                        <label key={label} onClick={() => setter(v => !v)} style={{
                          display: 'flex', alignItems: 'flex-start', gap: '10px',
                          padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
                          background: value ? 'rgba(99,102,241,0.18)' : 'rgba(255,255,255,0.04)',
                          border: value ? '1px solid rgba(99,102,241,0.5)' : '1px solid rgba(255,255,255,0.08)',
                          transition: 'all 0.15s', userSelect: 'none'
                        }}>
                          <div style={{
                            width: '18px', height: '18px', borderRadius: '4px', flexShrink: 0, marginTop: '1px',
                            border: value ? '2px solid #6366f1' : '2px solid rgba(255,255,255,0.2)',
                            background: value ? '#6366f1' : 'transparent',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            transition: 'all 0.15s'
                          }}>
                            {value && <span style={{ color: '#fff', fontSize: '11px', lineHeight: 1 }}>✓</span>}
                          </div>
                          <div>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: value ? '#a5b4fc' : 'var(--text-primary)' }}>{label}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>

                    <button type="button" onClick={() => {
                      setFilterHasUsername(false); setFilterHasPhone(false);
                      setFilterNoBots(true); setFilterActiveRecently(false); setFilterHasName(false);
                    }} style={{
                      marginTop: '12px', width: '100%', padding: '7px', borderRadius: '6px',
                      background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                      color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8rem'
                    }}>↺ Reset to defaults</button>
                  </div>
                )}
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

        {activeTab === 'Join Group' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '680px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '6px' }}>Mass Join Group/Channel</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '24px' }}>
              Make multiple accounts join a specific public or private group/channel.
            </p>
            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}

            <form onSubmit={handleJoinGroup}>
              <div className="form-group">
                <label className="form-label">Target Group or Channel</label>
                <input 
                  type="text" className="glass-input" 
                  placeholder="@username or https://t.me/joinchat/..." 
                  value={joinGroupTarget} onChange={(e) => setJoinGroupTarget(e.target.value)} required 
                />
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <label className="form-label" style={{ margin: 0 }}>Select Accounts to Join</label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={joinSelectAll} onChange={(e) => handleJoinToggleAll(e.target.checked)} />
                    Select All
                  </label>
                </div>
                <div className="accounts-list-scrollable" style={{ maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  {accounts.map(a => (
                    <label key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '6px', cursor: 'pointer', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <input type="checkbox" checked={joinAccounts.includes(a.phone)} onChange={(e) => handleJoinToggleAccount(a.phone, e.target.checked)} />
                      <span>{a.phone}</span>
                    </label>
                  ))}
                  {accounts.length === 0 && <div style={{ fontSize: '0.85rem', color: 'gray' }}>No accounts available</div>}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Delay between each account join (seconds)</label>
                <input type="number" min="1" step="1" className="glass-input" value={joinDelay} onChange={(e) => setJoinDelay(e.target.value)} required />
              </div>

              <button type="submit" className="glass-button" style={{ width: '100%', marginTop: '10px' }} disabled={loading || joinAccounts.length === 0}>
                {loading ? 'Starting...' : 'Start Joining'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'Scrape & Add' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '680px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '6px' }}>Scrape & Add (Group to Group)</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '24px' }}>
              Scrapes members from a source group and adds them to your target group using <b>all selected accounts</b> in parallel — no terminal needed.
            </p>
            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}

            <form onSubmit={handleScrapeAndAdd}>
              {/* Groups */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Source Group (Scrape From)</label>
                  <input type="text" className="glass-input" placeholder="https://t.me/source_group" value={saSourceGroup} onChange={e => setSaSourceGroup(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Target Group (Add To)</label>
                  <input type="text" className="glass-input" placeholder="https://t.me/target_group" value={saTargetGroup} onChange={e => setSaTargetGroup(e.target.value)} required />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Primary Account (Scraper)</label>
                  <select className="glass-input" value={saPrimaryAccount} onChange={e => setSaPrimaryAccount(e.target.value)} required>
                    <option value="" disabled>Select account</option>
                    {accounts.map(a => <option key={a.id} value={a.phone}>{a.phone}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Delay Between Adds (s)</label>
                  <input type="number" step="0.5" min="1" className="glass-input" value={saDelay} onChange={e => setSaDelay(e.target.value)} required />
                </div>
              </div>

              {/* Account Multi-Select */}
              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <label className="form-label" style={{ margin: 0 }}>Worker Accounts (Add Members)</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{
                      background: saWorkerAccounts.length > 0 ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(99,102,241,0.4)', borderRadius: '20px',
                      padding: '2px 10px', fontSize: '0.8rem', color: '#a5b4fc', fontWeight: 600
                    }}>
                      {saWorkerAccounts.length} / {accounts.length} selected
                    </span>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                      <input type="checkbox" checked={saWorkerSelectAll}
                        onChange={e => handleSaToggleAll(e.target.checked)}
                        style={{ accentColor: '#6366f1' }} />
                      All
                    </label>
                  </div>
                </div>
                {accounts.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', textAlign: 'center', padding: '12px 0' }}>No accounts found. Add one first.</p>
                ) : (
                  <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: '8px', maxHeight: '200px', overflowY: 'auto', padding: '4px 2px'
                  }}>
                    {accounts.map(acc => (
                      <label key={acc.id} style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                        background: saWorkerAccounts.includes(acc.phone) ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.04)',
                        border: saWorkerAccounts.includes(acc.phone) ? '1px solid rgba(99,102,241,0.4)' : '1px solid rgba(255,255,255,0.08)',
                        transition: 'all 0.15s', fontSize: '0.85rem'
                      }}>
                        <input type="checkbox"
                          checked={saWorkerAccounts.includes(acc.phone)}
                          onChange={e => handleSaToggleAccount(acc.phone, e.target.checked)}
                          style={{ accentColor: '#6366f1', flexShrink: 0 }} />
                        <span style={{ fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{acc.phone}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginBottom: '20px', padding: '12px', background: 'rgba(99,102,241,0.07)', borderRadius: '8px', borderLeft: '3px solid #6366f1' }}>
                🤖 All <b>{saWorkerAccounts.length}</b> selected accounts will share the workload automatically — <b>no extra terminals needed</b>. Watch progress in Terminal Logs.
              </div>

              <button type="submit" className="glass-button" style={{ width: '100%' }}
                disabled={loading || saWorkerAccounts.length === 0}>
                {loading ? '⏳ Starting...' : `🚀 Start Scrape & Add with ${saWorkerAccounts.length} Account(s)`}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'Inviter' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '30px', maxWidth: '680px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '6px' }}>Mass Inviter</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '20px' }}>
              Add members to your group using <b>all selected accounts</b> — choose your preferred mode below.
            </p>

            {/* Mode Toggle */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
              <button type="button" onClick={() => setInviterMode('csv')} style={{
                flex: 1, padding: '10px 0', borderRadius: '8px', border: 'none', cursor: 'pointer',
                fontWeight: 600, fontSize: '0.9rem', transition: 'all 0.2s',
                background: inviterMode === 'csv' ? 'linear-gradient(135deg,#10b981,#059669)' : 'rgba(255,255,255,0.06)',
                color: inviterMode === 'csv' ? '#fff' : 'var(--text-secondary)',
                boxShadow: inviterMode === 'csv' ? '0 2px 12px rgba(16,185,129,0.35)' : 'none',
              }}>📋 From CSV</button>
              <button type="button" onClick={() => setInviterMode('username')} style={{
                flex: 1, padding: '10px 0', borderRadius: '8px', border: 'none', cursor: 'pointer',
                fontWeight: 600, fontSize: '0.9rem', transition: 'all 0.2s',
                background: inviterMode === 'username' ? 'linear-gradient(135deg,#6366f1,#4f46e5)' : 'rgba(255,255,255,0.06)',
                color: inviterMode === 'username' ? '#fff' : 'var(--text-secondary)',
                boxShadow: inviterMode === 'username' ? '0 2px 12px rgba(99,102,241,0.35)' : 'none',
              }}>👤 By Username</button>
            </div>

            {errorMsg && <div style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>{errorMsg}</div>}

            {/* ─── CSV Mode ─── */}
            {inviterMode === 'csv' && (
              <form onSubmit={handleInvite}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Upload Users CSV</label>
                    <input type="file" accept=".csv" className="glass-input" onChange={e => setCsvFile(e.target.files[0])} required style={{ padding: '10px' }} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Delay Between Invites (s)</label>
                    <input type="number" min="1" step="0.5" className="glass-input" value={inviterDelay} onChange={e => setInviterDelay(e.target.value)} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Target Group to Invite Users To</label>
                  <input type="text" className="glass-input" placeholder="https://t.me/your_group" value={inviteGroup} onChange={e => setInviteGroup(e.target.value)} required />
                </div>

                {/* Account Multi-Select */}
                <div className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label className="form-label" style={{ margin: 0 }}>Select Worker Accounts</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{
                        background: inviterAccounts.length > 0 ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(16,185,129,0.4)', borderRadius: '20px',
                        padding: '2px 10px', fontSize: '0.8rem', color: '#6ee7b7', fontWeight: 600
                      }}>
                        {inviterAccounts.length} / {accounts.length} selected
                      </span>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <input type="checkbox" checked={inviterSelectAll}
                          onChange={e => handleInviterToggleAll(e.target.checked)}
                          style={{ accentColor: '#10b981' }} />
                        All
                      </label>
                    </div>
                  </div>
                  {accounts.length === 0 ? (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', textAlign: 'center', padding: '12px 0' }}>No accounts found. Add one first.</p>
                  ) : (
                    <div style={{
                      display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                      gap: '8px', maxHeight: '200px', overflowY: 'auto', padding: '4px 2px'
                    }}>
                      {accounts.map(acc => (
                        <label key={acc.id} style={{
                          display: 'flex', alignItems: 'center', gap: '8px',
                          padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                          background: inviterAccounts.includes(acc.phone) ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                          border: inviterAccounts.includes(acc.phone) ? '1px solid rgba(16,185,129,0.4)' : '1px solid rgba(255,255,255,0.08)',
                          transition: 'all 0.15s', fontSize: '0.85rem'
                        }}>
                          <input type="checkbox"
                            checked={inviterAccounts.includes(acc.phone)}
                            onChange={e => handleInviterToggleAccount(acc.phone, e.target.checked)}
                            style={{ accentColor: '#10b981', flexShrink: 0 }} />
                          <span style={{ fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{acc.phone}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginBottom: '20px', padding: '12px', background: 'rgba(16,185,129,0.07)', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
                  📋 The CSV member list will be split evenly across <b>{inviterAccounts.length}</b> selected account(s) — <b>one UI, zero terminals</b>.
                </div>

                <button type="submit" className="glass-button" style={{ width: '100%' }}
                  disabled={loading || inviterAccounts.length === 0}>
                  {loading ? '⏳ Starting...' : `🚀 Start Mass Invite with ${inviterAccounts.length} Account(s)`}
                </button>
              </form>
            )}

            {/* ─── Username Mode ─── */}
            {inviterMode === 'username' && (
              <form onSubmit={handleInviteByUsername}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Target Group</label>
                    <input type="text" className="glass-input" placeholder="https://t.me/your_group" value={inviteGroup} onChange={e => setInviteGroup(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Delay Between Invites (s)</label>
                    <input type="number" min="1" step="0.5" className="glass-input" value={inviterDelay} onChange={e => setInviterDelay(e.target.value)} />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Usernames to Add</label>
                  <textarea
                    className="glass-input"
                    placeholder={`@username1\n@username2\nusername3, username4`}
                    value={usernameInput}
                    onChange={e => setUsernameInput(e.target.value)}
                    required
                    rows={7}
                    style={{ resize: 'vertical', fontFamily: 'monospace', fontSize: '0.88rem', lineHeight: 1.6 }}
                  />
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                    One per line or comma-separated. The <code>@</code> prefix is optional.
                    {usernameInput.trim() && (
                      <b style={{ color: '#a5b4fc', marginLeft: '8px' }}>
                        {usernameInput.split(/[\n,]+/).map(u => u.trim()).filter(Boolean).length} username(s) detected
                      </b>
                    )}
                  </div>
                </div>

                {/* Account Multi-Select */}
                <div className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label className="form-label" style={{ margin: 0 }}>Select Worker Accounts</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{
                        background: inviterAccounts.length > 0 ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(99,102,241,0.4)', borderRadius: '20px',
                        padding: '2px 10px', fontSize: '0.8rem', color: '#a5b4fc', fontWeight: 600
                      }}>
                        {inviterAccounts.length} / {accounts.length} selected
                      </span>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <input type="checkbox" checked={inviterSelectAll}
                          onChange={e => handleInviterToggleAll(e.target.checked)}
                          style={{ accentColor: '#6366f1' }} />
                        All
                      </label>
                    </div>
                  </div>
                  {accounts.length === 0 ? (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', textAlign: 'center', padding: '12px 0' }}>No accounts found. Add one first.</p>
                  ) : (
                    <div style={{
                      display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                      gap: '8px', maxHeight: '180px', overflowY: 'auto', padding: '4px 2px'
                    }}>
                      {accounts.map(acc => (
                        <label key={acc.id} style={{
                          display: 'flex', alignItems: 'center', gap: '8px',
                          padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                          background: inviterAccounts.includes(acc.phone) ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.04)',
                          border: inviterAccounts.includes(acc.phone) ? '1px solid rgba(99,102,241,0.4)' : '1px solid rgba(255,255,255,0.08)',
                          transition: 'all 0.15s', fontSize: '0.85rem'
                        }}>
                          <input type="checkbox"
                            checked={inviterAccounts.includes(acc.phone)}
                            onChange={e => handleInviterToggleAccount(acc.phone, e.target.checked)}
                            style={{ accentColor: '#6366f1', flexShrink: 0 }} />
                          <span style={{ fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{acc.phone}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginBottom: '20px', padding: '12px', background: 'rgba(99,102,241,0.07)', borderRadius: '8px', borderLeft: '3px solid #6366f1' }}>
                  👤 Usernames will be resolved in real-time and added directly — split evenly across <b>{inviterAccounts.length}</b> account(s).
                </div>

                <button type="submit" className="glass-button" style={{ width: '100%', background: 'linear-gradient(135deg,#6366f1,#4f46e5)' }}
                  disabled={loading || inviterAccounts.length === 0}>
                  {loading ? '⏳ Starting...' : `👤 Add ${usernameInput.split(/[\n,]+/).map(u=>u.trim()).filter(Boolean).length || 0} Username(s) with ${inviterAccounts.length} Account(s)`}
                </button>
              </form>
            )}
          </div>
        )}


        {activeTab === 'Terminal Logs' && (
          <div className="animate-fade-in glass-panel" style={{ padding: '20px', minHeight: '400px' }}>
            <h2 style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              System Logs 
              <div style={{ display: 'flex', gap: '10px' }}>
                <button className="glass-button" style={{ padding: '6px 12px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #ef4444, #dc2626)', color: 'white' }} onClick={handleStopTasks}>🛑 Stop Tasks</button>
                <button className="glass-button secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => axios.post(`${API_BASE}/logs/clear`)}>Clear Logs</button>
              </div>
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

function App() {
  // ── License gate ──
  const [isLicensed, setIsLicensed] = useState(false);
  const [licenseChecking, setLicenseChecking] = useState(true);

  useEffect(() => {
    const savedKey = localStorage.getItem('tg_license_key');
    if (!savedKey) { setLicenseChecking(false); return; }
    // Re-verify saved key on startup
    generateHWID().then(hwid => {
      axios.post(`${API_BASE}/license/verify`, { token: savedKey, hwid })
        .then(() => { setIsLicensed(true); setLicenseChecking(false); })
        .catch(() => { localStorage.removeItem('tg_license_key'); setLicenseChecking(false); });
    });
  }, []);

  if (licenseChecking) {
    return (
      <div style={{
        position: 'fixed', inset: 0, background: '#0a0a12',
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '0.95rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🔑</div>
          Verifying license...
        </div>
      </div>
    );
  }

  if (!isLicensed) {
    return <LicenseGate onUnlocked={() => setIsLicensed(true)} />;
  }

  return <MainApp onLogout={() => setIsLicensed(false)} />;
}

export default App;
