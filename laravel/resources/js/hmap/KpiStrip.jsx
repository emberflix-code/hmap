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
            <div className="px-6 py-3 bg-red-50 border-b border-red-200 text-sm text-red-700">
                KPI fetch failed: {error}
            </div>
        );
    }

    const k = data || {};
    const yoy = k.cases_prior_year > 0
        ? Math.round(((k.cases_this_week - k.cases_prior_year) / k.cases_prior_year) * 100)
        : null;

    return (
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-center gap-6 text-sm">
            <Kpi
                label="EWARN alerts"
                value={k.alerts_this_week ?? '—'}
                hint="Barangays exceeding mean + 2σ this week"
                tone={k.alerts_this_week > 0 ? 'red' : 'green'}
            />
            <Kpi
                label="Cases this week"
                value={k.cases_this_week ?? '—'}
                hint="Confirmed + Probable, all barangays"
            />
            <Kpi
                label="Cases YTD"
                value={k.cases_ytd ?? '—'}
                hint={`Through morbidity week ${week} of ${year}`}
            />
            <Kpi
                label="Same week, prior year"
                value={k.cases_prior_year ?? '—'}
                hint={yoy != null ? `YoY: ${yoy > 0 ? '+' : ''}${yoy}%` : 'no baseline'}
                tone={yoy != null && yoy > 50 ? 'amber' : null}
            />
        </div>
    );
}

function Kpi({ label, value, hint, tone }) {
    const toneClass =
        tone === 'red' ? 'text-rose-700'
        : tone === 'amber' ? 'text-amber-700'
        : tone === 'green' ? 'text-emerald-700'
        : 'text-slate-800';
    return (
        <div className="flex flex-col">
            <span className="text-xs text-slate-500 uppercase tracking-wide">{label}</span>
            <span className={`text-2xl font-semibold ${toneClass} leading-tight`}>{value}</span>
            <span className="text-xs text-slate-400 mt-0.5">{hint}</span>
        </div>
    );
}
