<#
Render headless con medición.
Uso: .\scripts\render.ps1 -Blend base\gramaphenia-base.blend -Start 1 -End 24 -Out renders\prueba\f_
Escribe un log con tiempo total, s/frame y pico de VRAM (nvidia-smi).
#>
param(
  [Parameter(Mandatory)][string]$Blend,
  [int]$Start = 1,
  [int]$End = 24,
  [Parameter(Mandatory)][string]$Out,
  [string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)
# Rutas absolutas: el proceso de Blender no hereda el directorio de PowerShell
$Blend = (Resolve-Path $Blend).Path
$Out = [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Out))
$outDir = Split-Path $Out -Parent
if ($outDir) { New-Item -ItemType Directory -Force $outDir | Out-Null }

$peak = 0
$sampler = Start-ThreadJob -ScriptBlock {
  $max = 0
  while ($true) {
    $v = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | Select-Object -First 1)
    if ($v -gt $max) { $max = $v }
    Set-Content "$env:TEMP\gph_vram_peak.txt" $max
    Start-Sleep -Milliseconds 500
  }
}
$sw = [Diagnostics.Stopwatch]::StartNew()
& $Blender -b $Blend -o $Out -F PNG -s $Start -e $End -a
$sw.Stop()
Stop-Job $sampler; Remove-Job $sampler -Force
$peak = Get-Content "$env:TEMP\gph_vram_peak.txt" -ErrorAction SilentlyContinue

$frames = $End - $Start + 1
$log = [ordered]@{
  fecha = (Get-Date -Format s); blend = $Blend; frames = $frames
  segundos_total = [math]::Round($sw.Elapsed.TotalSeconds, 1)
  segundos_por_frame = [math]::Round($sw.Elapsed.TotalSeconds / $frames, 2)
  vram_pico_mib = $peak
}
$log | ConvertTo-Json | Tee-Object -FilePath "$Out`_log.json"
