"""Experimento 002, sonido v3: ¿el oleaje sigue de verdad la altura de las torres? (no sustituye escucharlo)

Parte A (informativa) - sobre el WAV de la v3: filtra en la banda de cada capa y correlaciona su volumen por fotograma
con la altura media real de su anillo (olas_002.json). Ojo: en la mezcla las notas de la caja de música caen en las
bandas media y exterior y las tapan, y el retumbo grave se cuela en las bandas vecinas; por eso esta parte NO decide.

Parte B (decide) - cada capa sintetizada SOLA: correlación de su volumen total por fotograma con la señal de SU anillo
(debe ser alta) y con esa misma señal desplazada un cuarto de vuelta (control: debe ser cercana a 0; los anillos
oscilan desfasados entre sí, así que comparar con "el anillo de al lado" no sirve como control).

Uso:  python verificar_olas.py olas_002.json sonido_002_v3_olas-y-caja-menor.wav
"""
import os
import sys
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sintetizar_002_olas as sv

olas = json.load(open(sys.argv[1]))
n, fps = olas["fotogramas"], olas["fps"]
sr, x = wavfile.read(sys.argv[2])
mono = (x.astype(float) / 32768).mean(axis=1)


def rms_por_frame(y):
    paso = len(y) // n
    return np.sqrt((y[: paso * n].reshape(n, paso) ** 2).mean(axis=1))


print("A) en la mezcla (informativa): volumen por fotograma en la banda de cada capa vs la altura de su anillo")
for nombre, banda, _, _ in sv.CAPAS:
    sos = signal.butter(4, banda, btype="band", fs=sr, output="sos")
    r = np.corrcoef(rms_por_frame(signal.sosfiltfilt(sos, mono)), olas[nombre])[0, 1]
    print("   %-8s %4d-%-5d Hz  r = %+.3f" % (nombre, banda[0], banda[1], r))

print("B) cada capa sola (decide): r con SU anillo | r con la señal desplazada un cuarto de vuelta (control, ~0)")
todas = list(sv.CAPAS)
ok = True
for capa in todas:
    sv.CAPAS = [capa]
    L, R = sv.capa_olas(olas, fps, n, np.random.default_rng(sv.SEMILLA))
    T = len(L) // 3
    vol = rms_por_frame(((L + R) / 2)[T:2 * T])
    propia = np.corrcoef(vol, olas[capa[0]])[0, 1]
    control = np.corrcoef(vol, np.roll(olas[capa[0]], n // 4))[0, 1]
    ok &= propia >= 0.85 and abs(control) < 0.5
    print("   %-8s r = %+.3f | control %+.3f" % (capa[0], propia, control))
sv.CAPAS = todas
print("Cada capa de oleaje sigue la altura de su anillo:", "SÍ" if ok else "NO (revisar)")
