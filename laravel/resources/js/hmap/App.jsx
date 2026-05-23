import React, { useEffect, useState } from 'react';
import axios from 'axios';

import Dashboard from './Dashboard.jsx';
import CaseEntry from './CaseEntry.jsx';
import Reports from './Reports.jsx';
import ClusterMapPanel from './ClusterMapPanel.jsx';
import WeeklyReport from './WeeklyReport.jsx';

// Derive the API base from the page's mount path so we work whether the
// app is served at "/" (local dev) or under a subpath like "/hmap" (LGU
// portal deployment). Strip the trailing /entry, /reports, etc. so the
// base is always the SPA root.
function deriveApiBase() {
    const path = window.location.pathname;
    // Match the SPA root (/, /hmap, /hmap/) before any of the React-router segments
    const match = path.match(/^(\/[^/]+)?(?:\/(?:entry|reports|clusters|weekly)?)?$/);
    const root = match && match[1] ? match[1] : '';
    return root + '/api';
}

const api = axios.create({ baseURL: deriveApiBase() });

export default function App() {
    const [view, setView] = useState(() => initialViewFromUrl());
    const [whoami, setWhoami] = useState(null);
    const [diseases, setDiseases] = useState([]);
    const [barangays, setBarangays] = useState([]);
    const [bootError, setBootError] = useState(null);

    useEffect(() => {
        Promise.all([
            api.get('/whoami'),
            api.get('/diseases'),
            api.get('/barangays'),
        ])
            .then(([w, d, b]) => {
                setWhoami(w.data);
                setDiseases(d.data);
                setBarangays(b.data);
            })
            .catch((err) => setBootError(err.response?.data?.detail || err.message));
    }, []);

    // Update the URL (no full reload) when the view changes so bookmarks/back work.
    useEffect(() => {
        const path =
            view === 'entry' ? '/hmap/entry' :
            view === 'reports' ? '/hmap/reports' :
            view === 'clusters' ? '/hmap/clusters' :
            view === 'weekly' ? '/hmap/weekly' :
            '/hmap';
        if (window.location.pathname !== path) {
            window.history.replaceState({}, '', path);
        }
    }, [view]);

    if (bootError) {
        return (
            <div className="p-8 text-red-700 bg-red-50 border border-red-200 rounded-lg m-8">
                <h2 className="font-semibold text-lg mb-2">H-MAP failed to start</h2>
                <p className="text-sm">{bootError}</p>
            </div>
        );
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
