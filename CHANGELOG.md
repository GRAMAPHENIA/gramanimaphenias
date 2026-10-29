# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
El proyecto usa versionado por hitos (`0.x`) mientras el kit se estabiliza.

## [Sin publicar]

### Pendiente
- Subir exposición y suavizar el horizonte de la escena base.
- Grano de película en el compositor.
- `docs/02-render-4gb.md` con las mediciones.
- Primer experimento con estética definida por el autor.

## [0.1.0] - 2026-10-29

### Agregado
- Estructura del repositorio, licencias (MIT para código, CC BY 4.0 para contenido) y Git LFS.
- `scripts/setup_scene.py`: escena base reproducible en Blender 5.2 LTS
  (1080x1920, 24 fps, EEVEE, AgX, cámara vertical, dos luces, suelo,
  compositor con glare y viñeta).
- `scripts/render.ps1`: render headless con medición de tiempo y VRAM.
- `scripts/encode.ps1`: secuencia PNG a mp4 H.264 con ffmpeg.
- `experimentos/000-prueba-cubo`: prueba del pipeline (1,2 s/frame, pico de VRAM 1390 MiB
  en RTX 3050 Ti de 4 GB).
- `docs/05-notas-blender-5.2.md`: notas de la versión 5.2 LTS verificadas en las notas oficiales.
