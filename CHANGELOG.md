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

### Agregado (render con la cámara D)
- `media/002-columnas-camara-d.mp4`: render con la cámara D elegida por el autor, esferas campana y sonido v4, bucle x3 (12,5 s).
  0,75 s/fotograma, pico de VRAM 2925 MiB; el contenido ocupa el 89 % del ancho y el 56 % del alto del cuadro.
- `make_002.py` usa la cámara D; la receta completa se verificó: reproduce el `.blend` guardado (cámara idéntica, geometría con diferencia 0,0).

### Agregado (campanas y sonido v4)
- `experimentos/002-columnas-cenital/campanas.py`: esferas campana (una de cada N columnas, más grandes y brillantes), las
  únicas que suenan. 3 parámetros nuevos en el modificador (separación, tamaño y brillo). Con tamaño 1 y brillo 1 el
  resultado es idéntico al anterior; con 1,8 las campanas miden exactamente x1,800 y las demás x1,000.
- `sonido/sintetizar_002_v4.py` (+ `verificar_v4.py`, `olas_002_8anillos.json`): una nota por campana y oleaje de 8 bandas que
  viaja a la velocidad de la cresta (audio 0,81 m/s, movimiento 0,81 m/s). Propuesta provisional, pendiente de escucha.
- `extraer_olas.py` acepta el número de anillos (8 por defecto; la v3 usó 3, y sigue reproduciéndose igual).
- La receta de Blender (con `campanas.py` en la cadena) se verificó: reproduce la sesión del autor con diferencia 0,0.

### Corregido
- Sonido v4: el ruido de las capas de oleaje ahora es periódico (duraba más que la vuelta y el bucle hacía un clic).

### Agregado (sonido v3 y encuadre)
- `sonido/sintetizar_002_olas.py` (+ `extraer_olas.py`, `verificar_olas.py`): esferas = caja de música, torres = oleaje
  seguido de la altura real de los anillos. Propuesta provisional, pendiente de escucha.
- Análisis de encuadre: con la cámara actual el límite es el ancho (95 % x 44 %); cámaras de propuesta D, F y G.

### Agregado (render del 002)
- `media/002-columnas-esferas.mp4`: render de la versión actual con el sonido elegido, bucle x3 (12,5 s).
  0,68 s/fotograma, pico de VRAM 2691 MiB, bucle cerrado (cierre 2,08 dentro del rango consecutivo 1,86 a 2,38).

### Agregado (sonido, propuesta provisional)
- `experimentos/002-columnas-cenital/sonido/`: audio sincronizado con los picos reales de las columnas.
  v1 (ticks + zumbido) y v2 (caja de música mecánica, pentatónica mayor y menor), con verificador objetivo.
  Bucle de 100 fotogramas = 200 000 muestras exactas. Pendiente que el autor elija y escuche.
- Elegida por el autor: caja de música en pentatónica menor (`sonido_002_v2b_pentatonica-menor.wav`).
- `scripts/encode.ps1`: opciones `-Audio` (mezcla una pista en el mp4) y `-Repetir` (repite el bucle).
- Git LFS también para `*.wav`.

### Cambiado
- Escena base: luces más fuertes, suelo de 200 m, mundo más oscuro y viñeta más suave
  para que el horizonte no sea un borde duro.

### Corregido
- `make_001.py` fija luces y mundo en valores absolutos: la receta reproduce el `.blend` publicado.

### Pendiente
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
