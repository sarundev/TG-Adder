import React, { useState, useEffect, useCallback } from 'react';
import './AdminDashboard.css';

const ADMIN_KEY = 'admin123';

function AdminDashboard({ onBack }) {
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateDuration, setGenerateDuration] = useState('1_month');
  const [generating, setGenerating] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchLicenses = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/license/list?admin_key=${ADMIN_KEY}`);
      const data = await res.json();
      setLicenses(data.keys || []);
    } catch (e) {
      showToast('Failed to fetch licenses', 'error');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchLicenses();
  }, [fetchLicenses]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/license/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_key: ADMIN_KEY, duration: generateDuration, prefix: 'TLG' })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`License generated: ${data.token}`);
        setShowGenerateModal(false);
        fetchLicenses();
      } else {
        showToast('Failed to generate license', 'error');
      }
    } catch (e) {
      showToast('Server error', 'error');
    }
    setGenerating(false);
  };

  const handleRevoke = async (token) => {
    if (!window.confirm(`Revoke license "${token}"? This action cannot be undone.`)) return;
    setActionLoading(prev => ({ ...prev, [token]: 'revoke' }));
    try {
      const res = await fetch('/api/license/revoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_key: ADMIN_KEY, token })
      });
      const data = await res.json();
      if (data.status === 'revoked') {
        showToast(`License revoked: ${token}`);
        fetchLicenses();
      } else {
        showToast('Failed to revoke', 'error');
      }
    } catch (e) {
      showToast('Server error', 'error');
    }
    setActionLoading(prev => ({ ...prev, [token]: null }));
  };

  const handleResetHwid = async (token) => {
    if (!window.confirm(`Reset HWID for "${token}"? The user will need to re-activate.`)) return;
    setActionLoading(prev => ({ ...prev, [token]: 'reset' }));
    try {
      const res = await fetch('/api/license/reset-hwid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_key: ADMIN_KEY, token })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast(`HWID reset for: ${token}`);
        fetchLicenses();
      } else {
        showToast('Failed to reset HWID', 'error');
      }
    } catch (e) {
      showToast('Server error', 'error');
    }
    setActionLoading(prev => ({ ...prev, [token]: null }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard!');
  };

  // Filter + Search
  const filtered = licenses.filter(lic => {
    const matchesSearch = searchQuery === '' ||
      lic.token.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (lic.hwid && lic.hwid.toLowerCase().includes(searchQuery.toLowerCase()));

    if (filterStatus === 'all') return matchesSearch;
    if (filterStatus === 'active') return matchesSearch && lic.bound;
    if (filterStatus === 'unbound') return matchesSearch && !lic.bound;
    if (filterStatus === 'expired') {
      if (!lic.expires_at || lic.expires_at === 'Never') return false;
      return matchesSearch && new Date(lic.expires_at) < new Date();
    }
    return matchesSearch;
  });

  // Stats
  const totalKeys = licenses.length;
  const activeDevices = licenses.filter(l => l.bound).length;
  const unboundKeys = licenses.filter(l => !l.bound).length;
  const expiredKeys = licenses.filter(l => {
    if (!l.expires_at || l.expires_at === 'Never') return false;
    return new Date(l.expires_at) < new Date();
  }).length;

  const getStatusInfo = (lic) => {
    if (!lic.bound) return { label: 'Unbound', className: 'status-unbound' };
    if (lic.expires_at && lic.expires_at !== 'Never' && new Date(lic.expires_at) < new Date()) {
      return { label: 'Expired', className: 'status-expired' };
    }
    return { label: 'Active', className: 'status-active' };
  };

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'Never') return 'Never';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const durationLabels = {
    '1_week': '1 Week',
    '1_month': '1 Month',
    '2_months': '2 Months',
    '3_months': '3 Months',
    '1_year': '1 Year',
    'lifetime': 'Lifetime'
  };

  return (
    <div className="admin-dashboard">
      {/* Toast */}
      {toast && (
        <div className={`admin-toast admin-toast-${toast.type}`}>
          <span>{toast.type === 'success' ? '✓' : '✕'}</span>
          {toast.message}
        </div>
      )}

      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="admin-sidebar-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Admin Panel</span>
        </div>
        <nav className="admin-sidebar-nav">
          <button className="admin-nav-item active">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            Overview
          </button>
          <button className="admin-nav-item active-indicator">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
              <line x1="6" y1="6" x2="6.01" y2="6"/>
              <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>
            Device Control
          </button>
          <button className="admin-nav-item">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            Settings
          </button>
        </nav>
        <div className="admin-sidebar-footer">
          <button className="admin-back-btn" onClick={onBack}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back to Site
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        {/* Header */}
        <header className="admin-header">
          <div>
            <h1 className="admin-title">Device & License Control</h1>
            <p className="admin-subtitle">Manage all user devices, licenses, and access permissions</p>
          </div>
          <div className="admin-header-actions">
            <button className="admin-btn admin-btn-refresh" onClick={fetchLicenses} disabled={loading}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
              Refresh
            </button>
            <button className="admin-btn admin-btn-generate" onClick={() => setShowGenerateModal(true)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Generate License
            </button>
          </div>
        </header>

        {/* Stats Row */}
        <div className="admin-stats">
          <div className="admin-stat-card">
            <div className="admin-stat-icon stat-total">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
            </div>
            <div>
              <span className="admin-stat-value">{totalKeys}</span>
              <span className="admin-stat-label">Total Keys</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon stat-active">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
            </div>
            <div>
              <span className="admin-stat-value">{activeDevices}</span>
              <span className="admin-stat-label">Active Devices</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon stat-unbound">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </div>
            <div>
              <span className="admin-stat-value">{unboundKeys}</span>
              <span className="admin-stat-label">Unbound Keys</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon stat-expired">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div>
              <span className="admin-stat-value">{expiredKeys}</span>
              <span className="admin-stat-label">Expired</span>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="admin-toolbar">
          <div className="admin-search-wrapper">
            <svg className="admin-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              type="text"
              className="admin-search"
              placeholder="Search by token or HWID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="admin-filters">
            {['all', 'active', 'unbound', 'expired'].map(f => (
              <button
                key={f}
                className={`admin-filter-btn ${filterStatus === f ? 'active' : ''}`}
                onClick={() => setFilterStatus(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                {f === 'all' && <span className="admin-filter-count">{totalKeys}</span>}
                {f === 'active' && <span className="admin-filter-count">{activeDevices}</span>}
                {f === 'unbound' && <span className="admin-filter-count">{unboundKeys}</span>}
                {f === 'expired' && <span className="admin-filter-count">{expiredKeys}</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="admin-table-container">
          {loading ? (
            <div className="admin-loading">
              <div className="admin-spinner" />
              <p>Loading licenses...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="admin-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
              <h3>No licenses found</h3>
              <p>Generate a new license to get started</p>
            </div>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>License Key</th>
                  <th>Status</th>
                  <th>HWID (Device)</th>
                  <th>Duration</th>
                  <th>Expires</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((lic, idx) => {
                  const status = getStatusInfo(lic);
                  return (
                    <tr key={lic.token} className={actionLoading[lic.token] ? 'row-loading' : ''}>
                      <td className="col-num">{idx + 1}</td>
                      <td className="col-token">
                        <div className="token-cell">
                          <code>{lic.token}</code>
                          <button className="admin-copy-btn" onClick={() => copyToClipboard(lic.token)} title="Copy token">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                            </svg>
                          </button>
                        </div>
                      </td>
                      <td>
                        <span className={`admin-status-badge ${status.className}`}>
                          <span className="status-dot" />
                          {status.label}
                        </span>
                      </td>
                      <td className="col-hwid">
                        {lic.hwid ? (
                          <code className="hwid-text">{lic.hwid.substring(0, 16)}...</code>
                        ) : (
                          <span className="hwid-none">—</span>
                        )}
                      </td>
                      <td>{durationLabels[lic.duration] || lic.duration || 'Lifetime'}</td>
                      <td>{formatDate(lic.expires_at)}</td>
                      <td>{formatDate(lic.created_at)}</td>
                      <td className="col-actions">
                        <button
                          className="admin-action-btn action-reset"
                          onClick={() => handleResetHwid(lic.token)}
                          disabled={!lic.bound || actionLoading[lic.token]}
                          title="Unbind device"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="23 4 23 10 17 10"/>
                            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                          </svg>
                          Reset
                        </button>
                        <button
                          className="admin-action-btn action-revoke"
                          onClick={() => handleRevoke(lic.token)}
                          disabled={actionLoading[lic.token]}
                          title="Revoke license permanently"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                          </svg>
                          Revoke
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="admin-table-footer">
          <span>Showing {filtered.length} of {totalKeys} licenses</span>
        </div>
      </main>

      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="admin-modal-overlay" onClick={() => setShowGenerateModal(false)}>
          <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h2>Generate New License</h2>
              <button className="admin-modal-close" onClick={() => setShowGenerateModal(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div className="admin-modal-body">
              <label className="admin-modal-label">Select Duration</label>
              <div className="admin-duration-grid">
                {Object.entries(durationLabels).map(([key, label]) => (
                  <button
                    key={key}
                    className={`admin-duration-option ${generateDuration === key ? 'selected' : ''}`}
                    onClick={() => setGenerateDuration(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div className="admin-modal-footer">
              <button className="admin-btn admin-btn-cancel" onClick={() => setShowGenerateModal(false)}>Cancel</button>
              <button className="admin-btn admin-btn-generate" onClick={handleGenerate} disabled={generating}>
                {generating ? (
                  <>
                    <span className="admin-btn-spinner" />
                    Generating...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    Generate Key
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
