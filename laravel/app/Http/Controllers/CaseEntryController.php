<?php

namespace App\Http\Controllers;

use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Validation\ValidationException;

/**
 * Module 1 — Data Digitization. PIDSR-aligned line-list intake.
 *
 * Two endpoints, both Encoder+ gated by the HRMO middleware:
 *   POST /api/cases       — single-case insert
 *   POST /api/cases/bulk  — CSV upload (multipart/form-data, file=csv)
 *
 * Both write to hmap_db.cases and append to hmap_db.audit_log per RA 10173.
 */
class CaseEntryController extends Controller
{
    private const CLASSIFICATIONS = ['Suspect', 'Probable', 'Confirmed', 'Discarded', 'Negative', 'Compatible', 'Pending'];
    private const SEXES = ['Male', 'Female', 'Unknown'];
    private const OUTCOMES = ['Alive', 'Died', 'Unknown'];
    private const AGE_GROUPS = ['0-4', '5-9', '10-14', '15-19', '20-59', '60+'];
    private const GEOCODE_SOURCES = [
        'nominatim_street', 'nominatim_subd', 'nominatim_bgy_centroid',
        'manual_pin', 'failed',
    ];

    public function store(Request $request): JsonResponse
    {
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $ip = $request->ip();

        $validated = $this->validatePayload($request->all());

        DB::beginTransaction();
        try {
            [$caseId, $row] = $this->insertCase($validated, $employeeId);
            $this->writeAuditLog($employeeId, 'INSERT', 'cases', $caseId, null, $row, $ip);
            $this->insertAddressIfPresent($caseId, $validated);
            DB::commit();
        } catch (\Throwable $e) {
            DB::rollBack();
            throw $e;
        }

        return response()->json([
            'case_id' => $caseId,
            'status'  => 'inserted',
        ], 201);
    }

    public function bulk(Request $request): JsonResponse
    {
        $request->validate([
            'csv' => 'required|file|mimes:csv,txt|max:10240',  // 10 MB cap
        ]);

        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $ip = $request->ip();

        $path = $request->file('csv')->getRealPath();
        $handle = fopen($path, 'r');
        if ($handle === false) {
            return response()->json(['error' => 'Could not read uploaded file'], 422);
        }

        $headerRow = fgetcsv($handle);
        if (!$headerRow) {
            fclose($handle);
            return response()->json(['error' => 'Empty CSV'], 422);
        }

        $headers = array_map(fn ($h) => strtolower(trim($h)), $headerRow);
        $required = ['disease_code', 'case_classification', 'date_onset',
                     'barangay_name', 'age', 'sex', 'outcome', 'morbidity_week', 'morbidity_year'];
        $missing = array_diff($required, $headers);
        if ($missing) {
            fclose($handle);
            return response()->json([
                'error' => 'CSV is missing required columns: ' . implode(', ', $missing),
                'expected_headers' => $required,
            ], 422);
        }

        $rowsInserted = 0;
        $errors = [];
        $rowNumber = 1; // header is row 1; data starts at 2

        DB::beginTransaction();
        try {
            while (($cells = fgetcsv($handle)) !== false) {
                $rowNumber++;
                if (count($cells) < count($headers)) {
                    $errors[] = ['row' => $rowNumber, 'error' => 'too few columns'];
                    continue;
                }
                $payload = array_combine($headers, array_map('trim', array_slice($cells, 0, count($headers))));
                try {
                    $validated = $this->validatePayload($payload);
                    [$caseId, $row] = $this->insertCase($validated, $employeeId);
                    $this->writeAuditLog($employeeId, 'INSERT', 'cases', $caseId, null, $row, $ip);
                    $rowsInserted++;
                } catch (ValidationException $e) {
                    $errors[] = ['row' => $rowNumber, 'error' => $e->errors()];
                } catch (\Throwable $e) {
                    $errors[] = ['row' => $rowNumber, 'error' => $e->getMessage()];
                }
            }
            DB::commit();
        } catch (\Throwable $e) {
            DB::rollBack();
            fclose($handle);
            Log::error('Bulk CSV ingest failed: ' . $e->getMessage());
            return response()->json([
                'error' => 'Transaction rolled back: ' . $e->getMessage(),
                'rows_inserted' => 0,
            ], 500);
        }

        fclose($handle);

        return response()->json([
            'rows_inserted' => $rowsInserted,
            'rows_failed' => count($errors),
            'errors' => $errors,
        ]);
    }

    /**
     * Returns the validated, normalized fields plus the resolved disease_id and barangay_id.
     *
     * Inputs use human-readable keys (disease_code, barangay_name) so the form and
     * CSV can stay PIDSR-friendly. We translate to the FK IDs here.
     */
    private function validatePayload(array $input): array
    {
        // CSV rows often have empty cells for optional fields ('' instead of null).
        // Coerce empty strings to null so Laravel's 'nullable' rules trigger and
        // we don't ship '' to MySQL DATE columns.
        $input = array_map(fn ($v) => is_string($v) && trim($v) === '' ? null : $v, $input);

        // Normalize CSV-style snake_case + accept the form's camelCase via aliasing
        $aliases = [
            'diseaseCode' => 'disease_code',
            'caseClassification' => 'case_classification',
            'dateOnset' => 'date_onset',
            'dateAdmitted' => 'date_admitted',
            'dateReported' => 'date_reported',
            'barangayName' => 'barangay_name',
            'facilityName' => 'facility_name',
            'morbidityWeek' => 'morbidity_week',
            'morbidityMonth' => 'morbidity_month',
            'morbidityYear' => 'morbidity_year',
            'ageGroup' => 'age_group',
        ];
        foreach ($aliases as $from => $to) {
            if (array_key_exists($from, $input) && !array_key_exists($to, $input)) {
                $input[$to] = $input[$from];
            }
        }

        $validator = validator($input, [
            'disease_code'        => 'required|string|max:20',
            'case_classification' => 'required|in:' . implode(',', self::CLASSIFICATIONS),
            'date_onset'          => 'nullable|date',
            'date_admitted'       => 'nullable|date',
            'date_reported'       => 'nullable|date',
            'barangay_name'       => 'required|string|max:80',
            'facility_name'       => 'nullable|string|max:120',
            'age'                 => 'nullable|integer|min:0|max:130',
            'age_group'           => 'nullable|in:' . implode(',', self::AGE_GROUPS),
            'sex'                 => 'nullable|in:' . implode(',', self::SEXES),
            'outcome'             => 'nullable|in:' . implode(',', self::OUTCOMES),
            'morbidity_week'      => 'required|integer|min:1|max:53',
            'morbidity_month'     => 'nullable|integer|min:1|max:12',
            'morbidity_year'      => 'required|integer|min:2010|max:2100',
            // Address fields (optional — barangay-only entries still work, but
            // a street_purok is needed for cluster detection participation).
            'street_purok'        => 'nullable|string|max:255',
            'case_lat'            => 'nullable|numeric|between:-90,90',
            'case_lng'            => 'nullable|numeric|between:-180,180',
            'geocode_source'      => 'nullable|in:' . implode(',', self::GEOCODE_SOURCES),
            'geocode_query'       => 'nullable|string|max:255',
            'geocode_formatted'   => 'nullable|string|max:255',
        ]);
        $validator->validate();
        $data = $validator->validated();

        // Resolve disease_code → disease_id
        $disease = DB::table('diseases')->where('disease_code', $data['disease_code'])->first(['disease_id']);
        if (!$disease) {
            throw ValidationException::withMessages(['disease_code' => "Unknown disease_code {$data['disease_code']}"]);
        }
        $data['disease_id'] = $disease->disease_id;

        // Resolve barangay_name → barangay_id (case-insensitive match)
        $barangay = DB::table('barangays')
            ->whereRaw('LOWER(barangay_name) = LOWER(?)', [$data['barangay_name']])
            ->first(['barangay_id']);
        if (!$barangay) {
            throw ValidationException::withMessages(['barangay_name' => "Unknown barangay {$data['barangay_name']}"]);
        }
        $data['barangay_id'] = $barangay->barangay_id;

        // Auto-derive age_group if not provided
        if (empty($data['age_group']) && isset($data['age'])) {
            $data['age_group'] = $this->ageGroupFor((int) $data['age']);
        }

        // Auto-derive morbidity_month if not provided
        if (empty($data['morbidity_month'])) {
            $data['morbidity_month'] = min(12, intdiv((int) $data['morbidity_week'] - 1, 4) + 1);
        }

        return $data;
    }

    private function insertCase(array $data, int $employeeId): array
    {
        $row = [
            'disease_id'          => $data['disease_id'],
            'case_classification' => $data['case_classification'],
            'date_onset'          => $data['date_onset'] ?? null,
            'date_admitted'       => $data['date_admitted'] ?? null,
            'date_reported'       => $data['date_reported'] ?? Carbon::today()->toDateString(),
            'barangay_id'         => $data['barangay_id'],
            'facility_id'         => null,
            'age'                 => $data['age'] ?? null,
            'age_group'           => $data['age_group'] ?? null,
            'sex'                 => $data['sex'] ?? null,
            'outcome'             => $data['outcome'] ?? 'Unknown',
            'morbidity_week'      => $data['morbidity_week'],
            'morbidity_month'     => $data['morbidity_month'],
            'morbidity_year'      => $data['morbidity_year'],
            'entered_by'          => $employeeId,
        ];

        $caseId = DB::table('cases')->insertGetId($row);
        return [$caseId, $row];
    }

    private function writeAuditLog(int $employeeId, string $action, string $table, int $targetId,
                                    ?array $oldValues, ?array $newValues, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => $table,
            'target_id'    => $targetId,
            'old_values'   => $oldValues ? json_encode($oldValues) : null,
            'new_values'   => $newValues ? json_encode($newValues) : null,
            'ip_address'   => $ip,
        ]);
    }

    /**
     * Persist the address row for a new case. Idempotent for the case_addresses
     * 1:1 relationship — uses insertOrIgnore so a stale row from a prior ETL
     * load wouldn't block a fresh case entry. Skipped entirely if the form
     * did not include a street_purok (barangay-only case, won't cluster).
     */
    private function insertAddressIfPresent(int $caseId, array $data): void
    {
        $street = $data['street_purok'] ?? null;
        if ($street === null || trim($street) === '') {
            return;
        }
        // If the geocoder didn't return coords, record 'failed' so cluster
        // detection knows the address was attempted (matches the ETL behavior).
        $source = $data['geocode_source'] ?? 'failed';
        $lat = isset($data['case_lat']) ? (float) $data['case_lat'] : null;
        $lng = isset($data['case_lng']) ? (float) $data['case_lng'] : null;
        if ($lat === null || $lng === null) {
            $source = 'failed';
        }
        DB::table('case_addresses')->insert([
            'case_id'           => $caseId,
            'raw_street_purok'  => mb_substr($street, 0, 255),
            'case_lat'          => $lat,
            'case_lng'          => $lng,
            'geocode_source'    => $source,
            'geocode_query'     => isset($data['geocode_query'])
                ? mb_substr($data['geocode_query'], 0, 255)
                : null,
            'geocode_formatted' => isset($data['geocode_formatted'])
                ? mb_substr($data['geocode_formatted'], 0, 255)
                : null,
        ]);
    }

    private function ageGroupFor(int $age): string
    {
        if ($age < 5) return '0-4';
        if ($age < 10) return '5-9';
        if ($age < 15) return '10-14';
        if ($age < 20) return '15-19';
        if ($age < 60) return '20-59';
        return '60+';
    }
}
