"""Experimento 002, sonido: extrae del .blend los eventos que el audio debe acompañar.

Lee los DATOS REALES del archivo (no las fórmulas): evalúa el grafo en cada fotograma del bucle y mide
  - picos:     para cada columna, el instante (en fotogramas, con precisión sub-fotograma) en que llega a su
               punto más alto; en ese mismo instante se desprende su esfera.
  - actividad: por fotograma, cuánto se mueven en total las columnas (suma de |cambio de altura|).
El bucle se trata como circular: el fotograma siguiente al último es el primero.

Uso (solo lectura sobre el archivo):
  blender -b experimentos/002-columnas-cenital/002.blend -P experimentos/002-columnas-cenital/sonido/extraer_eventos.py -- eventos.json
"""
import sys
import json
import bpy

salida = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
f0, f1 = sc.frame_start, sc.frame_end
n = f1 - f0 + 1
ANCHO = 0.34                     # "Ancho de columna": distingue las columnas de las esferas en las instancias


def alturas(frame):
    """{(x, y): altura de la columna} en un fotograma."""
    sc.frame_set(frame)
    d = {}
    for i in bpy.context.evaluated_depsgraph_get().object_instances:
        if not i.is_instance:
            continue
        m = i.matrix_world
        s = m.to_scale()
        if abs(s.x - ANCHO) < 1e-4:
            t = m.translation
            d[(round(t.x, 3), round(t.y, 3))] = s.z
    return d


serie = [alturas(f) for f in range(f0, f1 + 1)]
claves = sorted(serie[0])
picos = []
for k in claves:
    h = [serie[i][k] for i in range(n)]
    i = max(range(n), key=lambda j: h[j])
    a, b, c = h[(i - 1) % n], h[i], h[(i + 1) % n]
    den = a - 2 * b + c
    delta = 0.5 * (a - c) / den if den != 0 else 0.0           # vértice de la parábola por 3 puntos
    picos.append([round((i + delta) % n, 4), k[0], k[1]])        # posición en el bucle, 0..n (0 = primer fotograma)
actividad = []
for i in range(n):
    sig = serie[(i + 1) % n]
    actividad.append(round(sum(abs(sig[k] - serie[i][k]) for k in claves), 4))

json.dump({"fps": sc.render.fps, "fotogramas": n, "columnas": len(claves), "picos": picos, "actividad": actividad},
          open(salida, "w"))
print("Eventos: %d columnas, %d fotogramas, %d fps -> %s" % (len(claves), n, sc.render.fps, salida))
