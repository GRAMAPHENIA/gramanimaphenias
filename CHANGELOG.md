# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
El proyecto usa versionado por hitos (`0.x`) mientras el kit se estabiliza.

## [Sin publicar]

### Corregido
- `LICENSE` con texto MIT estándar para que GitHub lo reconozca.

### Agregado
- Experimento `002-columnas-cenital`: ola de columnas con destello al llegar al pico y esferas que se
  desprenden, suben achicándose y se oscurecen. Cámara diagonal del autor, bucle de 100 fotogramas.
  - `anadir_esferas.py`, `exponer_parametros.py` (11 parámetros en el panel del modificador),
    `distribuir_entradas.py` y `ordenar_nodos.py` (marcos en color por defecto, títulos en mayúsculas).
  - La receta completa se verificó: reproduce el `.blend` con diferencia 0,0.
  - README con las particularidades de Blender 5.2 encontradas (valores en 0 al exponer sockets,
    reevaluación del modificador, "Local Space" de `Translate Instances`).
- Grano de película en el compositor base (ruido blanco 4D, modo Linear Light, factor 0,03).
- Experimento `001-ola-de-columnas`: ola procedural con Geometry Nodes, bucle de 4 s, receta, script y preview.
- `docs/02-render-4gb.md`: ajustes para 4 GB de VRAM y tabla de mediciones.
- Convención de commits documentada en el README.

### Agregado (sonido, propuesta provisional)
- `experimentos/002-columnas-cenital/sonido/`: audio sincronizado con los picos reales de las columnas.
  v1 (ticks + zumbido) y v2 (caja de música mecánica, pentatónica mayor y menor), con verificador objetivo.
  Bucle de 100 fotogramas = 200 000 muestras exactas. Pendiente que el autor elija y escuche.
- Git LFS también para `*.wav`.

### Cambiado
- Escena base: luces más fuertes, suelo de 200 m, mundo más oscuro y viñeta más suave
  para que el horizonte no sea un borde duro.

### Corregido
- `make_001.py` fija luces y mundo en valores absolutos: la receta reproduce el `.blend` publicado.

### Pendiente
- Render de la versión actual del 002 (el video de `media/` es de la versión cenital anterior).
- Definir la estética final de los experimentos 001 y 002 con el autor.
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
