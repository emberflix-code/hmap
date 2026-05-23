import React, { useEffect, useState } from 'react';
import axios from 'axios';

import Dashboard from './Dashboard.jsx';
import CaseEntry from './CaseEntry.jsx';
import Reports from './Reports.jsx';
import ClusterMapPanel from './ClusterMapPanel.jsx';
import WeeklyReport from './WeeklyReport.jsx';
import Login from './Login.jsx';

// Derive the API base from the page's mount path so we work whether the
// app is served at "/" (local dev) or under a subpath like "/hmap" (LGU
// portal deployment). Strip the trailing /entry, /reports, etc. so the
// base is always the SPA root.
function deriveApiBase() {
    const path = window.location.pathname;
    const match = path.match(/^(\/[^/]+)?(?:\/(?:entry|reports|clusters|weekly|login)?)?$/);
    const root = match && match[1] ? match[1] : '';
    return root + '/api';
}

// withCredentials so the hmap_jwt HttpOnly cookie auto-attaches on every
// XHR. Same-origin so CSRF isn't an issue (the SPA shell and the API live
// at the same host:port). Accept: application/json forces Laravel to return
// JSON responses on validation errors / 401 instead of HTML redirects.
const api = axios.create({
    baseURL: deriveApiBase(),
    withCredentials: true,
    headers: { Accept: 'application/json' },
});

export default function App() {
    const [view, setView] = useState(() => initialViewFromUrl());
    const [whoami, setWhoami] = useState(null);
    const [diseases, setDiseases] = useState([]);
    const [barangays, setBarangays] = useState([]);
    const [authState, setAuthState] = useState('checking'); // checking | needs_login | ok | error
    const [bootError, setBootError] = useState(null);

    // Try to load the current user. 401 means we need to show Login;
    // any other error is a real boot failure.
    const refreshAuth = () => {
        setAuthState('checking');
        setBootError(null);
        api.get('/auth/me')
            .then((r) => {
                setWhoami(r.data);
                setAuthState('ok');
            })
            .catch((err) => {
                if (err.response?.status === 401) {
                    setAuthState('needs_login');
                } else {
                    setBootError(err.response?.data?.detail || err.message);
                    setAuthState('error');
                }
            });
    };

    // Boot: check auth, then load reference data once we know who we are.
    useEffect(() => { refreshAuth(); }, []);

    useEffect(() => {
        if (authState !== 'ok') return;
        Promise.all([api.get('/diseases'), api.get('/barangays')])
            .then(([d, b]) => {
                setDiseases(d.data);
                setBarangays(b.data);
            })
            .catch((err) => setBootError(err.response?.data?.detail || err.message));
    }, [authState]);

    // Update the URL (no full reload) when the view changes so bookmarks/back work.
    useEffect(() => {
        if (authState !== 'ok') return;
        const path =
            view === 'entry' ? '/hmap/entry' :
            view === 'reports' ? '/hmap/reports' :
            view === 'clusters' ? '/hmap/clusters' :
            view === 'weekly' ? '/hmap/weekly' :
            '/hmap';
        if (window.location.pathname !== path) {
            window.history.replaceState({}, '', path);
        }
    }, [view, authState]);

    const handleLogout = async () => {
        try { await api.post('/auth/logout'); } catch (_) { /* ignore */ }
        setWhoami(null);
        setDiseases([]);
        setBarangays([]);
        setAuthState('needs_login');
    };

    if (bootError) {
        return (
            <div className="p-8 text-red-700 bg-red-50 border border-red-200 rounded-lg m-8">
                <h2 className="font-semibold text-lg mb-2">H-MAP failed to start</h2>
                <p className="text-sm">{bootError}</p>
            </div>
        );
    }

    if (authState === 'checking') {
        return <div className="p-8 text-slate-500 text-sm">Loading H-MAP…</div>;
    }

    if (authState === 'needs_login') {
        return <Login api={api} onLoggedIn={refreshAuth} />;
    }

    if (!whoami || diseases.length === 0) {
        return <div className="p-8 text-slate-500 text-sm">Loading H-MAP…</div>;
    }

    return (
        <div className="min-h-screen flex flex-col">
            <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-semibold text-slate-800">H-MAP</h1>
                    <nav className="flex items-center gap-1">
                        <NavLink active={view === 'dashboard'} onClick={() => setView('dashboard')}>
                            Dashboard
                        </NavLink>
                        <NavLink active={view === 'weekly'} onClick={() => setView('weekly')}>
                            Weekly Report
                        </NavLink>
                        <NavLink active={view === 'clusters'} onClick={() => setView('clusters')}>
                            Clusters
                        </NavLink>
                        <NavLink active={view === 'entry'} onClick={() => setView('entry')}>
                            Case Entry
                        </NavLink>
                        <NavLink active={view === 'reports'} onClick={() => setView('reports')}>
                            Reports
                        </NavLink>
                    </nav>
                </div>
                <div className="flex items-center gap-3 text-sm">
                    <span className="text-slate-600">{whoami.employee_name}</span>
                    <RoleBadge role={whoami.role} />
                    <button
                        type="button"
                        onClick={handleLogout}
                        className="ml-2 px-3 py-1.5 text-xs rounded text-slate-600 hover:bg-slate-100 hover:text-slate-800"
                    >
                        Sign out
                    </button>
                </div>
            </header>

            {view === 'dashboard' && (
                <Dashboard api={api} diseases={diseases} barangays={barangays} whoami={whoami} />
            )}
            {view === 'weekly' && (
                <WeeklyReport api={api} diseases={diseases} />
            )}
            {view === 'clusters' && (
                <ClusterMapPanel api={api} />
            )}
            {view === 'entry' && (
                <CaseEntry api={api} diseases={diseases} barangays={barangays} />
            )}
            {view === 'reports' && (
                <Reports whoami={whoami} diseases={diseases} />
            )}
        </div>
    );
}

function initialViewFromUrl() {
    const p = window.location.pathname;
    if (p.includes('/entry')) return 'entry';
    if (p.includes('/reports')) return 'reports';
    if (p.includes('/clusters')) return 'clusters';
    if (p.includes('/weekly')) return 'weekly';
    return 'dashboard';
}

function NavLink({ active, onClick, children }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={
                'px-3 py-1.5 text-sm rounded ' +
                (active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800')
            }
        >
            {children}
        </button>
    );
}

function RoleBadge({ role }) {
    const color =
        role === 'Administrator'
            ? 'bg-rose-100 text-rose-700'
            : role === 'Analyst'
            ? 'bg-amber-100 text-amber-700'
            : 'bg-slate-100 text-slate-700';
    return <span className={'px-2 py-1 rounded text-xs font-medium ' + color}>{role}</span>;
}
