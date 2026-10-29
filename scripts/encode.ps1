<#
Secuencia PNG -> mp4 H.264 (yuv420p, apto para YouTube/Instagram).
Uso: .\scripts\encode.ps1 -Pattern renders\prueba\f_%04d.png -Out renders\prueba\prueba.mp4
#>
param(
  [Parameter(Mandatory)][string]$Pattern,
  [Parameter(Mandatory)][string]$Out,
  [int]$Fps = 24,
  [int]$Crf = 18
)
ffmpeg -y -framerate $Fps -i $Pattern -c:v libx264 -preset slow -crf $Crf -pix_fmt yuv420p -movflags +faststart $Out
