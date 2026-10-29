<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;

/**
 * The weekly dengue memo template (Weekly Report > Memo draft), editable by
 * the Administrator so CESU can update recipients, signatory and wording
 * when officials change, without a code change.
 *
 * The template is plain text with {placeholders} that the generator fills
 * from the week's data; the list below is what the editor shows. An
 * unknown placeholder is left as written, so a typo is visible in the draft
 * rather than silently dropped. With no saved template, DEFAULT is used.
 */
class MemoTemplate
{
    const KEY = 'dengue_weekly';

    const PLACEHOLDERS = [
        'week'                => 'Morbidity week number',
        'year'                => 'Morbidity year',
        'today'               => "Today's date",
        'date_range'          => 'Reporting period, e.g. January 1 to February 1, 2025',
        'cases'               => 'Dengue cases this year to date',
        'prev_cases'          => 'Cases in the same period last year',
        'change'              => 'Comparison with last year, e.g. "12% higher than"',
        'deaths'              => 'Deaths this year to date',
        'cfr'                 => 'Case fatality rate this year',
        'barangay_paragraph'  => 'Sentence on the barangays with the highest rate per 10,000',
        'age_paragraph'       => 'Sentence on the age range and median',
        'age_group_paragraph' => 'Sentence on the most affected age group',
        'dru_paragraph'       => 'Sentence on the facilities reporting the most cases',
        'males'               => 'Male cases',
        'males_pct'           => 'Male share (%)',
        'females'             => 'Female cases',
        'females_pct'         => 'Female share (%)',
    ];

    const DEFAULT = <<<'TPL'
TO:     DARIUS J. SEBASTIAN, MD, PHSAE, MPH — Medical Officer V, OIC, City Health Office
        DR. DARWIN DAVID                  — Dengue Program Coordinator
        DR. FRANCISCO GOZOS II            — Head, Sanitation Division
        DIR. MARCO A.G. CABUENOS, JR.     — DILG-OIC, City Director
        DR. REGINALD SANTOS               — Infection Control Program Coordinator

FROM:   DARIUS J. SEBASTIAN, MD, PHSAE, MPH
        City Epidemiologist

RE:     Dengue Updates in Parañaque City, Morbidity Week {week}

DATE:   {today}

Time Period:   {date_range}
Data Source:   Philippine Integrated Disease Surveillance and Response (via the CESU Disease Outbreak Management System)


A. Dengue

There were {cases} cases reported from {date_range}. This is {change} the same period
last year ({prev_cases} cases). Total deaths to date: {deaths} (CFR {cfr}).

{barangay_paragraph}

{age_paragraph} {age_group_paragraph}

{dru_paragraph}

Sex distribution: {males} male ({males_pct}%), {females} female ({females_pct}%).

— Generated from PIDSR Registry data. Review and edit before sending.

TPL;

    /** The saved template row, or null when the default is in use. */
    public static function saved(): ?object
    {
        return DB::table('memo_templates')->where('template_key', self::KEY)->first();
    }

    public static function body(): string
    {
        $row = self::saved();
        return $row ? $row->body : self::DEFAULT;
    }

    /** Fill {placeholders} with $values (keys without braces). */
    public static function render(string $body, array $values): string
    {
        $map = [];
        foreach ($values as $k => $v) {
            $map['{' . $k . '}'] = (string) $v;
        }
        return strtr($body, $map);
    }

    /** Placeholders used in $body that the generator does not know. */
    public static function unknownPlaceholders(string $body): array
    {
        preg_match_all('/\{([a-z_]+)\}/', $body, $m);
        return array_values(array_diff(array_unique($m[1]), array_keys(self::PLACEHOLDERS)));
    }
}
