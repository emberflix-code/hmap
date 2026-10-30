import React, { useEffect, useMemo, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend as ChartLegend,
    Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { chartOptions, Legend } from './chartTheme.jsx';
import { useIsDark } from './theme.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    ChartLegend,
    Filler
);

const SHORT_DATE = { month: 'short', day: 'numeric' };
const FORECAST = '#0d9488';
const BAND = 'rgba(13, 148, 136, 0.14)';
const forecastOptions = (dark) => chartOptions('Morbidity week', 'Predicted cases', (items) => items[0].label.join(' · '), dark);

// Same rule as the risk tiers' "rising forecast" (ml/main.py is_rising),
// mirrored for falling.
function direction(first, last) {
    if (last >= first * 1.1 && last - first >= 1) {
        return { key: 'rising', label: 'Rising', cls: 'bg-red-50 text-red-700', rot: '' };
    }
    if (first >= last * 1.1 && first - last >= 1) {
        return { key: 'falling', label: 'Falling', cls: 'bg-emerald-50 text-emerald-700', rot: 'rotate-180' };
    }
    return { key: 'steady', label: 'Steady', cls: 'bg-slate-100 text-slate-700', rot: '' };
}

function Stat({ label, children }) {
    return (
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 px-4 py-3">
            <div className="text-[11px] font-medium text-slate-500 mb-1">{label}</div>
            {children}
        </div>
    );
}

function Note({ tone, children }) {
    const cls = tone === 'warn'
        ? 'bg-amber-50 border-amber-200 text-amber-800'
        : 'bg-blue-50 border-blue-200 text-blue-800';
    return (
        <div className={'flex gap-2 items-start text-xs border rounded-lg px-3 py-2 ' + cls}>
            <svg viewBox="0 0 24 24" className="h-4 w-4 mt-px shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v4h1" />
            </svg>
            <span>{children}</span>
        </div>
    );
}

// '2026-11-02' -> 'Nov 2 - Nov 8'
function weekRange(isoMonday) {
    const start = new Date(`${isoMonday}T00:00:00`);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return `${start.toLocaleDateString('en-US', SHORT_DATE)} - ${end.toLocaleDateString('en-US', SHORT_DATE)}`;
}

// ISO week of a Monday date, the numbering the models are trained on
function isoWeek(isoMonday) {
    const d = new Date(`${isoMonday}T00:00:00Z`);
    d.setUTCDate(d.getUTCDate() + 3);  // Thursday of the same week
    const jan1 = Date.UTC(d.getUTCFullYear(), 0, 1);
    return { year: d.getUTCFullYear(), week: Math.ceil(((d - jan1) / 86400000 + 1) / 7) };
}

export default function ForecastPanel({ api, disease, year, week }) {
    const dark = useIsDark();
    const options = useMemo(() => forecastOptions(dark), [dark]);
    const [forecast, setForecast] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        api.post('/ml/forecast', { disease_code: disease, weeks_ahead: 4 })
            .then((r) => !cancelled && setForecast(r.data))
            .catch((err) => !cancelled && setError(err.response?.data?.detail || err.message))
            .finally(() => !cancelled && setLoading(false));
        return () => { cancelled = true; };
    }, [api, disease]);

    const chartData = useMemo(() => {
        if (!forecast) return null;
        // "MW45" with the week's dates underneath (Monday to Sunday)
        const labels = forecast.points.map((p) => [`MW${p.morbidity_week}`, weekRange(p.week_start)]);
        return {
            labels,
            datasets: [
                {
                    label: 'Upper 80% bound',
                    data: forecast.points.map((p) => p.upper_bound),
                    borderColor: 'transparent',
                    backgroundColor: BAND,
                    fill: '+2',
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    tension: 0.3,
                },
                {
                    label: 'Predicted cases',
                    data: forecast.points.map((p) => p.predicted_cases),
                    borderColor: FORECAST,
                    backgroundColor: FORECAST,
                    pointBackgroundColor: FORECAST,
                    pointBorderColor: dark ? '#111a2e' : '#ffffff',
                    pointBorderWidth: 2,
                    borderWidth: 2.5,
                    fill: false,
                    pointRadius: 5,
                    pointHoverRadius: 6,
                    tension: 0.3,
                },
                {
                    label: 'Lower 80% bound',
                    data: forecast.points.map((p) => p.lower_bound),
                    borderColor: 'transparent',
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    tension: 0.3,
                },
            ],
        };
    }, [forecast, dark]);

    if (loading) {
        return <div className="p-4 text-sm text-slate-500">Generating forecast…</div>;
    }
    if (error) {
        // A withheld forecast (model did not beat the same-week-last-year
        // comparison) is expected behavior, so it is shown as a note, not an error.
        const withheld = typeof error === 'string' && error.startsWith('Forecast not displayed');
        return withheld
            ? <div className="p-4 text-sm text-slate-600 bg-slate-50">{error}</div>
            : <div className="p-4 text-sm text-red-700 bg-red-50">{error}</div>;
    }
    if (!forecast || !chartData) {
        return null;
    }
    const first = forecast.points[0];
    const last = forecast.points[forecast.points.length - 1];
    const tail = isoWeek(forecast.training_tail_week);
    // The forecast always starts from today, whatever week the filters show.
    const anchor = new Date(`${forecast.forecast_anchor_week}T00:00:00Z`);
    anchor.setUTCDate(anchor.getUTCDate() - 7);
    const current = isoWeek(anchor.toISOString().slice(0, 10));
    const otherWeekSelected = year !== undefined
        && (Number(year) !== current.year || Number(week) !== current.week);

    const trend = direction(first.predicted_cases, last.predicted_cases);
    const r1 = (n) => Math.round(n).toLocaleString('en-US');

    return (
        <div className="p-5 h-full flex flex-col gap-4">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 flex-1">
                <div className="flex flex-col gap-3">
                    <Stat label={`Next week (MW${first.morbidity_week})`}>
                        <span className="text-3xl font-semibold tracking-tight tabular-nums text-slate-900">{r1(first.predicted_cases)}</span>
                        <span className="ml-1.5 text-sm text-slate-500">cases</span>
                        <div className="text-xs text-slate-500 mt-0.5 tabular-nums">likely {r1(first.lower_bound)} to {r1(first.upper_bound)}</div>
                    </Stat>
                    <Stat label={`Four-week direction (to MW${last.morbidity_week})`}>
                        <span className={'inline-flex items-center gap-1 px-2 py-1 rounded-md text-sm font-semibold ' + trend.cls}>
                            <svg viewBox="0 0 12 12" className={'h-3.5 w-3.5 ' + trend.rot} fill="currentColor" aria-hidden="true">
                                {trend.key === 'steady' ? <rect x="1" y="5" width="10" height="2" rx="1" /> : <path d="M6 2 10 8H2z" />}
                            </svg>
                            {trend.label}
                        </span>
                        <div className="text-xs text-slate-500 mt-1 tabular-nums">{r1(first.predicted_cases)} to {r1(last.predicted_cases)} cases per week</div>
                    </Stat>
                    <Stat label="Validation error (MAPE)">
                        <span className="text-lg font-semibold tabular-nums text-slate-900">{forecast.validation_mape?.toFixed(1) ?? 'n/a'}%</span>
                        <div className="text-xs text-slate-500 mt-0.5">On 2024-2025 weeks withheld from the model; lower than the same-week-last-year comparison</div>
                    </Stat>
                </div>
                <div className="lg:col-span-3 flex flex-col">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                        <Legend items={[
                            { label: 'Predicted cases', line: FORECAST },
                            { label: '80% likely range', band: BAND },
                        ]} />
                        <span className="text-xs text-slate-500">
                            MW{first.morbidity_week} to MW{last.morbidity_week}, {last.morbidity_year}
                            {forecast.barangay_name && <> · {forecast.barangay_name}</>}
                        </span>
                    </div>
                    <div className="flex-1 min-h-[240px]">
                        <Line data={chartData} options={options} />
                    </div>
                </div>
            </div>
            {(otherWeekSelected || forecast.weeks_bridged > 0) && (
                <div className="flex flex-col gap-2">
                    {otherWeekSelected && (
                        <Note tone="info">
                            This forecast is counted from the current week, not from MW{week} of {year} selected above.
                            Compare it with the coming {last.morbidity_year} reports, not with the {year} chart.
                        </Note>
                    )}
                    {forecast.weeks_bridged > 0 && (
                        <Note tone="warn">
                            The model was trained on cases up to MW{tail.week} {tail.year}, {forecast.weeks_bridged} weeks
                            before this forecast. Retrain it with the latest PIDSR data for a forecast that reflects recent weeks.
                        </Note>
                    )}
                </div>
            )}
            <p className="text-[11px] text-slate-400">
                AI-generated forecast. Decision-support indicator only; epidemiological judgment required for public health action.
            </p>
        </div>
    );
}
