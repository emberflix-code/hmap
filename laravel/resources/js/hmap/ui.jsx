import React from 'react';

// Shared page building blocks, so every page has the same header, cards,
// tabs, fields and buttons.

export const btn = {
    primary: 'inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-md bg-blue-600 text-white text-sm font-medium shadow-sm hover:bg-blue-700 disabled:opacity-50',
    secondary: 'inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-md border border-slate-300 bg-white text-slate-700 text-sm font-medium shadow-sm hover:bg-slate-50 disabled:opacity-50',
    ghost: 'inline-flex items-center justify-center gap-1.5 h-9 px-3 rounded-md text-blue-700 text-sm font-medium hover:bg-blue-50 disabled:opacity-50',
    small: 'inline-flex items-center justify-center gap-1 h-7 px-2.5 rounded-md border border-slate-300 bg-white text-slate-700 text-xs font-medium hover:bg-slate-50 disabled:opacity-50',
};

export const field = 'h-9 px-2.5 text-sm';

/** Page title, one-line description, and optional filters / actions on the right. */
export function PageHeader({ title, description, children }) {
    return (
        <div className="px-4 md:px-6 pt-6 pb-1 flex flex-wrap items-end justify-between gap-4">
            <div className="min-w-0">
                <h2 className="text-xl font-semibold tracking-tight text-slate-900">{title}</h2>
                {description && <p className="text-sm text-slate-500 mt-0.5">{description}</p>}
            </div>
            {children && (
                <div className="flex flex-wrap items-end gap-3 bg-white border border-slate-200 rounded-xl shadow-sm px-3 py-2.5">
                    {children}
                </div>
            )}
        </div>
    );
}

/** Card with a title row; `actions` sits at the right of the title. */
export function Card({ title, subtitle, actions, children, className = '', bodyClassName = '' }) {
    return (
        <section className={'bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden ' + className}>
            {(title || actions) && (
                <div className="px-5 py-3.5 border-b border-slate-100 flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                        {title && <h2 className="text-sm font-semibold text-slate-900">{title}</h2>}
                        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
                    </div>
                    {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
                </div>
            )}
            <div className={bodyClassName}>{children}</div>
        </section>
    );
}

/** Segmented tabs used inside pages (Weekly Report, Case Entry). */
export function Tabs({ tabs, active, onChange }) {
    return (
        <div className="px-4 md:px-6 pt-4">
            <div className="inline-flex flex-wrap gap-1 p-1 rounded-xl bg-slate-100" role="tablist">
                {tabs.map((t) => (
                    <button
                        key={t.id}
                        type="button"
                        role="tab"
                        aria-selected={active === t.id}
                        onClick={() => onChange(t.id)}
                        className={'px-3.5 py-1.5 rounded-lg text-sm font-medium ' +
                            (active === t.id ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800')}
                    >
                        {t.label}
                    </button>
                ))}
            </div>
        </div>
    );
}

/** Labelled form control. */
export function Field({ label, hint, children, className = '' }) {
    return (
        <label className={'flex flex-col gap-1 text-[11px] font-medium text-slate-500 ' + className}>
            <span>{label}</span>
            {children}
            {hint && <span className="text-[11px] font-normal text-slate-400">{hint}</span>}
        </label>
    );
}

export function NumberField({ label, value, onChange, min, max, width = 'w-24' }) {
    return (
        <Field label={label}>
            <input
                type="number"
                className={`${field} ${width} tabular-nums`}
                value={value}
                min={min}
                max={max}
                onChange={(e) => onChange(parseInt(e.target.value || '0', 10))}
            />
        </Field>
    );
}

/** ‹ week › stepper. */
export function WeekStepper({ week, onChange, label = 'Morbidity week' }) {
    const step = (d) => onChange(Math.min(53, Math.max(1, week + d)));
    const b = 'h-9 w-8 flex items-center justify-center text-slate-500 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-40';
    return (
        <label className="flex flex-col gap-1 text-[11px] font-medium text-slate-500">
            <span>{label}</span>
            <div className="flex items-stretch border border-slate-300 rounded-md overflow-hidden bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500">
                <button type="button" className={b + ' border-r border-slate-200'} onClick={() => step(-1)} disabled={week <= 1} aria-label="Previous week">‹</button>
                <input
                    type="number"
                    className="h-9 w-14 text-center text-sm tabular-nums !border-0 !shadow-none !rounded-none focus:!shadow-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
                    value={week}
                    min={1}
                    max={53}
                    onChange={(e) => onChange(parseInt(e.target.value || '0', 10))}
                />
                <button type="button" className={b + ' border-l border-slate-200'} onClick={() => step(1)} disabled={week >= 53} aria-label="Next week">›</button>
            </div>
        </label>
    );
}

/** Monday to Sunday of an ISO morbidity week, e.g. "Feb 2 - Feb 8". */
export function weekRange(year, week) {
    const jan4 = new Date(Date.UTC(year, 0, 4));
    const monday = new Date(jan4);
    monday.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7) + (week - 1) * 7);
    const sunday = new Date(monday);
    sunday.setUTCDate(monday.getUTCDate() + 6);
    const f = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
    return `${f(monday)} - ${f(sunday)}`;
}

/** Status / notice box. */
export function Notice({ tone = 'info', children, className = '' }) {
    const cls = {
        info: 'bg-blue-50 border-blue-200 text-blue-800',
        warn: 'bg-amber-50 border-amber-200 text-amber-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        ok: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    }[tone];
    return <div className={`text-sm border rounded-lg px-3.5 py-2.5 ${cls} ${className}`}>{children}</div>;
}
