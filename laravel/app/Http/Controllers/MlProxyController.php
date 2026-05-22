<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Thin proxy in front of the FastAPI ML microservice (Prophet + Random Forest).
 *
 * The ML service binds to 127.0.0.1:5000 in production (per docs/architecture.md)
 * and is NOT exposed externally. The frontend talks to Laravel; Laravel talks to
 * FastAPI. This keeps HRMO session enforcement at one place — here.
 */
class MlProxyController extends Controller
{
    public function forecast(Request $request): JsonResponse
    {
        return $this->forward('/predict/forecast', $request->validate([
            'disease_code' => 'required|string|max:20',
            'barangay_id'  => 'nullable|integer|min:1|max:16',
            'weeks_ahead'  => 'nullable|integer|min:1|max:12',
        ]));
    }

    public function risk(Request $request): JsonResponse
    {
        return $this->forward('/predict/risk', $request->validate([
            'disease_code'   => 'required|string|max:20',
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]));
    }

    /**
     * Single-address geocoding for the case-entry form. Proxies to FastAPI's
     * /geocode, which wraps ml/geocode.py's cache-backed Nominatim cascade.
     * Returns {success, lat, lng, geocode_source, formatted, from_cache}.
     */
    public function geocode(Request $request): JsonResponse
    {
        return $this->forward('/geocode', $request->validate([
            'street_purok' => 'required|string|max:255',
            'barangay'     => 'required|string|max:80',
        ]));
    }

    public function models(): JsonResponse
    {
        try {
            $resp = Http::timeout(5)->get(config('hmap.ml_url') . '/models');
            return response()->json($resp->json(), $resp->status());
        } catch (\Throwable $e) {
            return response()->json(['error' => 'ml_unreachable', 'detail' => $e->getMessage()], 502);
        }
    }

    public function health(): JsonResponse
    {
        try {
            $resp = Http::timeout(3)->get(config('hmap.ml_url') . '/health');
            return response()->json($resp->json(), $resp->status());
        } catch (\Throwable $e) {
            return response()->json(['status' => 'ml_unreachable', 'detail' => $e->getMessage()], 502);
        }
    }

    private function forward(string $path, array $payload): JsonResponse
    {
        try {
            $resp = Http::timeout(15)
                ->acceptJson()
                ->asJson()
                ->post(config('hmap.ml_url') . $path, $payload);
        } catch (\Throwable $e) {
            Log::error("ML proxy {$path} failed: " . $e->getMessage());
            return response()->json(['error' => 'ml_unreachable', 'detail' => $e->getMessage()], 502);
        }

        return response()->json($resp->json(), $resp->status());
    }
}
