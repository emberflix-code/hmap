import React, { useState } from 'react';

/**
 * H-MAP login form. Posts to /api/auth/login which proxies to HRMO's
 * /api/v1/auth/login, then stores the JWT in an HttpOnly cookie set
 * server-side. After success, calls onLoggedIn() so App.jsx can refetch
 * whoami and mount the dashboard.
 */
export default function Login({ api, onLoggedIn }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const submit = async (e) => {
        e.preventDefault();
        if (!username || !password) return;
        setSubmitting(true);
        setError(null);
        try {
            await api.post('/auth/login', { username, password });
            onLoggedIn();
        } catch (err) {
            const msg =
                err.response?.data?.message ||
                err.response?.data?.detail ||
                err.message ||
                'Login failed';
            setError(msg);
            setPassword('');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="app-shell min-h-screen bg-slate-50 grid lg:grid-cols-2">
            <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-blue-700 via-blue-600 to-teal-500 text-white">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-white/15 flex items-center justify-center" aria-hidden="true">
                        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12h4l2-5 4 10 2-5h6" /></svg>
                    </div>
                    <span className="text-lg font-semibold tracking-tight">H-MAP</span>
                </div>
                <div className="max-w-md">
                    <h2 className="text-3xl font-semibold leading-tight">Disease outbreak management for Parañaque City</h2>
                    <p className="mt-4 text-white/80 leading-relaxed">
                        PIDSR thresholds, hotspot detection, trend forecasts and response recommendations for the
                        City Epidemiology and Surveillance Unit, in one place.
                    </p>
                    <ul className="mt-8 space-y-3 text-sm text-white/90">
                        {['Weekly PIDSR alert and epidemic thresholds', 'Dengue hotspots across barangay boundaries', 'Ranked response for Moderate and High risk barangays'].map((t) => (
                            <li key={t} className="flex items-center gap-2.5">
                                <span className="h-5 w-5 rounded-full bg-white/20 flex items-center justify-center text-xs" aria-hidden="true">✓</span>
                                {t}
                            </li>
                        ))}
                    </ul>
                </div>
                <p className="text-xs text-white/60">City Health Office of Parañaque · Access limited to authorized CESU personnel</p>
            </div>
            <div className="flex items-center justify-center p-6">
            <div className="w-full max-w-sm">
                <div className="mb-8">
                    <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Sign in to H-MAP</h1>
                    <p className="text-sm text-slate-500 mt-1">
                        Parañaque City Epidemiology &amp; Surveillance Unit
                    </p>
                </div>
                <form
                    onSubmit={submit}
                    className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4"
                >
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            HRMO Username
                        </label>
                        <input
                            type="text"
                            autoComplete="username"
                            autoFocus
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full h-10 px-3 text-sm"
                            disabled={submitting}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full h-10 px-3 text-sm"
                            disabled={submitting}
                            required
                        />
                    </div>
                    {error && (
                        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={submitting || !username || !password}
                        className="w-full h-10 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-md text-sm shadow-sm"
                    >
                        {submitting ? 'Signing in…' : 'Sign in'}
                    </button>
                    <p className="text-xs text-slate-500 text-center pt-2">
                        Use your existing HRMO Portal credentials.
                    </p>
                </form>
            </div>
            </div>
        </div>
    );
}
