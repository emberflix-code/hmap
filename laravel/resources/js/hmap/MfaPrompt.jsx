import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';

const inputClass =
    'w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500';
const buttonClass =
    'w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium py-2 rounded-md text-sm transition-colors';

/**
 * Second login step, shown when the API answers 401 `mfa_required`.
 *   enrolled = false → first login: scan a QR code, confirm one code, then
 *                      save the recovery codes (shown once)
 *   enrolled = true  → enter the 6-digit code, or a recovery code
 * Calls onVerified() so App.jsx can reload whoami.
 */
export default function MfaPrompt({ api, enrolled, onVerified, onCancel }) {
    const [setup, setSetup] = useState(null);         // { secret, otpauth_uri, qr }
    const [recoveryCodes, setRecoveryCodes] = useState(null);
    const [code, setCode] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [notice, setNotice] = useState(null);

    useEffect(() => {
        if (enrolled) return;
        api.post('/auth/mfa/enroll')
            .then(async (r) => {
                const qr = await QRCode.toDataURL(r.data.otpauth_uri, { margin: 1, width: 200 });
                setSetup({ ...r.data, qr });
            })
            .catch((err) => setError(err.response?.data?.detail || err.message));
    }, [api, enrolled]);

    const submit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            if (enrolled) {
                const r = await api.post('/auth/mfa/verify', { code });
                if (r.data.method === 'recovery') {
                    setNotice(
                        `Recovery code accepted. You have ${r.data.recovery_codes_left} left; ` +
                            'ask the CESU Administrator to reset your authenticator if you lost your phone.'
                    );
                    return;
                }
                onVerified();
            } else {
                const r = await api.post('/auth/mfa/enroll/confirm', { code });
                setRecoveryCodes(r.data.recovery_codes);
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
            setCode('');
        } finally {
            setSubmitting(false);
        }
    };

    let body;
    if (recoveryCodes) {
        body = (
            <div className="space-y-4">
                <p className="text-sm text-slate-700">
                    Your authenticator is set up. Write down these recovery codes and keep them
                    somewhere safe. Each one works once if you lose your phone.
                    They will not be shown again.
                </p>
                <div className="grid grid-cols-2 gap-2 font-mono text-sm bg-slate-50 border border-slate-200 rounded p-3">
                    {recoveryCodes.map((c) => <div key={c}>{c}</div>)}
                </div>
                <button type="button" className={buttonClass} onClick={onVerified}>
                    I have saved my codes
                </button>
            </div>
        );
    } else if (notice) {
        body = (
            <div className="space-y-4">
                <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                    {notice}
                </div>
                <button type="button" className={buttonClass} onClick={onVerified}>
                    Continue
                </button>
            </div>
        );
    } else {
        body = (
            <form onSubmit={submit} className="space-y-4">
                {!enrolled && (
                    <div className="space-y-3 text-sm text-slate-700">
                        <p>
                            Set up two-step sign-in. Install Google Authenticator or Microsoft
                            Authenticator on your phone, then scan this code with the app.
                        </p>
                        {setup ? (
                            <>
                                <img src={setup.qr} alt="Authenticator setup QR code" className="mx-auto" width={200} height={200} />
                                <p className="text-xs text-slate-500">
                                    Cannot scan? Enter this key in the app instead:
                                    <span className="block font-mono text-slate-700 mt-1 break-all">
                                        {setup.secret.match(/.{1,4}/g).join(' ')}
                                    </span>
                                </p>
                            </>
                        ) : (
                            !error && <p className="text-slate-500">Preparing setup…</p>
                        )}
                    </div>
                )}
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        {enrolled ? 'Code from your authenticator app' : 'Enter the 6-digit code the app shows'}
                    </label>
                    <input
                        type="text"
                        inputMode={enrolled ? 'text' : 'numeric'}
                        autoComplete="one-time-code"
                        autoFocus
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className={inputClass + ' tracking-widest text-center font-mono'}
                        disabled={submitting}
                        required
                    />
                    {enrolled && (
                        <p className="text-xs text-slate-500 mt-1">
                            Lost your phone? Enter one of your recovery codes instead.
                        </p>
                    )}
                </div>
                {error && (
                    <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
                        {error}
                    </div>
                )}
                <button type="submit" disabled={submitting || !code} className={buttonClass}>
                    {submitting ? 'Checking…' : enrolled ? 'Verify' : 'Finish setup'}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="w-full text-xs text-slate-500 hover:text-slate-700"
                >
                    Sign out
                </button>
            </form>
        );
    }

    return (
        <div className="app-shell min-h-screen bg-slate-50 flex items-center justify-center p-4">
            <div className="w-full max-w-sm">
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-slate-800">H-MAP</h1>
                    <p className="text-sm text-slate-500 mt-1">Two-step sign-in</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">{body}</div>
            </div>
        </div>
    );
}
