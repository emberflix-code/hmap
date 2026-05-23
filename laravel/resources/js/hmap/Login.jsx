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
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
            <div className="w-full max-w-sm">
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-slate-800">H-MAP</h1>
                    <p className="text-sm text-slate-500 mt-1">
                        Parañaque City Epidemiology &amp; Surveillance
                    </p>
                </div>
                <form
                    onSubmit={submit}
                    className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-4"
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
                            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium py-2 rounded-md text-sm transition-colors"
                    >
                        {submitting ? 'Signing in…' : 'Sign in'}
                    </button>
                    <p className="text-xs text-slate-500 text-center pt-2">
                        Use your existing HRMO Portal credentials.
                    </p>
                </form>
            </div>
        </div>
    );
}
