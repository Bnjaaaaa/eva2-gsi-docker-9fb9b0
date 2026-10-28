<#
  Captura REAL de una terminal: abre una ventana de PowerShell (conhost), escribe el
  prompt y el comando, lo ejecuta de verdad y fotografía la ventana con PrintWindow.
  Uso:
    .\capturar_terminal.ps1 -Comando "docker images" -Salida "C:\ruta\01-imagenes.png" [-Directorio D:\...] [-Espera 5] [-Columnas 140] [-Filas 35]
  -Espera: segundos que se dejan correr el comando antes de la foto (o hasta que termine).
#>
param(
    [Parameter(Mandatory)] [string] $Comando,
    [Parameter(Mandatory)] [string] $Salida,
    [string] $Directorio = (Get-Location).Path,
    [int] $Espera = 8,
    [int] $Columnas = 140,
    [int] $Filas = 35
)

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class Captura {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int attr, out RECT r, int size);
    public static void Guardar(IntPtr h, string ruta) {
        RECT w; GetWindowRect(h, out w);
        RECT f; bool dwm = DwmGetWindowAttribute(h, 9, out f, Marshal.SizeOf(typeof(RECT))) == 0;
        using (var bmp = new Bitmap(w.Right - w.Left, w.Bottom - w.Top)) {
            using (var g = Graphics.FromImage(bmp)) {
                IntPtr hdc = g.GetHdc();
                PrintWindow(h, hdc, 2); // PW_RENDERFULLCONTENT
                g.ReleaseHdc(hdc);
            }
            if (dwm) { // recorta la sombra invisible del borde
                var r = new Rectangle(f.Left - w.Left, f.Top - w.Top, f.Right - f.Left, f.Bottom - f.Top);
                using (var c = bmp.Clone(r, bmp.PixelFormat)) c.Save(ruta, ImageFormat.Png);
            } else bmp.Save(ruta, ImageFormat.Png);
        }
    }
}
"@

$marca = "[[FIN-CAPTURA-$PID-$(Get-Random)]]"
$listo = Join-Path $env:TEMP ("cap-" + [guid]::NewGuid() + ".ok")
$cmdEsc = $Comando.Replace("'", "''")
$script = @"
`$Host.UI.RawUI.WindowTitle = 'Windows PowerShell'
try { `$Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size($Columnas, 3000) } catch {}
try { `$Host.UI.RawUI.WindowSize = New-Object Management.Automation.Host.Size($Columnas, $Filas) } catch {}
Set-Location -LiteralPath '$($Directorio.Replace("'", "''"))'
Clear-Host
Write-Host -NoNewline ('PS ' + (Get-Location).Path + '> ')
Write-Host '$cmdEsc' -ForegroundColor Yellow
Invoke-Expression '$cmdEsc'
New-Item -ItemType File -Path '$listo' -Force | Out-Null
"@
$enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($script))
$p = Start-Process conhost.exe -ArgumentList "powershell.exe -NoLogo -NoProfile -NoExit -EncodedCommand $enc" -PassThru

# Espera a que exista la ventana: Windows la atribuye al proceso hijo powershell, no a conhost
$h = [IntPtr]::Zero; $hijo = $null
for ($i = 0; $i -lt 75 -and $h -eq [IntPtr]::Zero; $i++) {
    Start-Sleep -Milliseconds 200
    if (-not $hijo) {
        $c = Get-CimInstance Win32_Process -Filter "ParentProcessId=$($p.Id) AND Name='powershell.exe'" | Select-Object -First 1
        if ($c) { $hijo = Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue }
    }
    if ($hijo) { $hijo.Refresh(); $h = $hijo.MainWindowHandle }
}
if ($h -eq [IntPtr]::Zero) {
    if ($hijo) { Stop-Process -Id $hijo.Id -Force -ErrorAction SilentlyContinue }
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    throw "No se encontró la ventana de la terminal"
}

# Espera a que el comando termine (o al tiempo máximo)
$t = 0; while (-not (Test-Path $listo) -and $t -lt ($Espera * 1000)) { Start-Sleep -Milliseconds 250; $t += 250 }
$termino = Test-Path $listo
Start-Sleep -Milliseconds 700
[void][Captura]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 300
New-Item -ItemType Directory -Force (Split-Path $Salida) | Out-Null
[Captura]::Guardar($h, $Salida)

# Cierra SOLO la ventana que abrimos (por PID)
Stop-Process -Id $hijo.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
Remove-Item $listo -ErrorAction SilentlyContinue
"Captura guardada: $Salida (comando terminado: $termino)"
