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
import { chartOptions } from './chartTheme.jsx';
import { useIsDark } from './theme.js';

// PIDSR level colours (previous design)
const C = { normal: '#2563eb', alert: '#f59e0b', epidemic: '#dc2626', mean: '#64748b' };

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
        <div className="inline-flex rounded-md border border-slate-300 overflow-hidden text-xs" role="group" aria-label="Chart type">
            {[['line', 'Line', LINE_ICON], ['histogram', 'Histogram', BAR_ICON]].map(([v, label, icon]) => (
                <button
                    key={v}
                    type="button"
                    aria-pressed={view === v}
                    onClick={() => onChange(v)}
                    className={'inline-flex items-center gap-1.5 px-2.5 py-1 font-medium ' +
                        (view === v ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50')}
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
    const dark = useIsDark();
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
                // Epidemic curve: one bar per morbidity week, coloured by PIDSR
                // level, separated by a hairline in the panel colour.
                type: 'bar',
                label: casesLabel,
                data: counts,
                backgroundColor: pointColors.map((c) => (c === C.normal ? 'rgba(37, 99, 235, 0.75)' : c)),
                borderColor: dark ? '#111a2e' : 'rgba(255, 255, 255, 0.9)',
                borderWidth: 1,
                barPercentage: 1.0,
                categoryPercentage: 0.95,
                order: 2,
            }
            : {
                type: 'line',
                label: casesLabel,
                data: counts,
                borderColor: C.normal,
                backgroundColor: dark ? 'rgba(59, 130, 246, 0.18)' : 'rgba(37, 99, 235, 0.15)',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                borderWidth: 2,
                fill: true,
                cubicInterpolationMode: 'monotone',   // smooth without dipping below zero
                pointRadius: counts.map((n, i) => (pointColors[i] === C.normal ? 2 : 4)),
                order: 2,
            };

        return {
            labels,
            datasets: [
                cases,
                {
                    type: 'line',
                    order: 1,
                    label: '5-yr mean',
                    data: labels.map((w) => meanByWeek[w] ?? null),
                    borderColor: dark ? '#94a3b8' : C.mean,
                    borderWidth: 1.5,
                    borderDash: [4, 3],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                },
                {
                    type: 'line',
                    order: 1,
                    label: 'PIDSR alert threshold (mean + 1 SD)',
                    data: labels.map((w) => alertByWeek[w] ?? null),
                    borderColor: C.alert,
                    borderWidth: 1.5,
                    borderDash: [6, 3],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    hidden: singleCase,
                },
                {
                    type: 'line',
                    order: 1,
                    label: 'PIDSR epidemic threshold (mean + 2 SD)',
                    data: labels.map((w) => thrByWeek[w] ?? null),
                    borderColor: dark ? '#f87171' : C.epidemic,
                    borderWidth: 1.5,
                    borderDash: [2, 4],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    hidden: singleCase,
                },
            ],
        };
    }, [series, thresholds, year, view, dark]);

    const options = useMemo(() => {
        const o = chartOptions('Morbidity week', 'Cases', (items) => `Morbidity week ${items[0].label}`, dark);
        o.scales.x.offset = true;
        o.scales.x.grid = { display: true, color: dark ? '#1c2942' : '#eef2f6' };
        o.scales.x.ticks = { ...o.scales.x.ticks, autoSkip: true, maxRotation: 45, minRotation: 45 };
        o.plugins.legend = {
            display: true,
            position: 'bottom',
            labels: {
                boxWidth: 12,
                font: { size: 11 },
                color: dark ? '#a8b4c7' : '#475569',
                // The bar series has one colour per week; its legend box shows the
                // "below alert" blue instead of the first week's colour.
                generateLabels: (chart) => ChartJS.defaults.plugins.legend.labels.generateLabels(chart).map((l) =>
                    l.datasetIndex === 0 ? { ...l, fillStyle: 'rgba(37, 99, 235, 0.75)', strokeStyle: C.normal } : l),
            },
        };
        return o;
    }, [dark]);

    if (error) {
        return <div className="p-4 text-sm text-red-700 bg-red-50">{error}</div>;
    }

    return (
        <div className="relative h-full px-5 pt-3 pb-3 flex flex-col">
            {loading && <span className="absolute right-5 top-3 text-xs text-slate-400">Loading…</span>}
            <div className="flex-1 min-h-[330px]">
                <Chart type="bar" data={chartData} options={options} />
            </div>
        </div>
    );
}

const LINE_ICON = <path d="M1.5 12 6 7l3 3 5.5-6" strokeLinecap="round" strokeLinejoin="round" />;
const BAR_ICON = <path d="M2 14V8h3v6M6.5 14V4h3v10M11 14V6h3v8" strokeLinejoin="round" />;
