<#
  Abre un .docx con Word (COM), actualiza índice de contenido, de figuras, de tablas
  y todos los campos, guarda y exporta a PDF.
  Uso: .\word_actualizar.ps1 -Docx "C:\ruta\informe.docx" [-Pdf "C:\ruta\informe.pdf"]
#>
param([Parameter(Mandatory)] [string] $Docx, [string] $Pdf)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $d = $word.Documents.Open($Docx)
    # Índices con interlineado sencillo (estilos integrados: TDC 1-3 = -20..-22, tabla de ilustraciones = -36)
    foreach ($id in -20, -21, -22, -36) {
        $e = $d.Styles.Item($id)
        $e.ParagraphFormat.LineSpacingRule = 0      # wdLineSpaceSingle
        $e.ParagraphFormat.SpaceAfter = 4
        $e.ParagraphFormat.FirstLineIndent = 0
    }
    $d.Fields.Update() | Out-Null          # numera las leyendas (SEQ) antes de los índices
    foreach ($t in $d.TablesOfContents) { $t.Update() }
    foreach ($t in $d.TablesOfFigures) { $t.Update() }
    $d.Fields.Update() | Out-Null
    $d.Save()
    if ($Pdf) { $d.ExportAsFixedFormat($Pdf, 17) }   # 17 = wdExportFormatPDF
    "Índices: contenido=$($d.TablesOfContents.Count) figuras/tablas=$($d.TablesOfFigures.Count) | páginas=$($d.ComputeStatistics(2))"
    $d.Close()
} finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
