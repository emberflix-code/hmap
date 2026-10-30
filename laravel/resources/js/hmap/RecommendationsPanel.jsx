import React, { useCallback, useEffect, useState } from 'react';

const TIER_STYLE = {
    High: 'bg-red-100 text-red-800',
    Moderate: 'bg-amber-100 text-amber-800',
    Low: 'bg-slate-100 text-slate-600',
};
const CATEGORY_LABEL = { Team: 'Team', Supply: 'Supply', Medicine: 'Medicine', IEC: 'Info material' };

/**
 * Module 6 recommender: barangays rated Moderate or High, ranked, each with
 * the resources the rule table recommends. The Health Analyst records
 * whether each item was acted on. Administrators also maintain the rules.
 */
export default function RecommendationsPanel({ api, disease, year, week, isAdmin }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [showRules, setShowRules] = useState(false);
    // The top three barangays start open; the rest are folded to a summary line.
    const [open, setOpen] = useState({});
    const isOpen = (b, idx) => open[b.barangay_id] ?? idx < 3;
    const toggle = (b, idx) => setOpen({ ...open, [b.barangay_id]: !isOpen(b, idx) });
    const setAll = (v) => setOpen(Object.fromEntries((data?.barangays || []).map((b) => [b.barangay_id, v])));

    const load = useCallback(() => {
        setError(null);
        api.get('/recommendations', { params: { disease_code: disease, year, week } })
            .then((r) => setData(r.data))
            .catch((err) => setError(err.response?.data?.detail || err.message));
    }, [api, disease, year, week]);

    useEffect(() => { load(); }, [load]);

    const record = (id, action_status) => {
        let action_note = null;
        if (action_status !== 'Pending') {
            action_note = window.prompt('Note (optional): what was done, when, by whom', '');
            if (action_note === null) return;   // cancelled
        }
        api.post(`/recommendations/${id}/action`, { action_status, action_note })
            .then(load)
            .catch((err) => setError(err.response?.data?.message || err.message));
    };

    if (error) return <div className="p-4 text-sm text-red-700">{error}</div>;
    if (!data) return <div className="p-4 text-sm text-slate-500">Loading recommendations…</div>;

    return (
        <div className="p-5 space-y-3">
            {data.barangays.length > 3 && (
                <div className="flex justify-end gap-1 -mt-1">
                    <button type="button" className="text-xs font-medium text-blue-700 hover:bg-blue-50 rounded-md px-2 py-1" onClick={() => setAll(true)}>Expand all</button>
                    <button type="button" className="text-xs font-medium text-blue-700 hover:bg-blue-50 rounded-md px-2 py-1" onClick={() => setAll(false)}>Collapse all</button>
                </div>
            )}
            {data.draft_rules > 0 && (
                <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                    {data.draft_rules} of the rules used here are drafts not yet validated by CESU.
                    Treat these items as suggestions.
                </div>
            )}
            {data.uses_fallback_rules && (
                <div className="text-xs text-slate-600">
                    No rules are defined for this disease yet; general response rules are shown.
                </div>
            )}
            {data.barangays.length === 0 && (
                <div className="text-sm text-slate-500">
                    No barangay is at Moderate or High risk for this disease in week {week} of {year}.
                </div>
            )}
            {data.barangays.map((b, idx) => {
                const expanded = isOpen(b, idx);
                const acted = b.items.filter((i) => i.action_status !== 'Pending').length;
                return (
                <div key={b.barangay_id} className="border border-slate-200 rounded-lg overflow-hidden">
                    <button
                        type="button"
                        onClick={() => toggle(b, idx)}
                        aria-expanded={expanded}
                        className="w-full px-4 py-2.5 bg-slate-50 hover:bg-slate-100 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-left"
                    >
                        <svg viewBox="0 0 20 20" className={'h-4 w-4 text-slate-400 transition-transform ' + (expanded ? 'rotate-90' : '')} fill="currentColor" aria-hidden="true">
                            <path fillRule="evenodd" d="M7.2 14.8a1 1 0 0 1 0-1.4L10.6 10 7.2 6.6a1 1 0 1 1 1.4-1.4l4.1 4.1a1 1 0 0 1 0 1.4l-4.1 4.1a1 1 0 0 1-1.4 0z" clipRule="evenodd" />
                        </svg>
                        <span className="font-semibold text-slate-800">
                            {b.rank ? `${b.rank}. ` : ''}{b.barangay_name}
                        </span>
                        <span className={'px-2 py-0.5 rounded-full text-xs font-medium ' + TIER_STYLE[b.tier]}>{b.tier}</span>
                        <span className="text-xs text-slate-500">
                            {b.rank
                                ? `${b.active_cases} active case${b.active_cases === 1 ? '' : 's'} in 4 weeks · ${b.reasons.join(', ')}`
                                : 'no longer flagged; recorded actions kept'}
                        </span>
                        <span className="ml-auto text-xs text-slate-500 tabular-nums">
                            {acted} of {b.items.length} actions recorded
                        </span>
                    </button>
                    {expanded && (
                    <table className="w-full text-xs">
                        <tbody>
                            {b.items.map((i) => (
                                <tr key={i.recommendation_id} className={'border-t border-slate-100 ' + (i.still_applies ? '' : 'opacity-60')}>
                                    <td className="px-3 py-1.5 text-slate-500 w-24">{CATEGORY_LABEL[i.category]}</td>
                                    <td className="py-1.5 text-slate-800" title={`Source: ${i.source}${i.notes ? '\n' + i.notes : ''}`}>
                                        {i.item}
                                        {i.rule_status === 'Draft' && <span className="ml-2 text-[10px] text-amber-700">draft</span>}
                                        {!i.still_applies && <span className="ml-2 text-[10px] text-slate-500">no longer applies</span>}
                                    </td>
                                    <td className="py-1.5 text-slate-700 w-32 text-right pr-3">
                                        {i.quantity != null ? `${i.quantity} ${i.unit || ''}` : 'as assessed'}
                                    </td>
                                    <td className="py-1.5 pr-3 w-56 text-right">
                                        {i.action_status === 'Pending' ? (
                                            <>
                                                <ActionButton onClick={() => record(i.recommendation_id, 'Acted')}>Acted</ActionButton>
                                                <ActionButton onClick={() => record(i.recommendation_id, 'Not acted')}>Not acted</ActionButton>
                                            </>
                                        ) : (
                                            <span title={i.action_note || ''}>
                                                <span className={i.action_status === 'Acted' ? 'text-emerald-700' : 'text-slate-600'}>
                                                    {i.action_status}
                                                </span>
                                                <span className="text-slate-400"> {i.action_at?.slice(0, 10)} </span>
                                                <button type="button" className="text-slate-400 hover:text-slate-700 underline"
                                                        onClick={() => record(i.recommendation_id, 'Pending')}>undo</button>
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    )}
                </div>
                );
            })}

            <div className="pt-2 border-t border-slate-100">
                <button type="button" className="text-xs text-blue-700 hover:underline" onClick={() => setShowRules(!showRules)}>
                    {showRules ? 'Hide rule table' : 'Show rule table'}
                </button>
            </div>
            {showRules && <RuleTable api={api} isAdmin={isAdmin} onChanged={load} />}
        </div>
    );
}

function ActionButton({ onClick, children }) {
    return (
        <button type="button" onClick={onClick}
                className="ml-1 h-7 px-2.5 rounded-md border border-slate-300 bg-white text-slate-700 font-medium hover:bg-slate-50">
            {children}
        </button>
    );
}

function RuleTable({ api, isAdmin, onChanged }) {
    const [rules, setRules] = useState(null);
    const [error, setError] = useState(null);

    const load = useCallback(() => {
        api.get('/recommendation-rules').then((r) => setRules(r.data))
            .catch((err) => setError(err.response?.data?.detail || err.message));
    }, [api]);
    useEffect(() => { load(); }, [load]);

    const change = (promise) =>
        promise.then(() => { load(); onChanged(); })
            .catch((err) => setError(err.response?.data?.message || err.message));

    const edit = (r) => {
        const item = window.prompt('Recommended item', r.item);
        if (item === null) return;
        const factor = r.scaling_basis === 'as_assessed' ? null
            : window.prompt(`Quantity factor (${r.scaling_basis.replace(/_/g, ' ')})`, r.quantity_factor ?? '');
        const body = { item };
        if (factor !== null && factor !== undefined) body.quantity_factor = factor === '' ? null : Number(factor);
        change(api.put(`/recommendation-rules/${r.rule_id}`, body));
    };

    if (error) return <div className="text-xs text-red-700">{error}</div>;
    if (!rules) return <div className="text-xs text-slate-500">Loading rules…</div>;

    return (
        <div className="overflow-x-auto">
            <p className="text-xs text-slate-500 mb-2">
                Moderate rules apply to Moderate and High barangays; High rules only to High.
                Editing a rule returns it to Draft until it is validated again.
            </p>
            <table className="w-full text-xs">
                <thead className="text-left text-slate-500">
                    <tr>
                        <th className="py-1">Disease</th><th>Tier</th><th>Category</th><th>Item</th>
                        <th>Quantity</th><th>Source</th><th>Status</th>{isAdmin && <th />}
                    </tr>
                </thead>
                <tbody className="text-slate-700">
                    {rules.map((r) => (
                        <tr key={r.rule_id} className={'border-t border-slate-100 ' + (r.is_active ? '' : 'opacity-40')}>
                            <td className="py-1 pr-2">{r.disease_code || 'any other'}</td>
                            <td className="pr-2">{r.risk_tier}</td>
                            <td className="pr-2">{CATEGORY_LABEL[r.category]}</td>
                            <td className="pr-2">{r.item}</td>
                            <td className="pr-2 whitespace-nowrap">
                                {r.scaling_basis === 'as_assessed' ? 'as assessed'
                                    : `${Number(r.quantity_factor)} ${r.unit || ''} ${r.scaling_basis === 'fixed' ? '' : r.scaling_basis.replace(/_/g, ' ')}`}
                            </td>
                            <td className="pr-2 text-slate-500">{r.source}</td>
                            <td className={'pr-2 ' + (r.status === 'Validated' ? 'text-emerald-700' : 'text-amber-700')}>
                                {r.is_active ? r.status : 'inactive'}
                            </td>
                            {isAdmin && (
                                <td className="whitespace-nowrap text-right">
                                    <ActionButton onClick={() => edit(r)}>Edit</ActionButton>
                                    {r.status === 'Draft' && r.is_active ? (
                                        <ActionButton onClick={() => change(api.post(`/recommendation-rules/${r.rule_id}/validate`))}>
                                            Validate
                                        </ActionButton>
                                    ) : null}
                                    <ActionButton onClick={() => change(api.put(`/recommendation-rules/${r.rule_id}`, { is_active: !r.is_active }))}>
                                        {r.is_active ? 'Deactivate' : 'Activate'}
                                    </ActionButton>
                                </td>
                            )}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
