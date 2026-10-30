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

const SHORT_DATE = { month: 'short', day: 'numeric' };

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

    return (
        <div className="p-4 h-full flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs text-slate-600">
                <div>
                    Next 4 morbidity weeks: <b>MW{first.morbidity_week} to MW{last.morbidity_week}, {last.morbidity_year}</b>
                    {forecast.barangay_name && <> · barangay: <b>{forecast.barangay_name}</b></>}
                </div>
                <div>
                    Validation MAPE: <b>{forecast.validation_mape?.toFixed(1) ?? 'n/a'}%</b>
                </div>
            </div>
            {otherWeekSelected && (
                <p className="mb-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    This forecast is counted from the current week, not from MW{week} of {year} selected above.
                    Compare it with the coming {last.morbidity_year} reports, not with the {year} chart.
                </p>
            )}
            {forecast.weeks_bridged > 0 && (
                <p className="mb-2 text-xs text-amber-700">
                    The model was trained on cases up to MW{tail.week} {tail.year}, {forecast.weeks_bridged} weeks
                    before this forecast. Retrain it with the latest PIDSR data for a forecast that reflects recent weeks.
                </p>
            )}
            <div className="flex-1 min-h-[260px]">
                <Line
                    data={chartData}
                    options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            x: { title: { display: true, text: 'Morbidity week' } },
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
