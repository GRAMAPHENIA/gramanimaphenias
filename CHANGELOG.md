# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
El proyecto usa versionado por hitos (`0.x`) mientras el kit se estabiliza.

## [Sin publicar]

### Corregido
- `LICENSE` con texto MIT estándar para que GitHub lo reconozca.

### Agregado
- Experimento `001-ola-de-columnas`: ola procedural con Geometry Nodes, bucle de 4 s, receta, script y preview.
- `docs/02-render-4gb.md`: ajustes para 4 GB de VRAM y tabla de mediciones.
- Convención de commits documentada en el README.

### Cambiado
- Escena base: luces más fuertes, suelo de 200 m, mundo más oscuro y viñeta más suave
  para que el horizonte no sea un borde duro.

### Pendiente
- Grano de película en el compositor.
- Definir la estética final del experimento 001 con el autor.
- Experimento de Grease Pencil (dibujo del autor).

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
