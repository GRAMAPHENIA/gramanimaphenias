"""Experimento 002, sonido: extrae del .blend señales continuas del movimiento de las TORRES (para la capa de olas).

Por fotograma, a partir de las alturas reales de las columnas (el bucle se trata como circular):
  - global:     altura media de todas las columnas.
  - anillos:    altura media por distancia al centro de la onda (interior / medio / exterior).
  - cuadrantes: altura media por ángulo alrededor del centro (4 sectores). No dependen de la cámara.
  - subida:     columnas que están subiendo vs bajando (balance), y velocidad media de subida.

Uso (solo lectura sobre el archivo):
  blender -b experimentos/002-columnas-cenital/002.blend -P experimentos/002-columnas-cenital/sonido/extraer_olas.py -- olas.json
"""
import sys
import json
import math
import bpy

salida = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
f0, f1 = sc.frame_start, sc.frame_end
n = f1 - f0 + 1
ANCHO = 0.34
CENTRO = (0.0, 0.5)


def alturas(frame):
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
dist = {k: math.hypot(k[0] - CENTRO[0], k[1] - CENTRO[1]) for k in claves}
ang = {k: (math.atan2(k[1] - CENTRO[1], k[0] - CENTRO[0]) + math.pi) / (2 * math.pi) for k in claves}
dmax = max(dist.values())
anillo = {k: min(2, int(dist[k] / dmax * 3)) for k in claves}
cuadrante = {k: min(3, int(ang[k] * 4)) for k in claves}


def media(sel, i):
    v = [serie[i][k] for k in sel]
    return sum(v) / len(v)


salida_d = {"fps": sc.render.fps, "fotogramas": n}
salida_d["global"] = [round(media(claves, i), 5) for i in range(n)]
for a in range(3):
    sel = [k for k in claves if anillo[k] == a]
    salida_d["anillo%d" % a] = [round(media(sel, i), 5) for i in range(n)]
for q in range(4):
    sel = [k for k in claves if cuadrante[k] == q]
    salida_d["cuadrante%d" % q] = [round(media(sel, i), 5) for i in range(n)]
sube, vel = [], []
for i in range(n):
    sig = serie[(i + 1) % n]
    d = [sig[k] - serie[i][k] for k in claves]
    sube.append(round(sum(1 for x in d if x > 0) / len(d), 5))
    vel.append(round(sum(x for x in d if x > 0) / len(d), 5))
salida_d["balance_subida"] = sube
salida_d["velocidad_subida"] = vel
json.dump(salida_d, open(salida, "w"))
print("Olas: %d columnas, %d fotogramas -> %s" % (len(claves), n, salida))
