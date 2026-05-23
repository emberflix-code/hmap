import React, { useEffect, useMemo, useState } from 'react';

/**
 * Mirrors three sheets of the CESU PIDSR workbook:
 *   - Summary Weekly Update (Cat I + Cat II disease tables)
 *   - PIDSRMain                (Dengue YTD detail)
 *   - SBgy                     (per-barangay rates per 10,000 pop)
 *
 * All values are YTD-through-week-N to match how CESU reads "5-year average"
 * in the workbook (see reference_5yrave_ytd_semantic memory entry).
 */
export default function WeeklyReport({ api, diseases }) {
    const today = useMemo(() => isoMorbidityWeek(new Date()), []);
    const [year, setYear] = useState(today.year);
    const [week, setWeek] = useState(today.week);
    const [tab, setTab] = useState('summary');

    return (
        <>
            <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-end gap-4">
                <FieldNumber label="Year" value={year} min={2010} max={2100} onChange={setYear} />
                <FieldNumber label="Morbidity week" value={week} min={1} max={53} onChange={setWeek} />
                <div className="ml-auto text-xs text-slate-500">
                    YTD through morbidity week {week} of {year} · mirrors CESU PIDSR workbook
                </div>
            </div>

            <div className="bg-white border-b border-slate-200 px-6">
                <TabBar
                    tabs={[
                        { id: 'summary', label: 'Summary (Cat I + II)' },
                        { id: 'dengue',  label: 'Dengue detail' },
                        { id: 'rates',   label: 'Per-barangay rates' },
                        { id: 'memo',    label: 'Memo draft' },
                    ]}
                    active={tab}
                    onChange={setTab}
                />
            </div>

            <main className="flex-1 p-6">
                {tab === 'summary' && <SummaryTab api={api} year={year} week={week} />}
                {tab === 'dengue'  && <DengueTab  api={api} year={year} week={week} />}
                {tab === 'rates'   && <RatesTab   api={api} diseases={diseases} year={year} week={week} />}
                {tab === 'memo'    && <MemoTab    api={api} year={year} week={week} />}
            </main>
        </>
    );
}

// ── Tab 1: Summary Weekly Update ──────────────────────────────────────────

function SummaryTab({ api, year, week }) {
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        setData(null); setErr(null);
        api.get('/weekly-summary', { params: { morbidity_year: year, morbidity_week: week } })
            .then((r) => setData(r.data))
            .catch((e) => setErr(e.response?.data?.message || e.message));
    }, [api, year, week]);

    if (err) return <ErrorBox>{err}</ErrorBox>;
    if (!data) return <Loading />;

    const cat1 = data.rows.filter((r) => r.disease_category === 'Category 1');
    const cat2 = data.rows.filter((r) => r.disease_category === 'Category 2');
    const baselineLabel = `${data.baseline_years[0]}–${data.baseline_years[data.baseline_years.length - 1]}`;

    return (
        <div className="space-y-6">
            <Panel
                title={`Table 1. Category I — Immediately Notifiable Diseases`}
                subtitle={`Parañaque City, YTD through MW ${week} of ${year} · vs. ${year - 1} · vs. 5-year average (${baselineLabel})`}
            >
                <SummaryTable rows={cat1} year={year} />
            </Panel>
            <Panel
                title={`Table 2. Category II — Weekly Notifiable Diseases`}
                subtitle={`Parañaque City, YTD through MW ${week} of ${year} · vs. ${year - 1} · vs. 5-year average (${baselineLabel})`}
            >
                <SummaryTable rows={cat2} year={year} />
            </Panel>
        </div>
    );
}

function SummaryTable({ rows, year }) {
    const fmt = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
    const cfr = (deaths, cases) =>
        cases > 0 ? ((deaths / cases) * 100).toFixed(2) + '%' : '—';
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                        <th rowSpan={2} className="text-left px-3 py-2 border-r border-slate-200">Disease</th>
                        <th colSpan={3} className="text-center px-3 py-2 border-r border-slate-200 bg-slate-100">5-year average</th>
                        <th colSpan={3} className="text-center px-3 py-2 border-r border-slate-200 bg-slate-100">{year - 1}</th>
                        <th colSpan={3} className="text-center px-3 py-2 bg-blue-50">{year} (current)</th>
                    </tr>
                    <tr className="text-xs text-slate-500">
                        <th className="px-3 py-1">Cases</th>
                        <th className="px-3 py-1">Deaths</th>
                        <th className="px-3 py-1 border-r border-slate-200">CFR</th>
                        <th className="px-3 py-1">Cases</th>
                        <th className="px-3 py-1">Deaths</th>
                        <th className="px-3 py-1 border-r border-slate-200">CFR</th>
                        <th className="px-3 py-1">Cases</th>
                        <th className="px-3 py-1">Deaths</th>
                        <th className="px-3 py-1">CFR</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((r) => {
                        const curHi = r.cases_current > r.avg_5yr_cases && r.cases_current > 0;
                        return (
                            <tr key={r.disease_code} className="border-b border-slate-100 last:border-b-0">
                                <td className="px-3 py-2 border-r border-slate-100">{r.disease_name}</td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(r.avg_5yr_cases)}</td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(r.avg_5yr_deaths)}</td>
                                <td className="px-3 py-2 text-right tabular-nums border-r border-slate-100 text-slate-500">
                                    {cfr(r.avg_5yr_deaths, r.avg_5yr_cases)}
                                </td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(r.cases_prior)}</td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(r.deaths_prior)}</td>
                                <td className="px-3 py-2 text-right tabular-nums border-r border-slate-100 text-slate-500">
                                    {cfr(r.deaths_prior, r.cases_prior)}
                                </td>
                                <td className={'px-3 py-2 text-right tabular-nums ' + (curHi ? 'font-semibold text-rose-700' : '')}>
                                    {fmt(r.cases_current)}
                                </td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(r.deaths_current)}</td>
                                <td className="px-3 py-2 text-right tabular-nums text-slate-500">
                                    {cfr(r.deaths_current, r.cases_current)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <p className="text-xs text-slate-500 mt-2 px-3">
                Bold red = current YTD cases exceed 5-year average. All values count ALL classifications
                (Suspect + Probable + Confirmed + Discarded + Negative + Compatible + Pending) — same basis
                as CESU's existing 5YrAve sheet.
            </p>
        </div>
    );
}

// ── Tab 2: Dengue detail (PIDSRMain) ──────────────────────────────────────

function DengueTab({ api, year, week }) {
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        setData(null); setErr(null);
        api.get('/dengue-detail', { params: { morbidity_year: year, morbidity_week: week } })
            .then((r) => setData(r.data))
            .catch((e) => setErr(e.response?.data?.message || e.message));
    }, [api, year, week]);

    if (err) return <ErrorBox>{err}</ErrorBox>;
    if (!data) return <Loading />;

    const cur = data.current;
    const prev = data.previous;
    const change = prev.cases > 0
        ? Math.round(((cur.cases - prev.cases) / prev.cases) * 100)
        : null;
    const changeLabel = change === null ? '—'
        : change === 0 ? '0% (same)'
        : change > 0 ? `${change}% higher`
        : `${Math.abs(change)}% lower`;

    return (
        <div className="space-y-6">
            <Panel
                title={`Dengue updates · MW ${week} of ${year}`}
                subtitle={`Parañaque City · YTD through week ${week}`}
            >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
                    <Stat label="Cases (current YTD)" value={cur.cases.toLocaleString()} hint={`${year}`} />
                    <Stat label={`Cases (${year - 1} YTD)`} value={prev.cases.toLocaleString()} hint={`prior year`} />
                    <Stat label="Change vs. prior year" value={changeLabel}
                          tone={change > 0 ? 'rose' : change < 0 ? 'emerald' : 'slate'} />
                    <Stat label="Deaths (current)" value={cur.deaths} hint={`CFR ${(cur.cfr * 100).toFixed(2)}%`} />
                    <Stat label="Deaths (prior year)" value={prev.deaths} hint={`CFR ${(prev.cfr * 100).toFixed(2)}%`} />
                    <Stat label="Sex distribution (current)"
                          value={`M ${cur.males} / F ${cur.females}`}
                          hint={cur.cases > 0
                              ? `${((cur.males / cur.cases) * 100).toFixed(0)}% male`
                              : ''} />
                </div>
            </Panel>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Panel title="Age profile (current YTD)" subtitle="Range and median age of cases">
                    <div className="p-4 grid grid-cols-3 gap-4">
                        <Stat label="Youngest" value={cur.age_min ?? '—'} hint={cur.age_min === 0 ? 'under 1 year' : 'years'} />
                        <Stat label="Median" value={cur.age_median ?? '—'} hint="years" />
                        <Stat label="Oldest" value={cur.age_max ?? '—'} hint="years" />
                    </div>
                    {cur.top_age_group && (
                        <div className="px-4 pb-4 text-sm text-slate-600">
                            <strong>Most-affected age group:</strong> {cur.top_age_group.group} ·{' '}
                            {cur.top_age_group.cases} cases ({((cur.top_age_group.cases / cur.cases) * 100).toFixed(1)}%)
                        </div>
                    )}
                </Panel>

                <Panel title="DRU type breakdown (current YTD)" subtitle="Where cases were reported">
                    <div className="p-4 space-y-2">
                        {Object.entries(cur.by_dru_type).map(([type, n]) => (
                            <DruTypeBar key={type} type={type} count={n} total={cur.cases} />
                        ))}
                    </div>
                </Panel>
            </div>

            <Panel title="Top sentinel sites (current YTD)" subtitle="Sentinel facilities ranked by case count">
                <div className="p-4">
                    {cur.top_sentinels.length === 0 ? (
                        <p className="text-sm text-slate-500">No cases reported through sentinel sites yet.</p>
                    ) : (
                        <ol className="space-y-1">
                            {cur.top_sentinels.map((s, i) => (
                                <li key={s.name} className="flex items-center gap-3 text-sm">
                                    <span className="font-semibold text-slate-700 w-6 text-right">{i + 1}.</span>
                                    <span className="flex-1">{s.name}</span>
                                    <span className="tabular-nums text-slate-700">{s.cases} cases</span>
                                    <span className="tabular-nums text-slate-400 text-xs w-12 text-right">
                                        {((s.cases / cur.cases) * 100).toFixed(1)}%
                                    </span>
                                </li>
                            ))}
                        </ol>
                    )}
                </div>
            </Panel>
        </div>
    );
}

function DruTypeBar({ type, count, total }) {
    const pct = total > 0 ? (count / total) * 100 : 0;
    return (
        <div>
            <div className="flex justify-between text-sm">
                <span>{type}</span>
                <span className="tabular-nums text-slate-600">
                    {count} <span className="text-slate-400 text-xs">({pct.toFixed(1)}%)</span>
                </span>
            </div>
            <div className="h-2 bg-slate-100 rounded mt-1 overflow-hidden">
                <div className="h-full bg-blue-500" style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

// ── Tab 3: Per-barangay rates (SBgy) ──────────────────────────────────────

function RatesTab({ api, diseases, year, week }) {
    const [disease, setDisease] = useState('DENGUE');
    const [data, setData] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        setData(null); setErr(null);
        api.get('/barangay-rates', {
            params: { disease_code: disease, morbidity_year: year, morbidity_week: week },
        })
            .then((r) => setData(r.data))
            .catch((e) => setErr(e.response?.data?.message || e.message));
    }, [api, disease, year, week]);

    const maxRate = useMemo(
        () => (data ? Math.max(0.0001, ...data.rows.map((r) => r.rate_per_10k)) : 1),
        [data]
    );

    return (
        <div className="space-y-4">
            <div className="flex items-end gap-4">
                <label className="flex flex-col text-xs text-slate-600">
                    <span className="mb-1">Disease</span>
                    <select
                        className="border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"
                        value={disease}
                        onChange={(e) => setDisease(e.target.value)}
                    >
                        {diseases.map((d) => (
                            <option key={d.disease_code} value={d.disease_code}>{d.disease_name}</option>
                        ))}
                    </select>
                </label>
            </div>

            {err && <ErrorBox>{err}</ErrorBox>}
            {!err && !data && <Loading />}
            {data && (
                <Panel
                    title={`Per-barangay rates · ${diseases.find((d) => d.disease_code === disease)?.disease_name ?? disease}`}
                    subtitle={`YTD through MW ${data.week} of ${data.year} · ranked by rate per 10,000 population`}
                >
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm border-collapse">
                            <thead className="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th className="text-left px-3 py-2 w-12">Rank</th>
                                    <th className="text-left px-3 py-2">Barangay</th>
                                    <th className="text-right px-3 py-2">Population</th>
                                    <th className="text-right px-3 py-2">Cases (YTD)</th>
                                    <th className="text-right px-3 py-2">Rate / 10,000</th>
                                    <th className="text-left px-3 py-2 w-1/4">Relative</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.rows.map((r) => (
                                    <tr key={r.barangay_id} className="border-b border-slate-100 last:border-b-0">
                                        <td className="px-3 py-2 tabular-nums font-semibold text-slate-700">{r.rank}</td>
                                        <td className="px-3 py-2">{r.barangay_name}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">{r.population.toLocaleString()}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">{r.cases}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">
                                            {r.rate_per_10k.toFixed(4)}
                                        </td>
                                        <td className="px-3 py-2">
                                            <div className="h-2 bg-slate-100 rounded overflow-hidden">
                                                <div
                                                    className="h-full bg-rose-400"
                                                    style={{ width: `${(r.rate_per_10k / maxRate) * 100}%` }}
                                                />
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                <tr className="border-t-2 border-slate-300 bg-slate-50 font-semibold">
                                    <td className="px-3 py-2">—</td>
                                    <td className="px-3 py-2">Total (Parañaque City)</td>
                                    <td className="px-3 py-2 text-right tabular-nums">{data.total.population.toLocaleString()}</td>
                                    <td className="px-3 py-2 text-right tabular-nums">{data.total.cases}</td>
                                    <td className="px-3 py-2 text-right tabular-nums">{data.total.rate_per_10k.toFixed(4)}</td>
                                    <td />
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </Panel>
            )}
        </div>
    );
}

// ── Tab 4: Memo draft (auto-generated from H-MAP data) ────────────────────

function MemoTab({ api, year, week }) {
    const [memo, setMemo] = useState('');
    const [original, setOriginal] = useState('');
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState(null);
    const [copied, setCopied] = useState(false);

    const regenerate = () => {
        setLoading(true); setErr(null); setCopied(false);
        api.get('/dengue-memo', { params: { morbidity_year: year, morbidity_week: week } })
            .then((r) => { setMemo(r.data.memo); setOriginal(r.data.memo); })
            .catch((e) => setErr(e.response?.data?.message || e.message))
            .finally(() => setLoading(false));
    };

    useEffect(() => { regenerate(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [year, week]);

    const copy = async () => {
        try {
            await navigator.clipboard.writeText(memo);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (e) {
            setErr('Could not copy: ' + e.message);
        }
    };

    const download = () => {
        const blob = new Blob([memo], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dengue-memo-${year}-MW${String(week).padStart(2, '0')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const isEdited = memo !== original;

    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <Panel
                title="Dengue narrative memo — editable draft"
                subtitle={`Auto-generated from MW ${week} of ${year} data · for review by the City Epidemiologist`}
            >
                <div className="p-4 space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                        <button
                            type="button"
                            onClick={regenerate}
                            disabled={loading}
                            className="px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50"
                        >
                            {loading ? 'Regenerating…' : 'Regenerate from data'}
                        </button>
                        <button
                            type="button"
                            onClick={copy}
                            disabled={!memo}
                            className="px-3 py-1.5 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:opacity-50"
                        >
                            {copied ? 'Copied!' : 'Copy to clipboard'}
                        </button>
                        <button
                            type="button"
                            onClick={download}
                            disabled={!memo}
                            className="px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50"
                        >
                            Download .txt
                        </button>
                        {isEdited && (
                            <span className="ml-auto text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                                Edited from original draft
                            </span>
                        )}
                    </div>

                    {err && <ErrorBox>{err}</ErrorBox>}

                    <textarea
                        value={memo}
                        onChange={(e) => setMemo(e.target.value)}
                        spellCheck={false}
                        className="w-full h-[480px] font-mono text-xs text-slate-800 border border-slate-300 rounded p-3 leading-relaxed resize-y"
                        placeholder={loading ? 'Generating draft…' : 'Memo will appear here.'}
                    />

                    <p className="text-xs text-slate-500">
                        This is a draft generated from PIDSR Registry data. Edit before sending. Numbers
                        are pulled live from the database, so regenerating after data is updated will reflect
                        the latest figures.
                    </p>
                </div>
            </Panel>
        </div>
    );
}


// ── Shared UI helpers ─────────────────────────────────────────────────────

function Panel({ title, subtitle, children }) {
    return (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
                {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
            </div>
            <div>{children}</div>
        </section>
    );
}

function TabBar({ tabs, active, onChange }) {
    return (
        <div className="flex gap-0 -mb-px">
            {tabs.map((t) => (
                <button
                    key={t.id}
                    type="button"
                    onClick={() => onChange(t.id)}
                    className={
                        'px-4 py-2 text-sm border-b-2 ' +
                        (active === t.id
                            ? 'border-blue-600 text-blue-700 font-medium'
                            : 'border-transparent text-slate-600 hover:text-slate-800')
                    }
                >
                    {t.label}
                </button>
            ))}
        </div>
    );
}

function Stat({ label, value, hint, tone }) {
    const toneClass =
        tone === 'rose' ? 'text-rose-700' :
        tone === 'emerald' ? 'text-emerald-700' :
        'text-slate-800';
    return (
        <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
            <div className="text-xs text-slate-500">{label}</div>
            <div className={'text-2xl font-semibold mt-1 ' + toneClass}>{value}</div>
            {hint && <div className="text-xs text-slate-500 mt-0.5">{hint}</div>}
        </div>
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

function Loading() {
    return <div className="p-8 text-sm text-slate-500">Loading…</div>;
}

function ErrorBox({ children }) {
    return (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
            {children}
        </div>
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
