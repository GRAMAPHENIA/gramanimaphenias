<#
Secuencia PNG -> mp4 H.264 (yuv420p, apto para YouTube/Instagram), con audio opcional.

Uso: .\scripts\encode.ps1 -Pattern renders\prueba\f_%04d.png -Out renders\prueba\prueba.mp4
Con audio y el bucle repetido 3 veces (el audio debe durar lo mismo que la animación para que cierre sin corte):
     .\scripts\encode.ps1 -Pattern renders\002\f_%04d.png -Out renders\002\columnas.mp4 `
        -Audio experimentos\002-columnas-cenital\sonido\sonido_002_v2b_pentatonica-menor.wav -Repetir 3
#>
param(
  [Parameter(Mandatory)][string]$Pattern,
  [Parameter(Mandatory)][string]$Out,
  [int]$Fps = 24,
  [int]$Crf = 18,
  [string]$Audio,        # opcional: WAV (u otro audio) que se mezcla en el mp4
  [int]$Repetir = 1      # cuántas veces se repite el bucle (video y audio)
)
$bucle = @()
if ($Repetir -gt 1) { $bucle = @('-stream_loop', ($Repetir - 1)) }

$entradas = @('-framerate', $Fps) + $bucle + @('-i', $Pattern)
$salida = @('-c:v', 'libx264', '-preset', 'slow', '-crf', $Crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart')
if ($Audio) {
  $entradas += $bucle + @('-i', $Audio)
  $salida += @('-c:a', 'aac', '-b:a', '192k', '-shortest')
}
ffmpeg -y @entradas @salida $Out
