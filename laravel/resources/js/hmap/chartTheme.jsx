import React from 'react';

/** Shared look for the dashboard charts: quiet grid, dark tooltip, no built-in legend. */
export function chartOptions(xTitle, yTitle, tooltipTitle, dark = false) {
    const tick = { color: dark ? '#8b98ad' : '#64748b', font: { size: 11, family: 'Inter, system-ui, sans-serif' } };
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        interaction: { mode: 'index', intersect: false },
        layout: { padding: { top: 4 } },
        scales: {
            x: {
                offset: true,
                grid: { display: false },
                border: { color: dark ? '#33425e' : '#cbd5e1' },
                ticks: { ...tick, autoSkip: true, maxRotation: 0, autoSkipPadding: 12 },
                title: { display: true, text: xTitle, ...tick, font: { ...tick.font, weight: '500' } },
            },
            y: {
                beginAtZero: true,
                grace: '8%',
                grid: { color: dark ? '#1c2942' : '#eef2f6' },
                border: { display: false },
                ticks: { ...tick, precision: 0, padding: 6 },
                title: { display: true, text: yTitle, ...tick, font: { ...tick.font, weight: '500' } },
            },
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: dark ? '#020617' : '#0f172a',
                borderColor: dark ? '#33425e' : '#0f172a',
                borderWidth: dark ? 1 : 0,
                titleColor: '#f8fafc',
                bodyColor: '#e2e8f0',
                padding: 10,
                cornerRadius: 8,
                boxPadding: 4,
                usePointStyle: true,
                titleFont: { size: 12, weight: '600' },
                bodyFont: { size: 12 },
                filter: (item) => item.raw != null,
                callbacks: {
                    title: tooltipTitle,
                    label: (c) => ` ${c.dataset.label}: ${Number(c.raw).toLocaleString('en-US', { maximumFractionDigits: 1 })}`,
                },
            },
        },
    };
}

/** HTML legend: square swatches for bars, short strokes for lines. */
export function Legend({ items }) {
    return (
        <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-600">
            {items.map((it) => (
                <li key={it.label} className="inline-flex items-center gap-1.5">
                    {it.swatch ? (
                        <span className="h-2.5 w-2.5 rounded-sm" style={{ background: it.swatch }} />
                    ) : it.band ? (
                        <span className="h-2.5 w-4 rounded-sm" style={{ background: it.band }} />
                    ) : (
                        <span className="w-4 border-t-2" style={{ borderColor: it.line, borderTopStyle: it.dash ? 'dashed' : 'solid' }} />
                    )}
                    {it.label}
                </li>
            ))}
        </ul>
    );
}
