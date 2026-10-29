# Notas de Blender 5.2 LTS relevantes para el lab

Fuente oficial: https://developer.blender.org/docs/release_notes/5.2/ (consultada 2026-10-29).
Blender 5.2 LTS salió el 2026-07-14 y recibe correcciones hasta julio 2028.

## EEVEE
- Pipeline de ray tracing en pantalla reorganizado: escenas de 5.1 pueden verse más oscuras
  o necesitar ajustar *thickness*. Fijar todo el lab en 5.2.
- Nuevo `Backface` en Screen Tracing (menos fugas de luz).
- Eliminado `Far Thickness` de Fast GI Approximation.
- Nuevas opciones de *shadow pool* de 1.5 GB y 2 GB: útiles con 4 GB de VRAM.
- Algo menos de VRAM en render; instancing hasta 2x más rápido en escenas limitadas por CPU.
- Raycast shader node (desde 5.1): base para toon / X-ray. Más preciso en 5.2.

## Geometry Nodes
- Los archivos con herramientas de nodos deben re-guardarse en 5.2.
- Cambiaron los identificadores de sockets en los nodos Compare y Random Value.
- Cambió la API de Python para propiedades del modificador de Geometry Nodes.

## Python
- Quitados `paint.eraser_brush` y `paint.eraser_brush_asset_reference`.

## Pendiente de verificar en las páginas oficiales
Grease Pencil (nuevo algoritmo de relleno), Cycles, Compositor y la física por nodos
(experimental): solo conocidos por prensa hasta ahora.
