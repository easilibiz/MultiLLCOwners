$ErrorActionPreference = 'Stop'
$inputDoc = 'C:\Users\ofirm\OneDrive\Documents\ChatGPT\find Multi LLC owners\Chicago_LLC_Portfolio_Process_Requirements.docx'
$outputPdf = 'C:\Users\ofirm\OneDrive\Documents\ChatGPT\find Multi LLC owners\qa_llc_process\rendered\Chicago_LLC_Portfolio_Process_Requirements.pdf'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPdf) | Out-Null
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
