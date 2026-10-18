$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$inputDoc = Join-Path $root 'LLC_Portfolio_Identification_and_Mailing_Master_Specification.docx'
$renderDir = Join-Path $root 'support\qa_master_spec\rendered'
$outputPdf = Join-Path $renderDir 'LLC_Portfolio_Identification_and_Mailing_Master_Specification.pdf'
New-Item -ItemType Directory -Force -Path $renderDir | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($inputDoc, $false, $true)
    $doc.Fields.Update() | Out-Null
    foreach ($section in $doc.Sections) {
        foreach ($header in $section.Headers) { $header.Range.Fields.Update() | Out-Null }
        foreach ($footer in $section.Footers) { $footer.Range.Fields.Update() | Out-Null }
    }
    $doc.ExportAsFixedFormat($outputPdf, 17)
    $doc.Close($false)
}
finally {
    $word.Quit()
}
Write-Output $outputPdf
