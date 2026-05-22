import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Tooltip, Popup, useMap } from 'react-leaflet';

const PARANAQUE_CENTER = [14.4793, 121.0198];
const PARANAQUE_ZOOM = 13;

// Cluster centroid colour ramps by size. Cross-barangay clusters get a
// distinct outline so the thesis's headline result is visible at a glance.
function clusterFill(c) {
    if (c.case_count >= 15) return '#7f1d1d'; // red-900
    if (c.case_count >= 10) return '#dc2626'; // red-600
    if (c.case_count >= 6)  return '#f97316'; // orange-500
    return '#eab308';                          // yellow-500
}

function clusterRadius(c, zoom) {
    // Scale by sqrt(case_count) so a 4-case and a 36-case cluster are 1x vs 3x
    const base = 6 + Math.sqrt(c.case_count) * 3;
    return base * (zoom >= 15 ? 1.3 : 1);
}

export default function ClusterMapPanel({ api }) {
    const [run, setRun] = useState(null);
    const [year, setYear] = useState('all');
    const [minSize, setMinSize] = useState(3);
    const [clusters, setClusters] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [selectedDetail, setSelectedDetail] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Discover the latest detection run on mount.
    useEffect(() => {
        api.get('/clusters/latest-run')
            .then((r) => setRun(r.data))
            .catch((err) => setError(err.response?.data?.detail || err.message));
    }, [api]);

    // Reload clusters whenever filter changes.
    useEffect(() => {
        if (!run?.detection_run_id) return;
        let cancelled = false;
        setLoading(true);
        setError(null);
        const params = { run_id: run.detection_run_id, min_size: minSize };
        if (year !== 'all') params.year = year;
        api.get('/clusters', { params })
            .then((r) => {
                if (!cancelled) setClusters(r.data.clusters || []);
            })
            .catch((err) => {
                if (!cancelled) setError(err.response?.data?.detail || err.message);
            })
            .finally(() => !cancelled && setLoading(false));
        return () => { cancelled = true; };
    }, [api, run, year, minSize]);

    // Load detail when a cluster is selected.
    useEffect(() => {
        if (!selectedId) {
            setSelectedDetail(null);
            return;
        }
        let cancelled = false;
        api.get(`/clusters/${selectedId}`)
            .then((r) => { if (!cancelled) setSelectedDetail(r.data); })
            .catch(() => { if (!cancelled) setSelectedDetail(null); });
        return () => { cancelled = true; };
    }, [api, selectedId]);

    // Derive year options from the run's date range — years that actually
    // have clusters. Built once per run rather than per filter change.
    const yearOptions = useMemo(() => {
        if (!run?.date_range_start || !run?.date_range_end) return [];
        const a = new Date(run.date_range_start).getFullYear();
        const b = new Date(run.date_range_end).getFullYear();
        const out = [];
        for (let y = b; y >= a; y--) out.push(y);
        return out;
    }, [run]);

    const stats = useMemo(() => {
        if (!clusters.length) return null;
        const total = clusters.length;
        const cases = clusters.reduce((s, c) => s + c.case_count, 0);
        const crossBgy = clusters.filter((c) => c.barangay_count > 1).length;
        const maxSize = clusters.reduce((m, c) => Math.max(m, c.case_count), 0);
        return { total, cases, crossBgy, maxSize };
    }, [clusters]);

    if (!run) {
        return <div className="p-8 text-slate-500 text-sm">Loading cluster data…</div>;
    }
    if (run.detection_run_id === null) {
        return (
            <div className="p-8 text-slate-600">
                <div className="font-semibold mb-1">No clusters yet</div>
                <div className="text-sm">
                    Run <code className="bg-slate-100 px-1 rounded">python ml/detect_clusters.py</code>{' '}
                    to populate detected clusters.
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex overflow-hidden">
            {/* Side panel */}
            <aside className="w-80 border-r border-slate-200 bg-white flex flex-col">
                <div className="px-4 py-3 border-b border-slate-200">
                    <h2 className="font-semibold text-slate-800">Dengue Clusters</h2>
                    <div className="text-xs text-slate-500 mt-1">
                        {run.eps_meters}m radius, ≥{run.min_samples} cases, {run.window_weeks}-week window
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                        Detection run #{run.detection_run_id} ·{' '}
                        {new Date(run.run_at).toLocaleDateString()}
                    </div>
                </div>

                <div className="px-4 py-3 border-b border-slate-200 space-y-2">
                    <label className="block text-xs font-medium text-slate-600">
                        Year
                        <select
                            value={year}
                            onChange={(e) => { setYear(e.target.value); setSelectedId(null); }}
                            className="mt-1 w-full text-sm border border-slate-300 rounded px-2 py-1"
                        >
                            <option value="all">All years</option>
                            {yearOptions.map((y) => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </label>
                    <label className="block text-xs font-medium text-slate-600">
                        Minimum cluster size: <b className="text-slate-800">{minSize}</b>
                        <input
                            type="range" min="3" max="20" step="1" value={minSize}
                            onChange={(e) => { setMinSize(parseInt(e.target.value, 10)); setSelectedId(null); }}
                            className="w-full mt-1"
                        />
                    </label>
                </div>

                {stats && (
                    <div className="px-4 py-3 border-b border-slate-200 grid grid-cols-2 gap-2 text-xs">
                        <Stat label="Clusters" value={stats.total.toLocaleString()} />
                        <Stat label="Total cases" value={stats.cases.toLocaleString()} />
                        <Stat label="Cross-barangay"
                              value={`${stats.crossBgy} (${stats.total ? Math.round(stats.crossBgy / stats.total * 100) : 0}%)`}
                              accent="amber" />
                        <Stat label="Largest" value={`${stats.maxSize} cases`} />
                    </div>
                )}

                <div className="flex-1 overflow-y-auto">
                    {loading && <div className="px-4 py-2 text-xs text-slate-500">Loading…</div>}
                    {error && <div className="px-4 py-2 text-xs text-red-600">{error}</div>}
                    {!loading && clusters.length === 0 && (
                        <div className="px-4 py-3 text-sm text-slate-500">
                            No clusters match the current filters.
                        </div>
                    )}
                    <ul className="divide-y divide-slate-100">
                        {clusters.slice(0, 200).map((c) => (
                            <ClusterRow
                                key={c.cluster_id}
                                c={c}
                                active={c.cluster_id === selectedId}
                                onClick={() => setSelectedId(c.cluster_id)}
                            />
                        ))}
                    </ul>
                    {clusters.length > 200 && (
                        <div className="px-4 py-2 text-[11px] text-slate-400">
                            … {clusters.length - 200} more not shown. Filter by year or raise the minimum size.
                        </div>
                    )}
                </div>
            </aside>

            {/* Map */}
            <div className="flex-1 relative">
                <MapContainer
                    center={PARANAQUE_CENTER}
                    zoom={PARANAQUE_ZOOM}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />

                    {/* All cluster centroids */}
                    {clusters.map((c) => (
                        <CircleMarker
                            key={c.cluster_id}
                            center={[c.centroid_lat, c.centroid_lng]}
                            radius={clusterRadius(c, PARANAQUE_ZOOM)}
                            pathOptions={{
                                color: c.barangay_count > 1 ? '#7c3aed' : clusterFill(c),
                                weight: c.barangay_count > 1 ? 3 : 1,
                                fillColor: clusterFill(c),
                                fillOpacity: c.cluster_id === selectedId ? 0.85 : 0.55,
                            }}
                            eventHandlers={{ click: () => setSelectedId(c.cluster_id) }}
                        >
                            <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
                                <div className="text-xs">
                                    <div className="font-semibold">{c.case_count} cases</div>
                                    <div>{c.window_start} → {c.window_end}</div>
                                    <div>{c.barangays_involved}</div>
                                    <div className="text-slate-500">radius: {Math.round(c.radius_m)}m</div>
                                </div>
                            </Tooltip>
                        </CircleMarker>
                    ))}

                    {/* Selected cluster: actual radius circle + member dots */}
                    {selectedDetail && (
                        <>
                            <Circle
                                center={[selectedDetail.centroid_lat, selectedDetail.centroid_lng]}
                                radius={selectedDetail.radius_m}
                                pathOptions={{
                                    color: '#2563eb',
                                    weight: 2,
                                    fillColor: '#2563eb',
                                    fillOpacity: 0.05,
                                    dashArray: '6 6',
                                }}
                            />
                            {selectedDetail.members.map((m) => (
                                <CircleMarker
                                    key={m.case_id}
                                    center={[m.lat, m.lng]}
                                    radius={6}
                                    pathOptions={{
                                        color: '#1d4ed8',
                                        fillColor: '#3b82f6',
                                        fillOpacity: 0.9,
                                        weight: 1,
                                    }}
                                >
                                    <Popup>
                                        <div className="text-xs">
                                            <div className="font-semibold">Case #{m.case_id}</div>
                                            <div>{m.date_onset || `MW${m.morbidity_week}/${m.morbidity_year}`}</div>
                                            <div>{m.case_classification} · {m.sex} · age {m.age ?? '—'}</div>
                                            <div className="text-slate-500">{m.barangay_name}</div>
                                            <div className="text-slate-500 italic">{m.street_address}</div>
                                            <div className="text-[10px] text-slate-400 mt-1">
                                                source: {m.geocode_source}
                                            </div>
                                        </div>
                                    </Popup>
                                </CircleMarker>
                            ))}
                            <FlyToSelected detail={selectedDetail} />
                        </>
                    )}
                </MapContainer>
                <Legend />
            </div>
        </div>
    );
}

function ClusterRow({ c, active, onClick }) {
    return (
        <li>
            <button
                type="button"
                onClick={onClick}
                className={
                    'w-full text-left px-4 py-2 hover:bg-slate-50 ' +
                    (active ? 'bg-blue-50 hover:bg-blue-50' : '')
                }
            >
                <div className="flex items-baseline justify-between">
                    <span className="font-semibold text-slate-800 text-sm">
                        {c.case_count} cases
                    </span>
                    <span className="text-[11px] text-slate-500">
                        {c.window_start} → {c.window_end}
                    </span>
                </div>
                <div className="text-xs text-slate-600 mt-0.5 truncate">
                    {c.barangays_involved}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-2">
                    <span>radius: {Math.round(c.radius_m)}m</span>
                    {c.barangay_count > 1 && (
                        <span className="px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 font-medium">
                            cross-barangay
                        </span>
                    )}
                </div>
            </button>
        </li>
    );
}

function Stat({ label, value, accent }) {
    const accentClass = accent === 'amber' ? 'text-amber-700' : 'text-slate-800';
    return (
        <div>
            <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
            <div className={'font-semibold ' + accentClass}>{value}</div>
        </div>
    );
}

function FlyToSelected({ detail }) {
    const map = useMap();
    useEffect(() => {
        if (!detail) return;
        // Zoom in enough to see all members + a comfortable margin around the radius circle
        const zoomLevel = detail.radius_m < 300 ? 18 : detail.radius_m < 600 ? 17 : 16;
        map.flyTo([detail.centroid_lat, detail.centroid_lng], zoomLevel, { duration: 0.7 });
    }, [detail, map]);
    return null;
}

function Legend() {
    return (
        <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 border border-slate-200 rounded shadow-sm px-3 py-2 text-xs">
            <div className="font-semibold text-slate-700 mb-1">Cluster size</div>
            <LegendRow color="#7f1d1d" label="≥15 cases" />
            <LegendRow color="#dc2626" label="10–14 cases" />
            <LegendRow color="#f97316" label="6–9 cases" />
            <LegendRow color="#eab308" label="3–5 cases" />
            <div className="font-semibold text-slate-700 mt-2 mb-1">Outline</div>
            <LegendRow color="#7c3aed" label="cross-barangay" outline />
            <div className="text-slate-500 text-[10px] mt-2">Click a cluster for member detail</div>
        </div>
    );
}

function LegendRow({ color, label, outline }) {
    return (
        <div className="flex items-center gap-2">
            <span
                className="inline-block w-3 h-3 rounded-full"
                style={
                    outline
                        ? { border: `2px solid ${color}`, backgroundColor: 'transparent' }
                        : { backgroundColor: color }
                }
            />
            <span className="text-slate-700">{label}</span>
        </div>
    );
}
