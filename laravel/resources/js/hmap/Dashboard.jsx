import React, { useMemo, useState } from 'react';

import HeatMapPanel from './HeatMapPanel.jsx';
import TrendChartPanel, { ChartTypeToggle, useTrendView } from './TrendChartPanel.jsx';
import ForecastPanel from './ForecastPanel.jsx';
import KpiStrip from './KpiStrip.jsx';
import RecommendationsPanel from './RecommendationsPanel.jsx';

export default function Dashboard({ api, diseases, barangays, whoami }) {
    const canSeeRecommendations = whoami?.role === 'Analyst' || whoami?.role === 'Administrator';
    const today = useMemo(() => isoMorbidityWeek(new Date()), []);
    const [disease, setDisease] = useState('DENGUE');
    const [year, setYear] = useState(today.year);
    const [week, setWeek] = useState(today.week);

    const [trendView, setTrendView] = useTrendView();
    const diseaseName =diseases.find((d) => d.disease_code === disease)?.disease_name || disease;
    const forecastEnabled = useMemo(
        () => diseases.find((d) => d.disease_code === disease)?.forecast_enabled === 1,
        [diseases, disease]
    );

    return (
        <>
            <div className="px-4 md:px-6 pt-6 flex flex-wrap items-end justify-between gap-4">
                <div>
                    <h2 className="text-xl font-semibold tracking-tight text-slate-900">Surveillance overview</h2>
                    <p className="text-sm text-slate-500 mt-0.5">
                        {diseaseName} · Morbidity week {week} of {year}
                        <span className="text-slate-400"> ({weekRange(year, week)})</span>
                    </p>
                </div>
                <div className="w-full md:w-auto flex flex-wrap items-end gap-3 bg-white border border-slate-200 rounded-xl shadow-sm px-3 py-2.5">
                    <FieldSelect
                        label="Disease"
                        value={disease}
                        onChange={setDisease}
                        options={diseases.map((d) => ({ value: d.disease_code, label: d.disease_name }))}
                    />
                    <FieldNumber label="Year" value={year} min={2010} max={2026} onChange={setYear} />
                    <WeekStepper week={week} onChange={setWeek} />
                    <button
                        type="button"
                        onClick={() => { setYear(today.year); setWeek(today.week); }}
                        className="h-9 px-3 text-xs font-medium rounded-md text-blue-700 hover:bg-blue-50"
                    >
                        Current week
                    </button>
                    <span className={'h-9 inline-flex items-center gap-1.5 px-2.5 rounded-md text-[11px] font-medium ' +
                        (forecastEnabled ? 'bg-teal-50 text-teal-700' : 'bg-slate-100 text-slate-500')}>
                        <span className={'h-1.5 w-1.5 rounded-full ' + (forecastEnabled ? 'bg-teal-500' : 'bg-slate-400')} />
                        {forecastEnabled ? 'Forecast available' : 'No forecast for this disease'}
                    </span>
                </div>
            </div>

            <KpiStrip api={api} disease={disease} year={year} week={week} />

            <main className="flex-1 px-4 md:px-6 py-5 md:py-6 grid grid-cols-1 lg:grid-cols-2 gap-5 min-w-0">
                <Panel title="Geographic distribution" subtitle={`Week ${week} of ${year}`}>
                    <HeatMapPanel
                        api={api}
                        disease={disease}
                        year={year}
                        week={week}
                        barangays={barangays}
                    />
                </Panel>

                <Panel
                    title="Disease trend with PIDSR alert and epidemic thresholds"
                    subtitle={`${diseaseName}, weekly cases in ${year}`}
                    actions={<ChartTypeToggle view={trendView} onChange={setTrendView} />}
                >
                    <TrendChartPanel api={api} disease={disease} year={year} view={trendView} />
                </Panel>

                <Panel
                    title="AI four-week forecast (Prophet)"
                    subtitle={forecastEnabled ? 'City-wide · next 4 morbidity weeks from today' : 'Not enabled for this disease'}
                    span={2}
                >
                    {forecastEnabled ? (
                        <ForecastPanel api={api} disease={disease} year={year} week={week} />
                    ) : (
                        <div className="text-sm text-slate-500 p-5">
                            Forecasts are shown only for diseases with a regular yearly pattern, where the
                            model has proven more accurate than the same week of the previous year. Use the
                            PIDSR thresholds for this disease.
                        </div>
                    )}
                </Panel>

                {canSeeRecommendations && (
                    <Panel
                        title="Recommended response"
                        subtitle={`Moderate and High barangays, ranked, week ${week} of ${year}`}
                        span={2}
                    >
                        <RecommendationsPanel
                            api={api}
                            disease={disease}
                            year={year}
                            week={week}
                            isAdmin={whoami?.role === 'Administrator'}
                        />
                    </Panel>
                )}
            </main>

            <footer className="px-4 md:px-6 py-4 flex flex-wrap justify-between gap-2 text-xs text-slate-400 border-t border-slate-200 bg-white">
                <span>H-MAP · City Epidemiology and Surveillance Unit, City Health Office of Parañaque</span>
                <span>Decision support only. PIDSR thresholds per DOH (2014); outbreak declaration rests with the City Health Officer.</span>
            </footer>
        </>
    );
}

function Panel({ title, subtitle, children, span, actions }) {
    return (
        <section
            className={
                'bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col ' +
                (span === 2 ? 'lg:col-span-2' : '')
            }
        >
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-start justify-between gap-3">
                <div className="min-w-0">
                    <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
                    {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
                </div>
                {actions && <div className="shrink-0">{actions}</div>}
            </div>
            <div className="flex-1 min-h-[360px]">{children}</div>
        </section>
    );
}

const FIELD = 'h-9 border border-slate-300 rounded-md px-2.5 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500';

function WeekStepper({ week, onChange }) {
    const step = (d) => onChange(Math.min(53, Math.max(1, week + d)));
    const btn = 'h-9 w-8 flex items-center justify-center text-slate-500 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-40';
    return (
        <label className="flex flex-col text-[11px] font-medium text-slate-500">
            <span className="mb-1">Morbidity week</span>
            <div className="flex items-stretch border border-slate-300 rounded-md overflow-hidden bg-white focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500">
                <button type="button" className={btn + ' border-r border-slate-200'} onClick={() => step(-1)} disabled={week <= 1} aria-label="Previous week">‹</button>
                <input
                    type="number"
                    className="h-9 w-14 text-center text-sm text-slate-800 tabular-nums focus:outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
                    value={week}
                    min={1}
                    max={53}
                    onChange={(e) => onChange(parseInt(e.target.value || '0', 10))}
                />
                <button type="button" className={btn + ' border-l border-slate-200'} onClick={() => step(1)} disabled={week >= 53} aria-label="Next week">›</button>
            </div>
        </label>
    );
}

// Monday to Sunday of an ISO morbidity week, e.g. "Feb 2 - Feb 8"
function weekRange(year, week) {
    const jan4 = new Date(Date.UTC(year, 0, 4));
    const monday = new Date(jan4);
    monday.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7) + (week - 1) * 7);
    const sunday = new Date(monday);
    sunday.setUTCDate(monday.getUTCDate() + 6);
    const f = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
    return `${f(monday)} - ${f(sunday)}`;
}

function FieldSelect({ label, value, onChange, options }) {
    return (
        <label className="flex flex-col text-[11px] font-medium text-slate-500">
            <span className="mb-1">{label}</span>
            <select
                className={FIELD + ' w-full sm:w-auto sm:min-w-[12rem]'}
                value={value}
                onChange={(e) => onChange(e.target.value)}
            >
                {options.map((o) => (
                    <option key={o.value} value={o.value}>
                        {o.label}
                    </option>
                ))}
            </select>
        </label>
    );
}

function FieldNumber({ label, value, onChange, min, max }) {
    return (
        <label className="flex flex-col text-[11px] font-medium text-slate-500">
            <span className="mb-1">{label}</span>
            <input
                type="number"
                className={FIELD + ' w-24 tabular-nums'}
                value={value}
                min={min}
                max={max}
                onChange={(e) => onChange(parseInt(e.target.value || '0', 10))}
            />
        </label>
    );
}

function isoMorbidityWeek(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
    return { year: d.getUTCFullYear(), week };
}
