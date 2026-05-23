import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, GeoJSON, Tooltip } from 'react-leaflet';

const PARANAQUE_CENTER = [14.4793, 121.0198];
const PARANAQUE_ZOOM = 13;

const RISK_COLORS = {
    High: '#dc2626',     // red-600
    Moderate: '#f59e0b', // amber-500
    Low: '#16a34a',      // green-600
};

export default function HeatMapPanel({ api, disease, year, week, barangays }) {
    const [riskScores, setRiskScores] = useState({});
    const [heatmapCounts, setHeatmapCounts] = useState({});
    const [geoJson, setGeoJson] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch the boundary polygons once. Derive the URL from the current
    // page path so this works at both `/` (local dev) and `/hmap/` (LGU
    // portal subpath deployment) — mirrors the axios baseURL trick in App.jsx.
    useEffect(() => {
        const match = window.location.pathname.match(/^(\/[^/]+)?(?:\/(?:entry|reports|clusters|weekly)?)?$/);
        const root = match && match[1] ? match[1] : '';
        fetch(root + '/barangays.geojson')
            .then((r) => (r.ok ? r.json() : null))
            .then((gj) => setGeoJson(gj))
            .catch(() => setGeoJson(null));
    }, []);

    // Risk + heat data, refetched whenever the picker changes.
    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);

        Promise.allSettled([
            api.post('/ml/risk', {
                disease_code: disease,
                morbidity_year: year,
                morbidity_week: week,
            }),
            api.get('/heatmap-week', {
                params: {
                    disease_code: disease,
                    morbidity_year: year,
                    morbidity_week: week,
                },
            }),
        ])
            .then(([risk, heat]) => {
                if (cancelled) return;
                if (risk.status === 'fulfilled') {
                    const m = {};
                    for (const s of risk.value.data.scores || []) {
                        m[s.barangay_id] = s;
                    }
                    setRiskScores(m);
                } else {
                    setRiskScores({});
                }
                if (heat.status === 'fulfilled') {
                    const m = {};
                    for (const r of heat.value.data || []) {
                        m[r.barangay_id] = r.cases;
                    }
                    setHeatmapCounts(m);
                } else {
                    setHeatmapCounts({});
                }
            })
            .finally(() => !cancelled && setLoading(false));

        return () => { cancelled = true; };
    }, [api, disease, year, week]);

    // Join barangay metadata (centroid, name) with case count + risk class
    const points = useMemo(() => {
        return barangays.map((b, i) => {
            const hasCentroid = b.centroid_lat != null && b.centroid_lng != null;
            const fallback = spreadFallback(i, barangays.length);
            return {
                id: b.barangay_id,
                name: b.barangay_name,
                lat: hasCentroid ? Number(b.centroid_lat) : fallback[0],
                lng: hasCentroid ? Number(b.centroid_lng) : fallback[1],
                hasCentroid,
                cases: heatmapCounts[b.barangay_id] || 0,
                risk: riskScores[b.barangay_id],
            };
        });
    }, [barangays, heatmapCounts, riskScores]);

    // Build a map from canonical_name (from the GeoJSON properties) → risk + cases.
    // The Python script writes properties.canonical_name in the GeoJSON.
    const riskByName = useMemo(() => {
        const m = {};
        for (const p of points) {
            m[p.name] = p;
        }
        return m;
    }, [points]);

    // Force the GeoJSON layer to re-render whenever the data behind it changes,
    // because GeoJSON in react-leaflet caches its style function on mount.
    const geoJsonKey = `${disease}|${year}|${week}|${Object.keys(riskScores).length}`;

    return (
        <div className="relative h-full">
            {loading && (
                <div className="absolute top-2 right-2 z-[1000] text-xs px-2 py-1 rounded bg-white/90 border border-slate-200 text-slate-600">
                    loading…
                </div>
            )}
            {error && (
                <div className="absolute top-2 left-2 z-[1000] text-xs px-2 py-1 rounded bg-red-50 border border-red-200 text-red-700">
                    {error}
                </div>
            )}
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

                {/* Choropleth polygons (under circles, semi-transparent) */}
                {geoJson && (
                    <GeoJSON
                        key={geoJsonKey}
                        data={geoJson}
                        style={(feature) => {
                            const canon = feature.properties.canonical_name;
                            const p = riskByName[canon];
                            const fill = RISK_COLORS[p?.risk?.risk_class] || '#cbd5e1';
                            return {
                                color: '#475569',
                                weight: 1,
                                fillColor: fill,
                                fillOpacity: p?.risk ? 0.35 : 0.10,
                            };
                        }}
                        onEachFeature={(feature, layer) => {
                            const canon = feature.properties.canonical_name;
                            const p = riskByName[canon];
                            const body = `<div class="text-xs">
                                <div class="font-semibold">${canon}</div>
                                <div>Cases this week: <b>${p?.cases ?? 0}</b></div>
                                ${p?.risk ? `<div>RF risk: <b style="color:${RISK_COLORS[p.risk.risk_class]}">${p.risk.risk_class}</b></div>
                                <div>5-yr mean: ${p.risk.mean_5yr}</div>
                                <div>Threshold: ${p.risk.threshold}</div>` : ''}
                            </div>`;
                            layer.bindTooltip(body, { sticky: true, opacity: 0.95 });
                        }}
                    />
                )}

                {/* Case-count circles on top, sized by sqrt(cases) */}
                {points.map((p) => p.cases > 0 && (
                    <CircleMarker
                        key={p.id}
                        center={[p.lat, p.lng]}
                        radius={radiusFor(p.cases)}
                        pathOptions={{
                            color: '#1e293b',
                            fillColor: '#1e293b',
                            fillOpacity: 0.55,
                            weight: 1,
                        }}
                    >
                        <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
                            <div className="text-xs">
                                <div className="font-semibold">{p.name}</div>
                                <div>Cases this week: <b>{p.cases}</b></div>
                                {p.risk && (
                                    <>
                                        <div>RF risk: <b style={{ color: RISK_COLORS[p.risk.risk_class] }}>{p.risk.risk_class}</b></div>
                                        <div>5-yr mean: {p.risk.mean_5yr}</div>
                                        <div>Threshold: {p.risk.threshold}</div>
                                    </>
                                )}
                            </div>
                        </Tooltip>
                    </CircleMarker>
                ))}
            </MapContainer>
            <Legend hasPolygons={!!geoJson} />
        </div>
    );
}

function radiusFor(cases) {
    return 6 + Math.sqrt(cases) * 3;
}

function spreadFallback(i, n) {
    const angle = (i / n) * Math.PI * 2;
    const r = 0.025;
    return [PARANAQUE_CENTER[0] + r * Math.cos(angle), PARANAQUE_CENTER[1] + r * Math.sin(angle)];
}

function Legend({ hasPolygons }) {
    return (
        <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 border border-slate-200 rounded shadow-sm px-3 py-2 text-xs">
            <div className="font-semibold text-slate-700 mb-1">RF risk class</div>
            <LegendRow color={RISK_COLORS.High} label="High" />
            <LegendRow color={RISK_COLORS.Moderate} label="Moderate" />
            <LegendRow color={RISK_COLORS.Low} label="Low" />
            {hasPolygons ? (
                <>
                    <div className="font-semibold text-slate-700 mt-2 mb-1">Layers</div>
                    <div className="text-slate-500">polygon: barangay risk</div>
                    <div className="text-slate-500">circle: weekly cases (√ scale)</div>
                </>
            ) : (
                <>
                    <div className="font-semibold text-slate-700 mt-2 mb-1">Circle size</div>
                    <div className="text-slate-500">∝ √(weekly cases)</div>
                </>
            )}
        </div>
    );
}

function LegendRow({ color, label }) {
    return (
        <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: color }}></span>
            <span className="text-slate-700">{label}</span>
        </div>
    );
}
