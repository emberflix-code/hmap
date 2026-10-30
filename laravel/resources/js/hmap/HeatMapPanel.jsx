import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, GeoJSON, Tooltip } from 'react-leaflet';
import L from 'leaflet';

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
            api.get('/risk-tiers', {
                params: {
                    disease_code: disease,
                    morbidity_year: year,
                    morbidity_week: week,
                },
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
                    for (const s of risk.value.data.tiers || []) {
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

    // Where each barangay's badge goes: a point inside its boundary polygon,
    // else the centroid stored in the database. A barangay with neither gets
    // no badge (it is still listed in the tooltips and the risk tiers).
    const anchors = useMemo(() => {
        const m = {};
        for (const f of geoJson?.features || []) {
            const pt = interiorPoint(f.geometry);
            if (pt) m[f.properties.canonical_name] = pt;
        }
        return m;
    }, [geoJson]);

    // Join barangay metadata (position, name) with case count + risk class
    const points = useMemo(() => {
        return barangays.map((b) => {
            const stored = b.centroid_lat != null && b.centroid_lng != null
                ? [Number(b.centroid_lat), Number(b.centroid_lng)] : null;
            const pos = anchors[b.barangay_name] || stored;
            return {
                id: b.barangay_id,
                name: b.barangay_name,
                lat: pos ? pos[0] : null,
                lng: pos ? pos[1] : null,
                cases: heatmapCounts[b.barangay_id] || 0,
                risk: riskScores[b.barangay_id],
            };
        });
    }, [barangays, heatmapCounts, riskScores, anchors]);

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
                            const fill = RISK_COLORS[p?.risk?.tier] || '#cbd5e1';
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
                                ${p?.risk ? `<div>Risk tier: <b style="color:${RISK_COLORS[p.risk.tier]}">${p.risk.tier}</b></div>
                                ${p.risk.reasons.length ? `<div>${p.risk.reasons.join('; ')}</div>` : ''}
                                <div>5-yr mean: ${p.risk.mean_5yr}</div>
                                <div>Epidemic threshold: ${p.risk.epidemic_threshold}</div>` : ''}
                            </div>`;
                            layer.bindTooltip(body, { sticky: true, opacity: 0.95 });
                        }}
                    />
                )}

                {/* Case-count badges on top: the week's count, coloured by the
                    barangay's risk tier, sized by sqrt(cases) */}
                {points.map((p) => p.cases > 0 && p.lat != null && (
                    <Marker
                        key={p.id}
                        position={[p.lat, p.lng]}
                        icon={badgeIcon(p.cases, RISK_COLORS[p.risk?.tier] || '#475569')}
                    >
                        <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
                            <div className="text-xs">
                                <div className="font-semibold">{p.name}</div>
                                <div>Cases this week: <b>{p.cases}</b></div>
                                {p.risk && (
                                    <>
                                        <div>Risk tier: <b style={{ color: RISK_COLORS[p.risk.tier] }}>{p.risk.tier}</b></div>
                                        {p.risk.reasons.length > 0 && <div>{p.risk.reasons.join('; ')}</div>}
                                        <div>5-yr mean: {p.risk.mean_5yr}</div>
                                        <div>Epidemic threshold: {p.risk.epidemic_threshold}</div>
                                    </>
                                )}
                            </div>
                        </Tooltip>
                    </Marker>
                ))}
            </MapContainer>
            <Legend hasPolygons={!!geoJson} />
        </div>
    );
}

function radiusFor(cases) {
    return 6 + Math.sqrt(cases) * 3;
}

function badgeIcon(cases, color) {
    const d = Math.round(radiusFor(cases) * 2) + 4;
    return L.divIcon({
        className: '',
        iconSize: [d, d],
        iconAnchor: [d / 2, d / 2],
        tooltipAnchor: [0, -d / 2],
        html: `<div class="case-badge" style="width:${d}px;height:${d}px;background:${color}">${cases}</div>`,
    });
}

// A [lat, lng] inside a (Multi)Polygon: the area centroid of its largest
// part when that falls inside, otherwise the middle of the widest inside
// stretch along the centroid's latitude (for C- or L-shaped barangays).
function interiorPoint(geometry) {
    if (!geometry) return null;
    const polys = geometry.type === 'Polygon' ? [geometry.coordinates]
        : geometry.type === 'MultiPolygon' ? geometry.coordinates : [];
    let best = null;
    let bestArea = 0;
    for (const poly of polys) {
        const ring = poly[0];
        let a = 0, cx = 0, cy = 0;
        for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            const f = ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
            a += f;
            cx += (ring[j][0] + ring[i][0]) * f;
            cy += (ring[j][1] + ring[i][1]) * f;
        }
        if (Math.abs(a) > bestArea) {
            bestArea = Math.abs(a);
            best = { ring, x: cx / (3 * a), y: cy / (3 * a) };
        }
    }
    if (!best) return null;
    const { ring, x, y } = best;
    if (insideRing(ring, x, y)) return [y, x];
    // crossings of the horizontal line through y; take the widest inside span
    const xs = [];
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [x1, y1] = ring[j];
        const [x2, y2] = ring[i];
        if ((y1 > y) !== (y2 > y)) xs.push(x1 + ((y - y1) / (y2 - y1)) * (x2 - x1));
    }
    xs.sort((p, q) => p - q);
    let span = null;
    for (let k = 0; k + 1 < xs.length; k += 2) {
        if (!span || xs[k + 1] - xs[k] > span[1] - span[0]) span = [xs[k], xs[k + 1]];
    }
    return span ? [y, (span[0] + span[1]) / 2] : [y, x];
}

function insideRing(ring, x, y) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, yi] = ring[i];
        const [xj, yj] = ring[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
}

function Legend({ hasPolygons }) {
    return (
        <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 border border-slate-200 rounded shadow-sm px-3 py-2 text-xs">
            <div className="font-semibold text-slate-700 mb-1">Risk tier (rule-based)</div>
            <LegendRow color={RISK_COLORS.High} label="High" />
            <LegendRow color={RISK_COLORS.Moderate} label="Moderate" />
            <LegendRow color={RISK_COLORS.Low} label="Low" />
            {hasPolygons ? (
                <>
                    <div className="font-semibold text-slate-700 mt-2 mb-1">Layers</div>
                    <div className="text-slate-500">polygon: barangay risk</div>
                    <div className="text-slate-500">badge: cases this week</div>
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
