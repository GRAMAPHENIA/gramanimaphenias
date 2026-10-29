# Render en una GPU de 4 GB

Equipo de referencia: i5-10500H, 15,8 GB de RAM, NVIDIA RTX 3050 Ti Laptop (4 GB de VRAM),
Blender 5.2 LTS, Windows 11.

## Decisión de motor
EEVEE por defecto. Cycles solo para tomas puntuales (texturas de hasta 2K). Con 4 GB de VRAM,
los proyectos con texturas grandes o mucha geometría se acercan rápido al límite.

## Ajustes de la escena base (`scripts/setup_scene.py`)
| Ajuste | Valor | Motivo |
| --- | --- | --- |
| Resolución | 1080x1920 al 100 %, 24 fps | Formato vertical para reels y shorts |
| Muestras de render | 64 | Suficiente con el denoise de EEVEE para formas simples |
| Ray tracing / AO | apagados | Cuestan VRAM y tiempo; se activan solo si la toma lo pide |
| Gestión de color | AgX | Mejor manejo de las luces fuertes que Standard |
| Suelo | plano de 200 m | Evita ver el borde del suelo en el horizonte |
| Compositor | glare Bloom + viñeta (0,35) | Acabado barato, se ejecuta en CPU/GPU sin costo notable |

Opciones de 5.2 que conviene probar cuando haga falta: *shadow pool* de 1,5 y 2 GB (más control
de la memoria de sombras) y el nuevo `Backface` en Screen Tracing (menos fugas de luz).
Fuente: [notas de EEVEE 5.2](https://developer.blender.org/docs/release_notes/5.2/eevee/).

## Mediciones
Experimento 000 (cubo animado sobre suelo, 2 luces de área), 24 fotogramas:

| Fecha | Escena | s/frame | Pico de VRAM |
| --- | --- | --- | --- |
| 2026-10-29 | luz baja, mundo claro | 1,20 | 1390 MiB |
| 2026-10-29 | luz y suelo definitivos (v0.1) | 1,26 | 2817 MiB |
| 2026-10-29 | experimento 001: 319 columnas instanciadas, 96 frames, máquina fría | 1,45 | 2853 MiB |
| 2026-10-29 | experimento 001 con grano, tras varios renders seguidos | 4,15 | 1676 MiB |

- La GPU en reposo usa unos 1468 MiB (Windows y otros programas). El pico de `nvidia-smi` es de toda
  la GPU, no solo de Blender, y varía según lo que haya abierto: la diferencia entre las dos filas
  no se debe solo a la escena. Para medir Blender solo, cerrar el resto de programas.
- 319 instancias con Geometry Nodes no cambian de forma apreciable la VRAM: el pico es casi igual al del cubo.
- **Límite térmico:** tras varios renders seguidos la GPU llegó a 88 °C con el aviso de reducción
  por calor activo (`clocks_event_reasons = 0x20`) y el tiempo por fotograma se triplicó (1,45 a 4,15 s)
  sin cambiar la escena. Para comparar tiempos hay que partir con la máquina fría, o dejarla enfriar
  entre corridas. Se puede mirar con `nvidia-smi --query-gpu=temperature.gpu,clocks_throttle_reasons.active --format=csv`.
- El grano del compositor no agrega tiempo medible (2,67 s contra 2,78 s en el mismo fotograma).
- Todas las mediciones son de una sola corrida; repetir antes de sacar conclusiones.

## Cómo medir
```powershell
.\scripts\render.ps1 -Blend experimentos\000-prueba-cubo\cubo.blend -Start 1 -End 24 -Out renders\prueba\f_
```
Deja `f__log.json` con segundos totales, segundos por frame y pico de VRAM.

## Reglas prácticas
- Texturas de 2K como máximo en fondos; 4K solo en el objeto principal.
- Instancias enlazadas para repetir objetos. En 5.2 EEVEE las dibuja hasta 2x más rápido.
- Aplicar subdivisión a un nivel razonable y decimar lo que no se ve de cerca.
- Si una toma no entra en VRAM: bajar texturas, bajar el shadow pool o partir en capas.
