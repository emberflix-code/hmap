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

export default function ForecastPanel({ api, disease }) {
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
        const labels = forecast.points.map((p) => p.week_start);
        return {
            labels,
            datasets: [
                {
                    label: 'Upper 80% bound',
                    data: forecast.points.map((p) => p.upper_bound),
                    borderColor: 'rgba(37, 99, 235, 0.25)',
                    backgroundColor: 'rgba(37, 99, 235, 0.10)',
                    borderWidth: 1,
                    fill: '+1',
                    pointRadius: 0,
                    tension: 0.2,
                },
                {
                    label: 'Predicted cases',
                    data: forecast.points.map((p) => p.predicted_cases),
                    borderColor: '#2563eb',
                    backgroundColor: '#2563eb',
                    borderWidth: 2.5,
                    fill: false,
                    pointRadius: 4,
                    tension: 0.2,
                },
                {
                    label: 'Lower 80% bound',
                    data: forecast.points.map((p) => p.lower_bound),
                    borderColor: 'rgba(37, 99, 235, 0.25)',
                    borderWidth: 1,
                    fill: false,
                    pointRadius: 0,
                    tension: 0.2,
                },
            ],
        };
    }, [forecast]);

    if (loading) {
        return <div className="p-4 text-sm text-slate-500">Generating forecast…</div>;
    }
    if (error) {
        return <div className="p-4 text-sm text-red-700 bg-red-50">{error}</div>;
    }
    if (!forecast || !chartData) {
        return null;
    }

    return (
        <div className="p-4 h-full flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs text-slate-600">
                <div>
                    Resolution: <b>{forecast.resolution}</b>
                    {forecast.barangay_name && <> · barangay: <b>{forecast.barangay_name}</b></>}
                </div>
                <div>
                    Validation MAPE: <b>{forecast.validation_mape?.toFixed(1) ?? 'n/a'}%</b>
                </div>
            </div>
            <div className="flex-1 min-h-[260px]">
                <Line
                    data={chartData}
                    options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            x: { title: { display: true, text: 'Week start' } },
                            y: { title: { display: true, text: 'Predicted cases' }, beginAtZero: true },
                        },
                        plugins: {
                            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                            tooltip: { intersect: false },
                        },
                    }}
                />
            </div>
            <p className="mt-2 text-xs text-slate-500 italic">
                AI-generated forecast. Decision-support indicator only; epidemiological judgment required for public health action.
            </p>
        </div>
    );
}
