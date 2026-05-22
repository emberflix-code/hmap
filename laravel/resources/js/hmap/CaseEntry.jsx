import React, { useEffect, useMemo, useRef, useState } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, TileLayer, useMap } from 'react-leaflet';

// Leaflet's default icon URLs break with bundlers because the CSS resolves
// them relative to the leaflet package, but Vite emits hashed asset names.
// Point Leaflet at the URLs Vite gives us so the marker actually appears
// instead of rendering as a broken-image square.
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

const CLASSIFICATIONS = ['Suspect', 'Probable', 'Confirmed', 'Discarded', 'Negative', 'Compatible', 'Pending'];
const SEXES = ['Male', 'Female', 'Unknown'];
const OUTCOMES = ['Alive', 'Died', 'Unknown'];

// How the encoder sees each geocode_source — keep human-readable.
const SOURCE_LABELS = {
    nominatim_street:       { label: 'Street-level match',      color: 'emerald' },
    nominatim_subd:         { label: 'Subdivision-level match', color: 'emerald' },
    nominatim_bgy_centroid: { label: 'Approximate (barangay centroid) — drag pin to correct', color: 'amber' },
    manual_pin:             { label: 'Manually pinned',         color: 'blue' },
    failed:                 { label: 'Geocoding failed',        color: 'rose' },
};

export default function CaseEntry({ api, diseases, barangays }) {
    const today = useMemo(() => isoMorbidityWeek(new Date()), []);
    const [tab, setTab] = useState('single');

    return (
        <div className="p-6 max-w-5xl mx-auto">
            <div className="flex items-center gap-1 mb-4 border-b border-slate-200">
                <TabButton active={tab === 'single'} onClick={() => setTab('single')}>
                    Single case
                </TabButton>
                <TabButton active={tab === 'csv'} onClick={() => setTab('csv')}>
                    CSV bulk upload
                </TabButton>
            </div>

            {tab === 'single' ? (
                <SingleCaseForm
                    api={api}
                    diseases={diseases}
                    barangays={barangays}
                    today={today}
                />
            ) : (
                <BulkCsvUploader api={api} />
            )}
        </div>
    );
}

function TabButton({ active, onClick, children }) {
    return (
        <button
            type="button"
            className={
                'px-4 py-2 text-sm font-medium border-b-2 ' +
                (active
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-slate-600 hover:text-slate-800 hover:bg-slate-50')
            }
            onClick={onClick}
        >
            {children}
        </button>
    );
}

function SingleCaseForm({ api, diseases, barangays, today }) {
    const [form, setForm] = useState({
        disease_code: 'DENGUE',
        case_classification: 'Suspect',
        date_onset: '',
        date_admitted: '',
        barangay_name: barangays[0]?.barangay_name || '',
        age: '',
        sex: '',
        outcome: 'Alive',
        morbidity_year: today.year,
        morbidity_week: today.week,
        // Address / geocoding fields. Filled in by the LocateAddress widget.
        street_purok: '',
        case_lat: null,
        case_lng: null,
        geocode_source: '',
        geocode_query: '',
        geocode_formatted: '',
    });
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    function update(field) {
        return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
    }

    // Called by the LocateAddress widget when the encoder confirms or moves
    // the pin. We keep the raw geocode result here so submit() can pass it
    // straight to the backend without re-querying.
    function setGeocode(g) {
        setForm((f) => ({
            ...f,
            case_lat: g.lat,
            case_lng: g.lng,
            geocode_source: g.geocode_source,
            geocode_query: g.geocode_query || '',
            geocode_formatted: g.formatted || '',
        }));
    }

    // Reset coords + source when the encoder edits the address text or switches
    // barangay; the prior geocode no longer applies and we don't want to
    // submit a stale pin.
    function updateStreet(e) {
        setForm((f) => ({
            ...f,
            street_purok: e.target.value,
            case_lat: null, case_lng: null,
            geocode_source: '', geocode_query: '', geocode_formatted: '',
        }));
    }
    function updateBarangay(e) {
        setForm((f) => ({
            ...f,
            barangay_name: e.target.value,
            case_lat: null, case_lng: null,
            geocode_source: '', geocode_query: '', geocode_formatted: '',
        }));
    }

    async function submit(e) {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        setResult(null);
        try {
            // Filter empty optional fields so server validation 'nullable' rules kick in
            const payload = Object.fromEntries(
                Object.entries(form).filter(([, v]) => v !== '' && v !== null)
            );
            if (payload.age !== undefined) payload.age = parseInt(payload.age, 10);
            payload.morbidity_year = parseInt(payload.morbidity_year, 10);
            payload.morbidity_week = parseInt(payload.morbidity_week, 10);

            const r = await api.post('/cases', payload);
            setResult(r.data);
        } catch (err) {
            const detail = err.response?.data;
            if (detail?.errors) {
                setError(
                    Object.entries(detail.errors)
                        .map(([f, msgs]) => `${f}: ${Array.isArray(msgs) ? msgs.join('; ') : msgs}`)
                        .join('\n')
                );
            } else {
                setError(detail?.message || err.message);
            }
        } finally {
            setSubmitting(false);
        }
    }

    const selectedBarangay = useMemo(
        () => barangays.find((b) => b.barangay_name === form.barangay_name),
        [barangays, form.barangay_name],
    );

    return (
        <form onSubmit={submit} className="bg-white rounded-lg border border-slate-200 shadow-sm">
            <div className="px-5 py-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">PIDSR case record</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                    All fields match PIDSR's standard case report form (DOH, 2014).
                </p>
            </div>

            <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label="Disease" required>
                    <select className={fieldClass} value={form.disease_code} onChange={update('disease_code')}>
                        {diseases.map((d) => (
                            <option key={d.disease_code} value={d.disease_code}>{d.disease_name}</option>
                        ))}
                    </select>
                </Field>
                <Field label="Case classification" required>
                    <select className={fieldClass} value={form.case_classification} onChange={update('case_classification')}>
                        {CLASSIFICATIONS.map((c) => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                </Field>
                <Field label="Barangay" required>
                    <select className={fieldClass} value={form.barangay_name} onChange={updateBarangay}>
                        {barangays.map((b) => (
                            <option key={b.barangay_id} value={b.barangay_name}>{b.barangay_name}</option>
                        ))}
                    </select>
                </Field>
                <Field label="Outcome">
                    <select className={fieldClass} value={form.outcome} onChange={update('outcome')}>
                        {OUTCOMES.map((o) => (
                            <option key={o} value={o}>{o}</option>
                        ))}
                    </select>
                </Field>

                <div className="md:col-span-2">
                    <LocateAddress
                        api={api}
                        streetPurok={form.street_purok}
                        onStreetChange={updateStreet}
                        barangay={form.barangay_name}
                        barangayCentroid={selectedBarangay}
                        geocode={{
                            lat: form.case_lat,
                            lng: form.case_lng,
                            geocode_source: form.geocode_source,
                            formatted: form.geocode_formatted,
                            geocode_query: form.geocode_query,
                        }}
                        onGeocode={setGeocode}
                    />
                </div>

                <Field label="Date of onset">
                    <input type="date" className={fieldClass} value={form.date_onset} onChange={update('date_onset')} />
                </Field>
                <Field label="Date admitted">
                    <input type="date" className={fieldClass} value={form.date_admitted} onChange={update('date_admitted')} />
                </Field>

                <Field label="Age (years)">
                    <input type="number" min={0} max={130} className={fieldClass} value={form.age} onChange={update('age')} />
                </Field>
                <Field label="Sex">
                    <select className={fieldClass} value={form.sex} onChange={update('sex')}>
                        <option value="">—</option>
                        {SEXES.map((s) => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                </Field>

                <Field label="Morbidity year" required>
                    <input type="number" min={2010} max={2100} className={fieldClass} value={form.morbidity_year} onChange={update('morbidity_year')} />
                </Field>
                <Field label="Morbidity week" required>
                    <input type="number" min={1} max={53} className={fieldClass} value={form.morbidity_week} onChange={update('morbidity_week')} />
                </Field>
            </div>

            <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between bg-slate-50">
                <div className="text-xs">
                    {result && (
                        <span className="text-emerald-700">
                            Saved as case #{result.case_id} ✓
                        </span>
                    )}
                    {error && (
                        <pre className="text-rose-700 whitespace-pre-wrap">{error}</pre>
                    )}
                </div>
                <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:bg-slate-400"
                >
                    {submitting ? 'Saving…' : 'Save case'}
                </button>
            </div>
        </form>
    );
}

function BulkCsvUploader({ api }) {
    const [file, setFile] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    async function submit(e) {
        e.preventDefault();
        if (!file) return;
        setSubmitting(true);
        setError(null);
        setResult(null);
        try {
            const fd = new FormData();
            fd.append('csv', file);
            const r = await api.post('/cases/bulk', fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(r.data);
        } catch (err) {
            setError(err.response?.data?.error || err.message);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
            <div className="px-5 py-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">CSV bulk upload</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                    PIDSR-compatible template. Required columns: <code>disease_code, case_classification,
                    date_onset, barangay_name, age, sex, outcome, morbidity_week, morbidity_year</code>.
                    Optional: <code>date_admitted, age_group, morbidity_month, facility_name</code>.
                </p>
            </div>
            <form onSubmit={submit} className="p-5">
                <input
                    type="file"
                    accept=".csv,text/csv"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="block text-sm"
                />
                <div className="mt-4 flex items-center gap-3">
                    <button
                        type="submit"
                        disabled={!file || submitting}
                        className="px-4 py-2 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:bg-slate-400"
                    >
                        {submitting ? 'Uploading…' : 'Upload CSV'}
                    </button>
                    <a
                        href="/cases-template.csv"
                        className="text-xs text-blue-700 underline hover:text-blue-800"
                        download
                    >
                        Download template
                    </a>
                </div>

                {error && (
                    <div className="mt-4 p-3 rounded bg-rose-50 border border-rose-200 text-sm text-rose-700">
                        {error}
                    </div>
                )}
                {result && (
                    <div className="mt-4">
                        <div className="p-3 rounded bg-emerald-50 border border-emerald-200 text-sm text-emerald-800">
                            Inserted <b>{result.rows_inserted}</b> row(s).
                            {result.rows_failed > 0 && (
                                <> <b>{result.rows_failed}</b> row(s) failed.</>
                            )}
                        </div>
                        {result.errors?.length > 0 && (
                            <details className="mt-3">
                                <summary className="cursor-pointer text-xs text-slate-600">
                                    Show {result.errors.length} error(s)
                                </summary>
                                <pre className="mt-2 p-3 text-xs bg-slate-50 border border-slate-200 rounded overflow-auto max-h-80">
                                    {JSON.stringify(result.errors, null, 2)}
                                </pre>
                            </details>
                        )}
                    </div>
                )}
            </form>
        </div>
    );
}

const fieldClass = 'w-full border border-slate-300 rounded px-2 py-1.5 text-sm text-slate-800 bg-white';

function Field({ label, required, children }) {
    return (
        <label className="flex flex-col text-xs text-slate-600">
            <span className="mb-1">
                {label}{required && <span className="text-rose-600 ml-0.5">*</span>}
            </span>
            {children}
        </label>
    );
}

/**
 * Street/purok address field + Locate button + Leaflet preview map with a
 * draggable confirmation pin.
 *
 * Workflow:
 *   1. Encoder types StreetPurok-style address (e.g. "QUIRINO AVE., 0549").
 *   2. Click "Locate" → POST /api/geocode → backend runs the cascade
 *      (cache-first; ~1.1s on miss due to Nominatim rate limit).
 *   3. Pin appears on the map at the returned coords, colored by precision.
 *      The encoder can drag the pin to correct it; dragging promotes the
 *      geocode_source to 'manual_pin' so cluster detection trusts it.
 *
 * Pin defaults to the barangay centroid if nothing has been geocoded yet —
 * gives the encoder an immediate visual anchor.
 */
function LocateAddress({
    api, streetPurok, onStreetChange, barangay, barangayCentroid,
    geocode, onGeocode,
}) {
    const [locating, setLocating] = useState(false);
    const [error, setError] = useState(null);

    const hasGeocode = geocode.lat != null && geocode.lng != null;
    const fallbackLatLng = barangayCentroid && barangayCentroid.centroid_lat != null
        ? [Number(barangayCentroid.centroid_lat), Number(barangayCentroid.centroid_lng)]
        : [14.4793, 121.0198];
    const pinLatLng = hasGeocode ? [geocode.lat, geocode.lng] : fallbackLatLng;

    async function locate() {
        if (!streetPurok || !streetPurok.trim()) {
            setError('Enter a street or purok first.');
            return;
        }
        setLocating(true);
        setError(null);
        try {
            const r = await api.post('/geocode', {
                street_purok: streetPurok.trim(),
                barangay,
            });
            const data = r.data;
            if (!data.success || data.lat == null) {
                setError('Could not locate that address. Drag the pin manually to set the location.');
                onGeocode({
                    lat: fallbackLatLng[0],
                    lng: fallbackLatLng[1],
                    geocode_source: 'manual_pin',
                    geocode_query: data.geocode_query || null,
                    formatted: data.formatted || null,
                });
                return;
            }
            onGeocode(data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Geocoding failed.');
        } finally {
            setLocating(false);
        }
    }

    return (
        <div>
            <label className="flex flex-col text-xs text-slate-600">
                <span className="mb-1">Street / Purok address</span>
                <div className="flex gap-2">
                    <input
                        type="text"
                        className={fieldClass}
                        placeholder="e.g. QUIRINO AVE., 0549"
                        value={streetPurok}
                        onChange={onStreetChange}
                    />
                    <button
                        type="button"
                        onClick={locate}
                        disabled={locating || !streetPurok.trim()}
                        className="shrink-0 px-3 py-1.5 rounded bg-slate-800 text-white text-xs font-medium hover:bg-slate-900 disabled:bg-slate-400"
                    >
                        {locating ? 'Locating…' : 'Locate'}
                    </button>
                </div>
            </label>

            {/* Precision status badge */}
            {hasGeocode && SOURCE_LABELS[geocode.geocode_source] && (
                <div className="mt-2 flex items-start gap-2 text-xs">
                    <SourceBadge source={geocode.geocode_source} />
                    {geocode.formatted && (
                        <span className="text-slate-600 italic">{geocode.formatted}</span>
                    )}
                </div>
            )}
            {error && (
                <div className="mt-2 text-xs text-rose-700">{error}</div>
            )}

            <div className="mt-2 rounded border border-slate-200 overflow-hidden" style={{ height: 280 }}>
                <MapContainer
                    center={pinLatLng}
                    zoom={hasGeocode ? 17 : 14}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                    <FlyTo center={pinLatLng} zoom={hasGeocode ? 17 : 14} />
                    {/* The pin shows as soon as any coords exist. Dragging it
                        promotes the geocode_source to manual_pin so cluster
                        detection trusts the encoder's choice. */}
                    {(hasGeocode || streetPurok.trim().length === 0) && (
                        <Marker
                            position={pinLatLng}
                            draggable={true}
                            eventHandlers={{
                                dragend: (e) => {
                                    const { lat, lng } = e.target.getLatLng();
                                    onGeocode({
                                        lat,
                                        lng,
                                        geocode_source: 'manual_pin',
                                        geocode_query: geocode.geocode_query || null,
                                        formatted: geocode.formatted || null,
                                    });
                                },
                            }}
                        />
                    )}
                </MapContainer>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
                Drag the pin to fine-tune the location. Drop accuracy improves cluster detection.
            </div>
        </div>
    );
}

function SourceBadge({ source }) {
    const info = SOURCE_LABELS[source];
    if (!info) return null;
    const palette = {
        emerald: 'bg-emerald-100 text-emerald-800',
        amber:   'bg-amber-100 text-amber-800',
        blue:    'bg-blue-100 text-blue-800',
        rose:    'bg-rose-100 text-rose-800',
    }[info.color] || 'bg-slate-100 text-slate-700';
    return (
        <span className={'px-2 py-0.5 rounded font-medium ' + palette}>{info.label}</span>
    );
}

// Smoothly re-centers the map when the parent's pinLatLng changes. Without
// this, the map's view freezes on its initial center and zoom — Leaflet
// doesn't react to the MapContainer `center` prop changing after mount.
function FlyTo({ center, zoom }) {
    const map = useMap();
    const lastRef = useRef(null);
    useEffect(() => {
        if (!center) return;
        const key = `${center[0]},${center[1]},${zoom}`;
        if (key === lastRef.current) return;
        lastRef.current = key;
        map.flyTo(center, zoom, { duration: 0.6 });
    }, [center, zoom, map]);
    return null;
}

function isoMorbidityWeek(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
    return { year: d.getUTCFullYear(), week };
}
