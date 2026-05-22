import React, { useEffect, useMemo, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

export default function TrendChartPanel({ api, disease, year }) {
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
        const thrByWeek = Object.fromEntries(thresholds.map((t) => [Number(t.morbidity_week), Number(t.threshold_value)]));
        return {
            labels,
            datasets: [
                {
                    label: `${year} cases`,
                    data: labels.map((w) => seriesByWeek[w] ?? 0),
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.15)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.25,
                    pointRadius: 2,
                },
                {
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
                    label: 'EWARN threshold (μ + 2σ)',
                    data: labels.map((w) => thrByWeek[w] ?? null),
                    borderColor: '#dc2626',
                    borderWidth: 1.5,
                    borderDash: [2, 4],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                },
            ],
        };
    }, [series, thresholds, year]);

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
        <div className="relative h-full p-4">
            {loading && (
                <div className="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-white/90 border border-slate-200 text-slate-600">
                    loading…
                </div>
            )}
            <Line data={chartData} options={options} />
        </div>
    );
}
