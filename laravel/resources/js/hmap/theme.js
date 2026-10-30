import { useEffect, useState } from 'react';

// Light / dark theme. The choice ('light', 'dark' or 'system') is kept per
// browser; 'system' follows the operating system setting.
const KEY = 'hmap.theme';

function stored() {
    try { return window.localStorage.getItem(KEY) || 'system'; } catch (_) { return 'system'; }
}

function systemDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function applyTheme(choice = stored()) {
    const dark = choice === 'dark' || (choice === 'system' && systemDark());
    document.documentElement.classList.toggle('dark', dark);
    return dark;
}

/** [choice, setChoice] for the header switch. */
export function useThemeChoice() {
    const [choice, setChoice] = useState(stored);
    useEffect(() => {
        applyTheme(choice);
        try { window.localStorage.setItem(KEY, choice); } catch (_) { /* private mode */ }
        if (choice !== 'system' || !window.matchMedia) return undefined;
        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        const onChange = () => applyTheme('system');
        mq.addEventListener('change', onChange);
        return () => mq.removeEventListener('change', onChange);
    }, [choice]);
    return [choice, setChoice];
}

/** True while the page is in dark mode; re-renders charts when it changes. */
export function useIsDark() {
    const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));
    useEffect(() => {
        const obs = new MutationObserver(() => setDark(document.documentElement.classList.contains('dark')));
        obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => obs.disconnect();
    }, []);
    return dark;
}
