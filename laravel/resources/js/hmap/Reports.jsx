import React, { useMemo, useState } from 'react';

const ROLE_LEVELS = { Encoder: 1, Analyst: 2, Administrator: 3 };

function roleMeets(actual, minimum) {
    return (ROLE_LEVELS[actual] ?? 0) >= (ROLE_LEVELS[minimum] ?? 0);
}

export default function Reports({ whoami, diseases }) {
    const today = useMemo(() => new Date(), []);
    const [summaryYear, setSummaryYear] = useState(today.getFullYear());
    const [summaryDisease, setSummaryDisease] = useState('');

    const role = whoami.role;

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-4">
            <ReportCard
                title="My entry log"
                description="Every case you personally encoded. Useful for verifying a week's work."
                role={role}
                requires="Encoder"
                href="/api/export/my-entries"
                filenameHint={`my-entries-${whoami.employee_id}-${today.toISOString().slice(0, 10)}.csv`}
            />

            <ReportCard
                title="Disease summary report"
                description="Per-(disease, barangay, week) aggregates for the selected year, with EWARN alert flag. Anonymized; suitable for sharing with city health office leadership."
                role={role}
                requires="Analyst"
                href={
                    '/api/export/disease-summary?year=' +
                    encodeURIComponent(summaryYear) +
                    (summaryDisease ? '&disease_code=' + encodeURIComponent(summaryDisease) : '')
                }
                filenameHint={`disease-summary-${summaryDisease || 'all'}-${summaryYear}.csv`}
                controls={
                    <div className="flex gap-3 items-end">
                        <label className="flex flex-col text-xs text-slate-600">
                            <span className="mb-1">Year</span>
                            <input
                                type="number"
                                min={2010}
                                max={2100}
                                className="border border-slate-300 rounded px-2 py-1.5 text-sm w-24"
                                value={summaryYear}
                                onChange={(e) => setSummaryYear(parseInt(e.target.value || '0', 10))}
                            />
                        </label>
                        <label className="flex flex-col text-xs text-slate-600">
                            <span className="mb-1">Disease (optional)</span>
                            <select
                                className="border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"
                                value={summaryDisease}
                                onChange={(e) => setSummaryDisease(e.target.value)}
                            >
                                <option value="">All diseases</option>
                                {diseases.map((d) => (
                                    <option key={d.disease_code} value={d.disease_code}>
                                        {d.disease_name}
                                    </option>
                                ))}
                            </select>
                        </label>
                    </div>
                }
            />

            <ReportCard
                title="Full case registry"
                description="All active case records, every column. Intended for DOH submission and archival purposes."
                role={role}
                requires="Administrator"
                href="/api/export/full-registry"
                filenameHint={`hmap-registry-${today.toISOString().slice(0, 10)}.csv`}
                note="Large export (~35,000 rows); the file streams in chunks of 500."
            />

            <div className="text-xs text-slate-500 mt-4 px-1">
                Every export is recorded in the system audit log with your employee ID, the export
                type, row count, IP address, and timestamp — consistent with Republic Act No.
                10173, the Data Privacy Act of 2012.
            </div>
        </div>
    );
}

function ReportCard({ title, description, role, requires, href, filenameHint, controls, note }) {
    const allowed = roleMeets(role, requires);
    return (
        <section
            className={
                'bg-white rounded-lg border shadow-sm p-5 flex flex-col gap-3 ' +
                (allowed ? 'border-slate-200' : 'border-slate-200 opacity-60')
            }
        >
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
                    <p className="text-xs text-slate-600 mt-1">{description}</p>
                </div>
                <span
                    className={
                        'text-[10px] uppercase font-semibold tracking-wide px-2 py-1 rounded ' +
                        (allowed
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-slate-100 text-slate-500')
                    }
                >
                    {requires}+
                </span>
            </div>
            {controls && allowed && <div>{controls}</div>}
            <div className="flex items-center gap-3 mt-1">
                <a
                    href={allowed ? href : undefined}
                    download={allowed ? filenameHint : undefined}
                    onClick={(e) => !allowed && e.preventDefault()}
                    className={
                        'px-4 py-2 rounded text-sm font-medium ' +
                        (allowed
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-slate-200 text-slate-500 cursor-not-allowed')
                    }
                >
                    Download CSV
                </a>
                {!allowed && (
                    <span className="text-xs text-slate-500">
                        Requires {requires} role.
                    </span>
                )}
                {note && allowed && <span className="text-xs text-slate-500">{note}</span>}
            </div>
        </section>
    );
}
