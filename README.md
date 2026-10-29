# gramanimaphenias

**Gramaphenia Blender Lab**

Laboratorio de animaciones sencillas y de bajo costo en Blender: 3D, Grease Pencil
y Geometry Nodes, pensado para renderizarse en una laptop modesta y documentarse
para que cualquiera pueda replicarlo.

## Entorno de referencia

- Blender **5.2 LTS** (usar esta versión; las anteriores pueden dar resultados distintos)
- Windows 11, i5-10500H, 15.8 GB RAM, NVIDIA RTX 3050 Ti Laptop (4 GB VRAM)
- Motor por defecto: EEVEE (Cycles solo en tomas puntuales)
- Formato de prueba: 1080x1920 vertical, 24 fps
- ffmpeg para codificar, Git + Git LFS para el repositorio

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `docs/` | Entorno, add-ons, ajustes de render para 4 GB, cámara, Grease Pencil + GN |
| `base/` | Escena base reproducible y presets |
| `scripts/` | Render headless, construcción de escena, benchmark, codificación |
| `experimentos/` | Un experimento por carpeta, con receta, fuentes, tiempos y preview |
| `media/` | Solo previews ligeras |

## Licencias

Código (`scripts/` y todo `.py`/`.ps1`): MIT (`LICENSE`). Documentación y assets: CC BY 4.0 (`LICENSE-CONTENT`).

Ver los cambios en [`CHANGELOG.md`](CHANGELOG.md).

## Commits

Prefijo clásico en inglés y descripción en español, en minúsculas y sin punto final:
`feat:` (algo nuevo), `fix:` (corrección), `docs:` (documentación), `refactor:`,
`chore:` (mantenimiento), `perf:`, `test:`. Ejemplo: `feat: agregar compositor con glare y viñeta`.

## Estado

- [x] Fase 1: repositorio, licencias, LFS, estructura
- [~] Fase 2: investigación en `docs/` (hecho `05-notas-blender-5.2.md`; faltan GP, Cycles, compositor)
- [x] Fase 3: escena base reproducible (`scripts/setup_scene.py`); encuadre pendiente de ajustar
- [x] Fase 4: pipeline `scripts/render.ps1` + `scripts/encode.ps1`

Medición de referencia (experimento 000, cubo, EEVEE 64 muestras, 1080x1920, 24 frames):
1,2 s/frame, pico de VRAM 1390 MiB (RTX 3050 Ti 4 GB), mp4 H.264 1080x1920 24 fps.
El pico de VRAM incluye lo que usa Windows; no es solo Blender.

Compositor base (Blender 5.2: grupo en `scene.compositing_node_group`): glare Bloom + viñeta.
El grano no está: no hay nodo de ruido directo en el compositor; queda por resolver.
Encuadre ajustado: el cubo entra completo en el salto (cámara en (0,-13,3.2)).

Próximo paso: subir la exposición (la escena sale oscura y la viñeta pesa mucho), suavizar
el borde duro del suelo en el horizonte, escribir `docs/02-render-4gb.md` con las cifras
y definir con el autor la estética del experimento 001.
Pendiente: identidad de git local y commit inicial.
