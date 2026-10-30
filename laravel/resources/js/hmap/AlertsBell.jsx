import React, { useEffect, useState } from 'react';

const TYPE_LABEL = {
    epidemic_threshold: 'Above epidemic threshold',
    single_case: 'Single-case alert',
    hotspot: 'Active hotspot',
};
const SEEN_KEY = 'hmap.alerts.lastSeenId';

function readSeen() {
    try { return parseInt(window.localStorage.getItem(SEEN_KEY) || '0', 10); } catch (_) { return 0; }
}
function writeSeen(id) {
    try { window.localStorage.setItem(SEEN_KEY, String(id)); } catch (_) { /* private mode */ }
}

/**
 * In-app channel of Module 7: the latest outbreak alerts with their email/SMS
 * delivery status. Refreshes every 5 minutes; the badge counts alerts newer
 * than the last one this browser has seen.
 */
export default function AlertsBell({ api }) {
    const [alerts, setAlerts] = useState([]);
    const [open, setOpen] = useState(false);
    const [seen, setSeen] = useState(readSeen);

    useEffect(() => {
        const load = () => api.get('/notifications').then((r) => setAlerts(r.data)).catch(() => {});
        load();
        const t = setInterval(load, 5 * 60 * 1000);
        return () => clearInterval(t);
    }, [api]);

    const unseen = alerts.filter((a) => a.notification_id > seen).length;

    const toggle = () => {
        if (!open && alerts.length) {
            const newest = Math.max(...alerts.map((a) => a.notification_id));
            writeSeen(newest);
            setSeen(newest);
        }
        setOpen(!open);
    };

    return (
        <div className="relative">
            <button
                type="button"
                onClick={toggle}
                className="relative inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                </svg>
                <span className="sr-only sm:not-sr-only">Alerts</span>
                {unseen > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-red-600 text-white text-[10px] font-semibold leading-none">
                        {unseen}
                    </span>
                )}
            </button>
            {open && (
                <div className="absolute right-0 mt-2 w-[min(26rem,calc(100vw-2rem))] max-h-[28rem] overflow-y-auto bg-white border border-slate-200 rounded-lg shadow-lg z-[1000]">
                    {alerts.length === 0 ? (
                        <div className="p-4 text-sm text-slate-500">No outbreak alerts yet.</div>
                    ) : (
                        alerts.map((a) => (
                            <div key={a.notification_id} className="px-4 py-2.5 border-b border-slate-100 text-xs">
                                <div className="flex justify-between gap-2">
                                    <span className="font-semibold text-slate-800">
                                        {a.disease_code} · {a.barangay_name}
                                    </span>
                                    <span className="text-slate-400">MW {a.morbidity_week} {a.morbidity_year}</span>
                                </div>
                                <div className="text-slate-600 mt-0.5">
                                    {TYPE_LABEL[a.alert_type]} ({a.case_count} case{a.case_count === 1 ? '' : 's'} this week)
                                </div>
                                <div className="text-slate-400 mt-0.5">
                                    {a.created_at}
                                    {Object.entries(a.deliveries).map(([status, n]) => (
                                        <span key={status} className={'ml-2 ' + (status === 'failed' ? 'text-red-600' : '')}>
                                            {n} {status}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
