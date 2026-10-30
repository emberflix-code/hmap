import React, { useEffect, useMemo, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    LineController,
    BarController,
    Title,
    Tooltip,
    Legend as ChartLegend,
    Filler,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { C, areaFill, chartOptions, Legend } from './chartTheme.jsx';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    LineController,
    BarController,
    Title,
    Tooltip,
    ChartLegend,
    Filler
);

const VIEW_KEY = 'hmap.trend.view';

function readView() {
    try { return window.localStorage.getItem(VIEW_KEY) === 'histogram' ? 'histogram' : 'line'; } catch (_) { return 'line'; }
}

/** Line / Histogram choice, remembered per browser. */
export function useTrendView() {
    const [view, setView] = useState(readView);
    const changeView = (v) => {
        setView(v);
        try { window.localStorage.setItem(VIEW_KEY, v); } catch (_) { /* private mode */ }
    };
    return [view, changeView];
}

export function ChartTypeToggle({ view, onChange }) {
    return (
        <div className="inline-flex p-0.5 rounded-lg bg-slate-100" role="group" aria-label="Chart type">
            {[['line', 'Line', LINE_ICON], ['histogram', 'Histogram', BAR_ICON]].map(([v, label, icon]) => (
                <button
                    key={v}
                    type="button"
                    aria-pressed={view === v}
                    onClick={() => onChange(v)}
                    className={'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ' +
                        (view === v ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800')}
                >
                    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">{icon}</svg>
                    {label}
                </button>
            ))}
        </div>
    );
}

// 'histogram' draws the weekly cases as touching bars (the epidemic curve CESU
// asked for); the PIDSR threshold lines stay on top in both views.
export default function TrendChartPanel({ api, disease, year, view = 'line' }) {
    const [series, setSeries] = useState([]);
    const [thresholds, setThresholds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);

        Promise.all([
            api.get('/weekly-series', {
                params: {
                    disease_code: disease,
                    year_start: year,
                    year_end: year,
                },
            }),
            api.get('/thresholds', {
                params: { disease_code: disease },
            }),
        ])
            .then(([s, t]) => {
                if (cancelled) return;
                setSeries(s.data || []);
                setThresholds(t.data || []);
            })
            .catch((err) => {
                if (cancelled) return;
                setError(err.response?.data?.detail || err.message);
            })
            .finally(() => !cancelled && setLoading(false));

        return () => {
            cancelled = true;
        };
    }, [api, disease, year]);

    const chartData = useMemo(() => {
        // X axis is morbidity weeks 1..53
        const labels = Array.from({ length: 53 }, (_, i) => i + 1);
        const seriesByWeek = Object.fromEntries(series.map((r) => [Number(r.week), Number(r.cases)]));
        const meanByWeek = Object.fromEntries(thresholds.map((t) => [Number(t.morbidity_week), Number(t.mean_cases)]));
        const alertByWeek = Object.fromEntries(thresholds.map((t) => [Number(t.morbidity_week), Number(t.alert_threshold)]));
        const thrByWeek = Object.fromEntries(thresholds.map((t) => [Number(t.morbidity_week), Number(t.threshold_value)]));
        const singleCase = thresholds.some((t) => Number(t.single_case_trigger) === 1);
        const counts = labels.map((w) => seriesByWeek[w] ?? 0);

        // PIDSR levels (DOH, 2014, pp. 57-58): red above the epidemic threshold
        // or any case of a single-case disease, amber above the alert threshold.
        const levelColor = (n, w) => {
            if (singleCase) return n > 0 ? C.epidemic : C.normal;
            if (thrByWeek[w] !== undefined && n > thrByWeek[w]) return C.epidemic;
            if (alertByWeek[w] !== undefined && n > alertByWeek[w]) return C.alert;
            return C.normal;
        };
        const pointColors = counts.map((n, i) => levelColor(n, labels[i]));
        const casesLabel = singleCase ? `${year} cases (any case = alert)` : `${year} cases`;
        const cases = view === 'histogram'
            ? {
                // Epidemic curve: one bar per morbidity week, touching (no gaps),
                // coloured by PIDSR level.
                type: 'bar',
                label: casesLabel,
                data: counts,
                backgroundColor: pointColors,
                hoverBackgroundColor: pointColors.map((c) => c + 'cc'),
                borderColor: pointColors,
                borderWidth: 0.5,   // same colour as the bar: closes anti-aliasing seams
                barPercentage: 1.0,
                categoryPercentage: 1.0,
                borderRadius: 0,
                order: 2,
            }
            : {
                type: 'line',
                label: casesLabel,
                data: counts,
                borderColor: C.normal,
                backgroundColor: (ctx) => areaFill(ctx, C.normal),
                pointBackgroundColor: pointColors,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5,
                borderWidth: 2,
                fill: true,
                cubicInterpolationMode: 'monotone',   // smooth without dipping below zero
                pointRadius: counts.map((n, i) => (pointColors[i] === C.normal ? 0 : 4)),
                pointHoverRadius: 5,
                order: 2,
            };

        return {
            labels,
            datasets: [
                cases,
                {
                    type: 'line',
                    order: 1,
                    label: '5-year mean',
                    data: labels.map((w) => meanByWeek[w] ?? null),
                    borderColor: C.mean,
                    borderWidth: 1.5,
                    borderDash: [3, 3],
                    fill: false,
                    stepped: view === 'histogram' ? 'middle' : false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                },
                {
                    type: 'line',
                    order: 1,
                    label: 'Alert threshold (mean + 1 SD)',
                    data: labels.map((w) => alertByWeek[w] ?? null),
                    borderColor: C.alertLine,
                    borderWidth: 2,
                    borderDash: [6, 4],
                    fill: false,
                    stepped: view === 'histogram' ? 'middle' : false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    hidden: singleCase,
                },
                {
                    type: 'line',
                    order: 1,
                    label: 'Epidemic threshold (mean + 2 SD)',
                    data: labels.map((w) => thrByWeek[w] ?? null),
                    borderColor: C.epidemicLine,
                    borderWidth: 2,
                    fill: false,
                    stepped: view === 'histogram' ? 'middle' : false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    hidden: singleCase,
                },
            ],
        };
    }, [series, thresholds, year, view]);

    const options = useMemo(() => chartOptions('Morbidity week', 'Cases (Confirmed + Probable)', (items) => `Morbidity week ${items[0].label}`), []);
    const singleCase = thresholds.some((t) => Number(t.single_case_trigger) === 1);

    if (error) {
        return <div className="p-4 text-sm text-red-700 bg-red-50">{error}</div>;
    }

    return (
        <div className="relative h-full px-5 pt-4 pb-3 flex flex-col">
            <div className="flex flex-wrap items-center gap-3 mb-3">
                <Legend
                    items={[
                        { label: 'Below alert', swatch: C.normal },
                        { label: 'Above alert', swatch: C.alert },
                        { label: 'Above epidemic', swatch: C.epidemic },
                        ...(singleCase ? [] : [
                            { label: 'Alert threshold', line: C.alertLine, dash: true },
                            { label: 'Epidemic threshold', line: C.epidemicLine },
                        ]),
                        { label: '5-year mean', line: C.mean, dash: true },
                    ]}
                />
                {loading && <span className="ml-auto text-xs text-slate-400">Loading…</span>}
            </div>
            <div className="flex-1 min-h-[300px]">
                <Chart type="bar" data={chartData} options={options} />
            </div>
        </div>
    );
}

const LINE_ICON = <path d="M1.5 12 6 7l3 3 5.5-6" strokeLinecap="round" strokeLinejoin="round" />;
const BAR_ICON = <path d="M2 14V8h3v6M6.5 14V4h3v10M11 14V6h3v8" strokeLinejoin="round" />;
