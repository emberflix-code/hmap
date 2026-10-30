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
    Legend,
    Filler,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';

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
    Legend,
    Filler
);

const VIEW_KEY = 'hmap.trend.view';

function readView() {
    try { return window.localStorage.getItem(VIEW_KEY) === 'histogram' ? 'histogram' : 'line'; } catch (_) { return 'line'; }
}

export default function TrendChartPanel({ api, disease, year }) {
    // 'histogram' draws the weekly cases as bars (the epidemic curve CESU asked
    // for); the PIDSR threshold lines stay on top in both views.
    const [view, setView] = useState(readView);
    const changeView = (v) => {
        setView(v);
        try { window.localStorage.setItem(VIEW_KEY, v); } catch (_) { /* private mode */ }
    };
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
            if (singleCase) return n > 0 ? '#dc2626' : '#2563eb';
            if (thrByWeek[w] !== undefined && n > thrByWeek[w]) return '#dc2626';
            if (alertByWeek[w] !== undefined && n > alertByWeek[w]) return '#f59e0b';
            return '#2563eb';
        };
        const pointColors = counts.map((n, i) => levelColor(n, labels[i]));
        const casesLabel = singleCase ? `${year} cases (any case = alert)` : `${year} cases`;
        const cases = view === 'histogram'
            ? {
                // epidemic curve: one bar per morbidity week, coloured by PIDSR level
                type: 'bar',
                label: casesLabel,
                data: counts,
                backgroundColor: pointColors.map((c) => (c === '#2563eb' ? 'rgba(37, 99, 235, 0.75)' : c)),
                borderColor: 'rgba(255, 255, 255, 0.9)',
                borderWidth: 1,
                barPercentage: 1.0,
                categoryPercentage: 0.95,
                order: 2,
            }
            : {
                type: 'line',
                label: casesLabel,
                data: counts,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.15)',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                borderWidth: 2,
                fill: true,
                tension: 0.25,
                pointRadius: counts.map((n, i) => (pointColors[i] === '#2563eb' ? 2 : 4)),
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
                    borderColor: '#64748b',
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
                    borderColor: '#f59e0b',
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
                    borderColor: '#dc2626',
                    borderWidth: 1.5,
                    borderDash: [2, 4],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    hidden: singleCase,
                },
            ],
        };
    }, [series, thresholds, year, view]);

    const options = useMemo(
        () => ({
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: { title: { display: true, text: 'Morbidity week' } },
                y: { title: { display: true, text: 'Cases' }, beginAtZero: true },
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: { intersect: false },
            },
        }),
        []
    );

    if (error) {
        return <div className="p-4 text-sm text-red-700 bg-red-50">{error}</div>;
    }

    return (
        <div className="relative h-full p-4 flex flex-col">
            <div className="flex items-center justify-end gap-2 mb-2 text-xs">
                {loading && <span className="text-slate-500">loading…</span>}
                <div className="inline-flex rounded border border-slate-300 overflow-hidden" role="group" aria-label="Chart type">
                    {[['line', 'Line'], ['histogram', 'Histogram']].map(([v, label]) => (
                        <button
                            key={v}
                            type="button"
                            aria-pressed={view === v}
                            onClick={() => changeView(v)}
                            className={'px-2.5 py-1 ' + (view === v ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50')}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex-1 min-h-[300px]">
                <Chart type="bar" data={chartData} options={options} />
            </div>
        </div>
    );
}
