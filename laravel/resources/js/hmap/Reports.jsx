import React, { useEffect, useMemo, useState } from 'react';

const ROLE_LEVELS = { Encoder: 1, Analyst: 2, Administrator: 3 };

function roleMeets(actual, minimum) {
    return (ROLE_LEVELS[actual] ?? 0) >= (ROLE_LEVELS[minimum] ?? 0);
}

export default function Reports({ api, whoami, diseases }) {
    const today = useMemo(() => new Date(), []);
    const [summaryYear, setSummaryYear] = useState(today.getFullYear());
    const [summaryDisease, setSummaryDisease] = useState('');

    const role = whoami.role;

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-4">
            <ReportCard
                title="My entry log"
                description="Every case you personally encoded. Useful for verifying a week's work."
                role={role}
                requires="Encoder"
                href="/api/export/my-entries"
                filenameHint={`my-entries-${whoami.employee_id}-${today.toISOString().slice(0, 10)}.csv`}
            />

            <ReportCard
                title="Disease summary report"
                description="Per-(disease, barangay, week) aggregates for the selected year, with EWARN alert flag. Anonymized; suitable for sharing with city health office leadership."
                role={role}
                requires="Analyst"
                href={
                    '/api/export/disease-summary?year=' +
                    encodeURIComponent(summaryYear) +
                    (summaryDisease ? '&disease_code=' + encodeURIComponent(summaryDisease) : '')
                }
                filenameHint={`disease-summary-${summaryDisease || 'all'}-${summaryYear}.csv`}
                controls={
                    <div className="flex gap-3 items-end">
                        <label className="flex flex-col text-xs text-slate-600">
                            <span className="mb-1">Year</span>
                            <input
                                type="number"
                                min={2010}
                                max={2100}
                                className="border border-slate-300 rounded px-2 py-1.5 text-sm w-24"
                                value={summaryYear}
                                onChange={(e) => setSummaryYear(parseInt(e.target.value || '0', 10))}
                            />
                        </label>
                        <label className="flex flex-col text-xs text-slate-600">
                            <span className="mb-1">Disease (optional)</span>
                            <select
                                className="border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"
                                value={summaryDisease}
                                onChange={(e) => setSummaryDisease(e.target.value)}
                            >
                                <option value="">All diseases</option>
                                {diseases.map((d) => (
                                    <option key={d.disease_code} value={d.disease_code}>
                                        {d.disease_name}
                                    </option>
                                ))}
                            </select>
                        </label>
                    </div>
                }
            />

            <ReportCard
                title="Full case registry"
                description="All active case records, every column. Intended for DOH submission and archival purposes."
                role={role}
                requires="Administrator"
                href="/api/export/full-registry"
                filenameHint={`hmap-registry-${today.toISOString().slice(0, 10)}.csv`}
                note="Large export (~35,000 rows); the file streams in chunks of 500."
            />

            {roleMeets(role, 'Administrator') && <NotificationRecipients api={api} />}
            {roleMeets(role, 'Administrator') && <BackupStatus api={api} />}

            <div className="text-xs text-slate-500 mt-4 px-1">
                Every export is recorded in the system audit log with your employee ID, the export
                type, row count, IP address, and timestamp — consistent with Republic Act No.
                10173, the Data Privacy Act of 2012.
            </div>
        </div>
    );
}

// Who receives outbreak alerts by email and SMS (Module 7). Alerts themselves
// are created by the scheduled `php artisan hmap:notify`.
function NotificationRecipients({ api }) {
    const empty = { full_name: '', position: '', email: '', mobile: '', via_email: true, via_sms: false };
    const [rows, setRows] = useState(null);
    const [form, setForm] = useState(empty);
    const [message, setMessage] = useState(null);

    const load = () => api.get('/notification-recipients').then((r) => setRows(r.data))
        .catch(() => setMessage('Recipient list unavailable.'));
    useEffect(() => { load(); }, [api]);

    const errorText = (err) => {
        const e = err.response?.data?.errors;
        return e ? Object.values(e).flat().join(' ') : err.response?.data?.message || err.message;
    };
    const add = (e) => {
        e.preventDefault();
        const body = { ...form, email: form.email || null, mobile: form.mobile || null, position: form.position || null };
        api.post('/notification-recipients', body)
            .then(() => { setForm(empty); setMessage('Recipient added.'); load(); })
            .catch((err) => setMessage(errorText(err)));
    };
    const toggle = (r, field) =>
        api.put(`/notification-recipients/${r.recipient_id}`, { [field]: !r[field] })
            .then(load).catch((err) => setMessage(errorText(err)));
    const test = (r) =>
        api.post(`/notification-recipients/${r.recipient_id}/test`)
            .then((res) => setMessage(`Test to ${r.full_name}: ` + Object.entries(res.data)
                .map(([ch, v]) => `${ch} ${v.status}${v.error ? ' (' + v.error + ')' : ''}`).join(', ')))
            .catch((err) => setMessage(errorText(err)));

    const input = 'border border-slate-300 rounded px-2 py-1 text-xs';
    return (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-sm font-semibold text-slate-800">Outbreak alert recipients</h2>
                    <p className="text-xs text-slate-600 mt-1">
                        People who receive an email or SMS when a barangay exceeds its epidemic threshold,
                        reports a single-case alert disease, or has an active hotspot. One message per
                        disease, barangay, alert type and week; no patient information.
                    </p>
                </div>
                <span className="text-[10px] uppercase font-semibold tracking-wide px-2 py-1 rounded bg-emerald-50 text-emerald-700">
                    Administrator+
                </span>
            </div>
            {message && <div className="text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded px-3 py-2">{message}</div>}
            {rows && (
                <table className="text-xs w-full">
                    <thead className="text-slate-500 text-left">
                        <tr><th className="py-1">Name</th><th>Email</th><th>Mobile</th><th>Email</th><th>SMS</th><th>Active</th><th /></tr>
                    </thead>
                    <tbody className="text-slate-700">
                        {rows.map((r) => (
                            <tr key={r.recipient_id} className={'border-t border-slate-100 ' + (r.is_active ? '' : 'opacity-50')}>
                                <td className="py-1">{r.full_name}<div className="text-slate-400">{r.position}</div></td>
                                <td>{r.email || '-'}</td>
                                <td>{r.mobile || '-'}</td>
                                {['via_email', 'via_sms', 'is_active'].map((f) => (
                                    <td key={f}><input type="checkbox" checked={!!r[f]} onChange={() => toggle(r, f)} /></td>
                                ))}
                                <td className="text-right">
                                    <button type="button" onClick={() => test(r)}
                                            className="px-2 py-0.5 rounded border border-slate-300 hover:bg-slate-100">Send test</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            <form onSubmit={add} className="flex flex-wrap gap-2 items-end">
                <input className={input} placeholder="Full name" required value={form.full_name}
                       onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
                <input className={input} placeholder="Position" value={form.position}
                       onChange={(e) => setForm({ ...form, position: e.target.value })} />
                <input className={input} type="email" placeholder="Email" value={form.email}
                       onChange={(e) => setForm({ ...form, email: e.target.value })} />
                <input className={input} placeholder="Mobile 09XXXXXXXXX" value={form.mobile}
                       onChange={(e) => setForm({ ...form, mobile: e.target.value })} />
                <label className="text-xs"><input type="checkbox" checked={form.via_email}
                       onChange={(e) => setForm({ ...form, via_email: e.target.checked })} /> email</label>
                <label className="text-xs"><input type="checkbox" checked={form.via_sms}
                       onChange={(e) => setForm({ ...form, via_sms: e.target.checked })} /> SMS</label>
                <button type="submit" className="px-3 py-1 rounded bg-blue-600 text-white text-xs hover:bg-blue-700">Add recipient</button>
            </form>
        </section>
    );
}

// Read-only register of the nightly encrypted backups (ml/backup_db.py).
// A backup older than ~1 day, or a failed test restoration, is shown in red.
function BackupStatus({ api }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        api.get('/admin/backups')
            .then((r) => setData(r.data))
            .catch(() => setError('Backup register unavailable.'));
    }, [api]);

    const stale =
        data && (!data.last_success_at || Date.now() - new Date(data.last_success_at.replace(' ', 'T')) > 36 * 3600 * 1000);
    const verifyFailed = data && data.last_verify_status === 'failed';

    return (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-sm font-semibold text-slate-800">Database backups</h2>
                    <p className="text-xs text-slate-600 mt-1">
                        Encrypted (AES-256) nightly backups with SHA-256 checksums, test-restored weekly.
                        Restoration is performed from the server by the system administrator.
                    </p>
                </div>
                <span className="text-[10px] uppercase font-semibold tracking-wide px-2 py-1 rounded bg-emerald-50 text-emerald-700">
                    Administrator+
                </span>
            </div>
            {error && <div className="text-xs text-red-700">{error}</div>}
            {data && (
                <>
                    <div className="flex gap-6 text-xs">
                        <div className={stale ? 'text-red-700 font-semibold' : 'text-slate-700'}>
                            Last successful backup: {data.last_success_at || 'none yet'}
                        </div>
                        <div className={verifyFailed ? 'text-red-700 font-semibold' : 'text-slate-700'}>
                            Last test restoration: {data.last_verified_at || 'none yet'}
                            {data.last_verify_status && ` (${data.last_verify_status})`}
                        </div>
                    </div>
                    <table className="text-xs w-full">
                        <thead className="text-slate-500 text-left">
                            <tr>
                                <th className="py-1">#</th>
                                <th>Started</th>
                                <th>Status</th>
                                <th>Size</th>
                                <th>Test restore</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-700">
                            {data.backups.slice(0, 10).map((b) => (
                                <tr key={b.backup_id} className="border-t border-slate-100" title={b.error || b.verify_detail || ''}>
                                    <td className="py-1">{b.backup_id}</td>
                                    <td>{b.started_at}</td>
                                    <td className={b.status === 'failed' ? 'text-red-700' : ''}>
                                        {b.status}{b.file_pruned ? ' (file pruned)' : ''}
                                    </td>
                                    <td>{b.file_size_bytes != null ? (b.file_size_bytes / 1048576).toFixed(1) + ' MB' : '-'}</td>
                                    <td className={b.verify_status === 'failed' ? 'text-red-700' : ''}>
                                        {b.verify_status || '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
        </section>
    );
}

function ReportCard({ title, description, role, requires, href, filenameHint, controls, note }) {
    const allowed = roleMeets(role, requires);
    return (
        <section
            className={
                'bg-white rounded-lg border shadow-sm p-5 flex flex-col gap-3 ' +
                (allowed ? 'border-slate-200' : 'border-slate-200 opacity-60')
            }
        >
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
                    <p className="text-xs text-slate-600 mt-1">{description}</p>
                </div>
                <span
                    className={
                        'text-[10px] uppercase font-semibold tracking-wide px-2 py-1 rounded ' +
                        (allowed
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-slate-100 text-slate-500')
                    }
                >
                    {requires}+
                </span>
            </div>
            {controls && allowed && <div>{controls}</div>}
            <div className="flex items-center gap-3 mt-1">
                <a
                    href={allowed ? href : undefined}
                    download={allowed ? filenameHint : undefined}
                    onClick={(e) => !allowed && e.preventDefault()}
                    className={
                        'px-4 py-2 rounded text-sm font-medium ' +
                        (allowed
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-slate-200 text-slate-500 cursor-not-allowed')
                    }
                >
                    Download CSV
                </a>
                {!allowed && (
                    <span className="text-xs text-slate-500">
                        Requires {requires} role.
                    </span>
                )}
                {note && allowed && <span className="text-xs text-slate-500">{note}</span>}
            </div>
        </section>
    );
}
