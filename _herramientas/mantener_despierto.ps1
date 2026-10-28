# Mantiene el equipo despierto (sin suspension y con pantalla encendida) mientras este script corra.
# No cambia la configuracion de energia: al terminar el proceso, Windows vuelve a su comportamiento normal.
param([int]$Horas = 14)

Add-Type -Namespace Win32 -Name Power -MemberDefinition @'
[DllImport("kernel32.dll")]
public static extern uint SetThreadExecutionState(uint esFlags);
'@

# ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
$flags = [uint32]'0x80000003'
$fin = (Get-Date).AddHours($Horas)
"Mantener despierto: inicio $(Get-Date -Format 'HH:mm:ss'), termina a mas tardar $($fin.ToString('dd-MM HH:mm')) (PID $PID)"

while ((Get-Date) -lt $fin) {
    [void][Win32.Power]::SetThreadExecutionState($flags)
    Start-Sleep -Seconds 60
}

[void][Win32.Power]::SetThreadExecutionState([uint32]'0x80000000')
"Mantener despierto: terminado $(Get-Date -Format 'HH:mm:ss')"
