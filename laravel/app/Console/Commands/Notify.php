<?php

namespace App\Console\Commands;

use App\Services\Notifier;
use Illuminate\Console\Command;

/**
 * Checks for outbreak alerts and sends notifications (Module 7). Run from
 * cron every 15 minutes; safe to repeat, since each alert is sent only once
 * per disease, barangay, alert type and morbidity week.
 *
 *   php artisan hmap:notify                     current and previous morbidity week
 *   php artisan hmap:notify --year=2025 --week=30
 */
class Notify extends Command
{
    protected $signature = 'hmap:notify {--year= : morbidity year} {--week= : morbidity week}
                            {--no-send : create notifications but do not deliver them}';

    protected $description = 'Detect outbreak alerts and send email/SMS notifications';

    public function handle(): int
    {
        if ($this->option('year') || $this->option('week')) {
            if (!$this->option('year') || !$this->option('week')) {
                $this->error('Give both --year and --week, or neither.');
                return 1;
            }
            $weeks = [[(int) $this->option('year'), (int) $this->option('week')]];
        } else {
            $weeks = Notifier::weeksToCheck();
        }

        foreach ($weeks as [$year, $week]) {
            $n = Notifier::detect($year, $week);
            $this->line("MW {$week} {$year}: {$n} new notification" . ($n === 1 ? '' : 's'));
        }
        if ($this->option('no-send')) {
            return 0;
        }
        $c = Notifier::deliver();
        $this->line("deliveries: {$c['sent']} sent, {$c['failed']} failed, {$c['skipped']} skipped");
        return 0;
    }
}
