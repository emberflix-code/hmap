param(
    [Parameter(Mandatory = $true)][string]$Workbook,   # e.g. docs\PIDSR Report YR 2026.xlsx
    [Parameter(Mandatory = $true)][string]$OutCsv,
    [int]$FirstWeek = 1,
    [int]$LastWeek = 52
)
# Exports CESU's own 5YrAve figures for every morbidity week (Ch.4 Level 2
# data fidelity test). A scratch COPY of the workbook is opened in Excel, the
# reporting week ('Summary Weekly Update'!N5, which 5YrAve!B2 reads) is set
# to each week in turn, the workbook recalculates its own COUNTIFS formulas,
# and the Category I and II tables are written to a CSV. The original
# workbook is never modified.

$ErrorActionPreference = 'Stop'
$src = (Resolve-Path $Workbook).Path
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("5yrave_" + [guid]::NewGuid().ToString('N') + ".xlsx")
Copy-Item $src $tmp

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add('week,category,disease,y2021_cases,y2021_deaths,y2022_cases,y2022_deaths,y2023_cases,y2023_deaths,y2024_cases,y2024_deaths,y2025_cases,y2025_deaths,y2026_cases,y2026_deaths,avg_cases,avg_deaths,median_cases,median_deaths')
try {
    $wb = $xl.Workbooks.Open($tmp)
    $control = $wb.Worksheets.Item('Summary Weekly Update')
    $sheet = $wb.Worksheets.Item('5YrAve')
    $blocks = @(@{ cat = 'I'; first = 6; last = 31 }, @{ cat = 'II'; first = 35; last = 60 })
    for ($w = $FirstWeek; $w -le $LastWeek; $w++) {
        $control.Range('N5').Value2 = $w.ToString('00')
        $xl.Calculate()
        foreach ($b in $blocks) {
            for ($r = $b.first; $r -le $b.last; $r++) {
                $name = [string]$sheet.Cells.Item($r, 1).Value2
                if ([string]::IsNullOrWhiteSpace($name) -or $name -eq '0') { continue }
                $vals = foreach ($c in 2..17) { $v = $sheet.Cells.Item($r, $c).Value2; if ($null -eq $v) { '' } else { [string]$v } }
                $rows.Add(('{0},{1},"{2}",{3}' -f $w, $b.cat, $name.Replace('"', '""'), ($vals -join ',')))
            }
        }
        Write-Host "week $w done"
    }
    $wb.Close($false)
} finally {
    $xl.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
    Remove-Item $tmp -ErrorAction SilentlyContinue
}
[IO.File]::WriteAllLines($OutCsv, $rows, (New-Object Text.UTF8Encoding($false)))
Write-Host "wrote $($rows.Count - 1) rows to $OutCsv"
