param([string]$docx, [string]$pdf)
# Converts a .docx to PDF with Microsoft Word, so pagination matches what Word prints.
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docx, $false, $true)
    $doc.SaveAs([ref]$pdf, [ref]17)
    $doc.Close($false)
} finally {
    $word.Quit()
}
