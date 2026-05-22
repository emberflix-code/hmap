import React, { useMemo, useState } from 'react';

import HeatMapPanel from './HeatMapPanel.jsx';
import TrendChartPanel from './TrendChartPanel.jsx';
import ForecastPanel from './ForecastPanel.jsx';
import KpiStrip from './KpiStrip.jsx';

export default function Dashboard({ api, diseases, barangays }) {
    const today = useMemo(() => isoMorbidityWeek(new Date()), []);
    const [disease, setDisease] = useState('DENGUE');
    const [year, setYear] = useState(today.year);
    const [week, setWeek] = useState(today.week);

    const forecastEnabled = useMemo(
        () => diseases.find((d) => d.disease_code === disease)?.forecast_enabled === 1,
        [diseases, disease]
    );

    return (
        <>
            <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-end gap-4">
                <FieldSelect
                    label="Disease"
                    value={disease}
                    onChange={setDisease}
                    options={diseases.map((d) => ({ value: d.disease_code, label: d.disease_name }))}
                />
                <FieldNumber label="Year" value={year} min={2010} max={2026} onChange={setYear} />
                <FieldNumber label="Morbidity week" value={week} min={1} max={53} onChange={setWeek} />
                <div className="ml-auto text-xs text-slate-500">
                    {forecastEnabled
                        ? 'Forecast available (Prophet)'
                        : 'Forecast unavailable for this disease'}
                </div>
            </div>

            <KpiStrip api={api} disease={disease} year={year} week={week} />

            <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Panel title="Geographic distribution" subtitle={`Week ${week} of ${year}`}>
                    <HeatMapPanel
                        api={api}
                        disease={disease}
                        year={year}
                        week={week}
                        barangays={barangays}
                    />
                </Panel>

                <Panel title="Disease trend with EWARN threshold" subtitle={`${disease}, year ${year}`}>
                    <TrendChartPanel api={api} disease={disease} year={year} />
                </Panel>

                <Panel
                    title="AI four-week forecast (Prophet)"
                    subtitle={forecastEnabled ? 'City-wide' : 'Not enabled for this disease'}
                    span={2}
                >
                    {forecastEnabled ? (
                        <ForecastPanel api={api} disease={disease} />
                    ) : (
                        <div className="text-sm text-slate-500 p-4">
                            Prophet forecasting is enabled only for diseases with sufficient
                            historical signal. See <code>docs/prophet.md</code>.
                        </div>
                    )}
                </Panel>
            </main>

            <footer className="text-center text-xs text-slate-400 py-3 border-t border-slate-200 bg-white">
                H-MAP · Parañaque City CESU · data through morbidity week {week} of {year}
            </footer>
        </>
    );
}

function Panel({ title, subtitle, children, span }) {
    return (
        <section
            className={
                'bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex flex-col ' +
                (span === 2 ? 'lg:col-span-2' : '')
            }
        >
            <div className="px-4 py-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
                {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
            </div>
            <div className="flex-1 min-h-[360px]">{children}</div>
        </section>
    );
}

function FieldSelect({ label, value, onChange, options }) {
    return (
        <label className="flex flex-col text-xs text-slate-600">
            <span className="mb-1">{label}</span>
            <select
                className="border border-slate-300 rounded px-2 py-1.5 text-sm text-slate-800 bg-white"
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
        <label className="flex flex-col text-xs text-slate-600">
            <span className="mb-1">{label}</span>
            <input
                type="number"
                className="border border-slate-300 rounded px-2 py-1.5 text-sm text-slate-800 bg-white w-24"
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
