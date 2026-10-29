<?php

namespace App\Console\Commands;

use App\Services\Mfa;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

/**
 * Removes an employee's authenticator enrollment (lost or replaced phone,
 * and no recovery codes left). Their verified sessions end at once, and on
 * the next login they set up the authenticator again.
 *
 *   php artisan hmap:mfa-reset 1042 --by=1001
 */
class MfaReset extends Command
{
    protected $signature = 'hmap:mfa-reset {employee_id : employee whose authenticator is reset}
                            {--by= : employee ID of the Administrator who approved the reset}';

    protected $description = 'Reset a CESU staff member\'s multi-factor authentication';

    public function handle(): int
    {
        $id = (int) $this->argument('employee_id');
        $by = (int) $this->option('by');
        if (!$by || DB::table('user_roles')->where('employee_id', $by)->where('role', 'Administrator')
                ->where('is_active', 1)->doesntExist()) {
            $this->error('--by must be the employee ID of an active CESU Administrator.');
            return 1;
        }
        if (!DB::table('user_mfa')->where('employee_id', $id)->delete()) {
            $this->warn("Employee {$id} has no authenticator set up; nothing to reset.");
            return 0;
        }
        Mfa::clearFailures($id);
        Mfa::audit($by, null, 'MFA_RESET', ['employee_id' => $id]);
        $this->info("Authenticator removed for employee {$id}. They will set it up again at next login.");
        return 0;
    }
}
