import React, { useEffect, useState } from 'react';

export default function KpiStrip({ api, disease, year, week }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        setError(null);
        api.get('/summary', {
            params: {
                disease_code: disease,
                morbidity_year: year,
                morbidity_week: week,
            },
        })
            .then((r) => !cancelled && setData(r.data))
            .catch((err) => !cancelled && setError(err.response?.data?.detail || err.message));
        return () => { cancelled = true; };
    }, [api, disease, year, week]);

    if (error) {
        return (
            <div className="mx-6 mt-5 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
                KPI fetch failed: {error}
            </div>
        );
    }

    const k = data || {};
    const yoy = k.cases_prior_year > 0
        ? Math.round(((k.cases_this_week - k.cases_prior_year) / k.cases_prior_year) * 100)
        : null;
    const alerts = k.alerts_this_week;

    return (
        <div className="px-6 pt-5 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <Kpi
                label="PIDSR alerts"
                value={alerts ?? '—'}
                hint="Barangays above their epidemic threshold, or with a single-case alert disease, this week"
                tone={alerts > 0 ? 'red' : alerts === 0 ? 'green' : null}
                icon={<path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />}
                badge={alerts > 0 ? 'Action needed' : alerts === 0 ? 'No alerts' : null}
            />
            <Kpi
                label="Cases this week"
                value={fmt(k.cases_this_week)}
                hint={`Confirmed + Probable, all barangays, MW${week} ${year}`}
                icon={<path d="M3 3v18h18M7 15l4-4 3 3 5-6" />}
                delta={yoy}
            />
            <Kpi
                label="Cases year to date"
                value={fmt(k.cases_ytd)}
                hint={`Morbidity weeks 1 to ${week} of ${year}`}
                icon={<><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>}
            />
            <Kpi
                label="Same week, prior year"
                value={fmt(k.cases_prior_year)}
                hint={`MW${week} of ${year - 1}, for comparison`}
                icon={<path d="M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5M12 7v5l3 2" />}
            />
        </div>
    );
}

function fmt(n) {
    return n == null ? '—' : Number(n).toLocaleString('en-US');
}

const TONES = {
    red: { value: 'text-red-700', icon: 'bg-red-50 text-red-600', badge: 'bg-red-50 text-red-700 ring-red-600/20', bar: 'before:bg-red-500' },
    green: { value: 'text-emerald-700', icon: 'bg-emerald-50 text-emerald-600', badge: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', bar: 'before:bg-emerald-500' },
    none: { value: 'text-slate-900', icon: 'bg-blue-50 text-blue-600', badge: '', bar: 'before:bg-transparent' },
};

function Kpi({ label, value, hint, tone, icon, badge, delta }) {
    const t = TONES[tone] || TONES.none;
    return (
        <div className={`relative bg-white rounded-xl border border-slate-200 shadow-sm p-4 overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 ${t.bar}`}>
            <div className="flex items-start justify-between gap-3">
                <span className="text-xs font-medium text-slate-500">{label}</span>
                <span className={`h-8 w-8 rounded-lg flex items-center justify-center ${t.icon}`} aria-hidden="true">
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{icon}</svg>
                </span>
            </div>
            <div className="mt-1 flex items-baseline gap-2">
                <span className={`text-3xl font-semibold tracking-tight tabular-nums ${t.value}`}>{value}</span>
                {badge && <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ring-1 ring-inset ${t.badge}`}>{badge}</span>}
                {delta != null && <Delta pct={delta} />}
            </div>
            <p className="mt-1 text-xs text-slate-500 leading-snug">{hint}</p>
        </div>
    );
}

// Change against the same week of the prior year; a rise in cases is shown in red.
function Delta({ pct }) {
    const up = pct > 0;
    const cls = pct === 0 ? 'bg-slate-100 text-slate-600' : up ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700';
    return (
        <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[11px] font-semibold tabular-nums ${cls}`}
              title="Compared with the same week of the prior year">
            {pct !== 0 && (
                <svg viewBox="0 0 12 12" className={`h-3 w-3 ${up ? '' : 'rotate-180'}`} fill="currentColor" aria-hidden="true"><path d="M6 2 10 8H2z" /></svg>
            )}
            {Math.abs(pct)}% vs last year
        </span>
    );
}
