<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;

/**
 * Backup register (Module 9). Read-only view of backup_log, written by
 * ml/backup_db.py: when each encrypted backup ran, its size and checksum,
 * and whether its latest test restoration passed. Backups themselves are
 * created, verified, and restored only from the server shell.
 */
class BackupsController extends Controller
{
    public function index(): JsonResponse
    {
        $rows = DB::table('backup_log')
            ->select('backup_id', 'started_at', 'finished_at', 'status', 'error',
                     'file_size_bytes', 'sha256', 'verified_at', 'verify_status',
                     'verify_detail', 'deleted_at')
            ->orderByDesc('started_at')
            ->limit(30)
            ->get();

        $lastSuccess = $rows->firstWhere('status', 'success');
        $lastVerified = $rows->first(function ($r) {
            return $r->verified_at !== null;
        });

        return response()->json([
            'last_success_at'      => $lastSuccess->finished_at ?? null,
            'last_verified_at'     => $lastVerified->verified_at ?? null,
            'last_verify_status'   => $lastVerified->verify_status ?? null,
            'backups'              => $rows->map(function ($r) {
                return [
                    'backup_id'       => (int) $r->backup_id,
                    'started_at'      => $r->started_at,
                    'finished_at'     => $r->finished_at,
                    'status'          => $r->status,
                    'error'           => $r->error,
                    'file_size_bytes' => $r->file_size_bytes !== null ? (int) $r->file_size_bytes : null,
                    'sha256'          => $r->sha256,
                    'verified_at'     => $r->verified_at,
                    'verify_status'   => $r->verify_status,
                    'verify_detail'   => $r->verify_detail,
                    'file_pruned'     => $r->deleted_at !== null,
                ];
            }),
        ]);
    }
}
