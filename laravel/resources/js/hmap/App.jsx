import React, { useEffect, useState } from 'react';
import axios from 'axios';

import Dashboard from './Dashboard.jsx';
import CaseEntry from './CaseEntry.jsx';
import Reports from './Reports.jsx';
import ClusterMapPanel from './ClusterMapPanel.jsx';
import WeeklyReport from './WeeklyReport.jsx';
import Login from './Login.jsx';
import MfaPrompt from './MfaPrompt.jsx';
import AlertsBell from './AlertsBell.jsx';

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
    const [authState, setAuthState] = useState('checking'); // checking | needs_login | needs_mfa | ok | error
    const [mfaEnrolled, setMfaEnrolled] = useState(false);
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
                if (err.response?.status === 401 && err.response.data?.error === 'mfa_required') {
                    setMfaEnrolled(!!err.response.data.enrolled);
                    setAuthState('needs_mfa');
                } else if (err.response?.status === 401) {
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

    if (authState === 'needs_mfa') {
        return <MfaPrompt api={api} enrolled={mfaEnrolled} onVerified={refreshAuth} onCancel={handleLogout} />;
    }

    if (!whoami || diseases.length === 0) {
        return <div className="p-8 text-slate-500 text-sm">Loading H-MAP…</div>;
    }

    return (
        <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
            <header className="sticky top-0 z-[1100] bg-white/95 backdrop-blur border-b border-slate-200 px-4 md:px-6 md:h-16 flex flex-wrap md:flex-nowrap items-center justify-between gap-x-3">
                    <div className="h-16 flex items-center gap-3 shrink-0">
                        <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center shadow-sm" aria-hidden="true">
                            <svg viewBox="0 0 24 24" className="h-5 w-5 text-white" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M3 12h4l2-5 4 10 2-5h6" />
                            </svg>
                        </div>
                        <div className="leading-tight">
                            <h1 className="text-[15px] font-semibold tracking-tight text-slate-900">H-MAP</h1>
                            <p className="hidden xl:block text-[11px] text-slate-500">Parañaque City Epidemiology and Surveillance Unit</p>
                        </div>
                    </div>
                    <nav className="order-last md:order-none w-full md:w-auto md:flex-1 md:ml-4 lg:ml-6 h-11 md:h-full flex items-stretch gap-1 overflow-x-auto whitespace-nowrap [scrollbar-width:none] border-t border-slate-100 md:border-0 -mx-4 px-4 md:mx-0 md:px-0">
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
                <div className="h-16 flex items-center gap-2 md:gap-3 text-sm shrink-0">
                    <AlertsBell api={api} />
                    <div className="hidden md:block h-8 w-px bg-slate-200" />
                    <div className="flex items-center gap-2.5">
                        <div className="h-8 w-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-semibold" title={whoami.employee_name}>
                            {initials(whoami.employee_name)}
                        </div>
                        <div className="hidden lg:block leading-tight">
                            <div className="text-[13px] font-medium text-slate-800">{whoami.employee_name}</div>
                            <RoleBadge role={whoami.role} />
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={handleLogout}
                        className="ml-1 px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    >
                        Sign out
                    </button>
                </div>
            </header>

            {view === 'dashboard' && (
                <Dashboard api={api} diseases={diseases} barangays={barangays} whoami={whoami} />
            )}
            {view === 'weekly' && (
                <WeeklyReport api={api} diseases={diseases} isAdmin={whoami.role === 'Administrator'} />
            )}
            {view === 'clusters' && (
                <ClusterMapPanel api={api} />
            )}
            {view === 'entry' && (
                <CaseEntry api={api} diseases={diseases} barangays={barangays} />
            )}
            {view === 'reports' && (
                <Reports api={api} whoami={whoami} diseases={diseases} />
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
            aria-current={active ? 'page' : undefined}
            className={
                'px-3 text-sm border-b-2 -mb-px transition-colors ' +
                (active
                    ? 'border-blue-600 text-blue-700 font-semibold'
                    : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300')
            }
        >
            {children}
        </button>
    );
}

function RoleBadge({ role }) {
    const color =
        role === 'Administrator'
            ? 'text-blue-700'
            : role === 'Analyst'
            ? 'text-teal-700'
            : 'text-slate-500';
    return <span className={'text-[11px] font-medium ' + color}>{role}</span>;
}

function initials(name) {
    return (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
}
