"""Experimento 002, sonido v4: comprobaciones de las dos peticiones del autor (no sustituyen escucharlo).

  A. Campanas: cada nota coincide con una columna campana (ix, iy múltiplos de la separación) y con el instante en que
     esa columna llega a su pico, según los datos de eventos_002.json (que salen del .blend). No hay notas sin campana
     ni campanas sin nota.
  B. Cada banda de oleaje, sola, sigue la altura de SU anillo (correlación >= 0,85; control: la misma señal desplazada
     un cuarto de vuelta, cercano a 0).
  C. Misma velocidad: el retraso entre anillos vecinos en el AUDIO (correlación cruzada circular de las envolventes de
     cada banda) se convierte en una velocidad de la cresta y se compara con la del MOVIMIENTO (calculada igual con las
     alturas reales) y con la teórica de la onda (longitud de onda / periodo).

Uso:  python verificar_v4.py eventos_002.json olas_002_8anillos.json sonido_002_v4_campanas-y-olas.wav [separacion]
"""
import os
import sys
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sintetizar_002_v4 as v4

ev = json.load(open(sys.argv[1]))
olas = json.load(open(sys.argv[2]))
ruta = sys.argv[3]
sep = int(sys.argv[4]) if len(sys.argv) > 4 else v4.SEPARACION
fps, n, na = olas["fps"], olas["fotogramas"], olas["n_anillos"]
picos = np.array(ev["picos"])
notas = json.load(open(ruta + ".notas.json"))

# --- A: campanas ---
x, y = picos[:, 1], picos[:, 2]
paso = np.min(np.diff(np.unique(np.round(x, 3))))
ix = np.rint((x - x.min()) / paso).astype(int)
iy = np.rint((y - y.min()) / paso).astype(int)
campana = (ix % sep == 0) & (iy % sep == 0)
esperadas = sorted((p[0] / fps, p[1]) for p in picos[campana])
dadas = sorted((e["t_s"], e["x"]) for e in notas)
coinciden = len(esperadas) == len(dadas) and all(abs(a[0] - b[0]) < 1e-3 and abs(a[1] - b[1]) < 1e-3 for a, b in zip(esperadas, dadas))
print("A) campanas: %d columnas campana en la grilla (%d x %d, cada %d) | %d notas | coinciden (instante a 1 ms, posición): %s"
      % (campana.sum(), len(np.unique(ix[campana])), len(np.unique(iy[campana])), sep, len(notas), "SÍ" if coinciden else "NO"))
sin_nota = [i for i in np.where(~campana)[0] if any(abs(picos[i, 0] / fps - e["t_s"]) < 1e-3 and abs(picos[i, 1] - e["x"]) < 1e-3 and abs(picos[i, 2] - picos[i, 2]) < 1e-3 for e in notas)]
print("   notas sobre columnas que NO son campana: %d" % len(sin_nota))

# --- B: cada banda sola ---
ok = True
print("B) cada banda sola: r con SU anillo | control (señal desplazada un cuarto de vuelta, ~0)")
for k in range(na):
    L, R = v4.capa_olas(olas, fps, n, np.random.default_rng(v4.SEMILLA), anillos=[k])
    T = len(L) // 3
    y_ = ((L + R) / 2)[T:2 * T]
    vol = np.sqrt((y_[: (len(y_) // n) * n].reshape(n, -1) ** 2).mean(axis=1))
    r = np.corrcoef(vol, olas["anillo%d" % k])[0, 1]
    c = np.corrcoef(vol, np.roll(olas["anillo%d" % k], n // 4))[0, 1]
    ok &= r >= 0.85 and abs(c) < 0.5
    print("   anillo %d (%4d-%4d Hz)  r = %+.3f | control %+.3f" % (k, v4.bordes(na)[k], v4.bordes(na)[k + 1], r, c))
print("   cada banda sigue la altura de su anillo:", "SÍ" if ok else "NO")


# --- C: velocidad de la cresta ---
def retraso(a, b):
    """Retraso (en fotogramas, con sub-fotograma) con que b sigue a a: correlación cruzada circular."""
    c = np.real(np.fft.ifft(np.fft.fft(b - b.mean()) * np.conj(np.fft.fft(a - a.mean()))))
    i = int(np.argmax(c))
    y0, y1, y2 = c[(i - 1) % n], c[i], c[(i + 1) % n]
    d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    return ((i + d + n / 2) % n) - n / 2


sr, w = wavfile.read(ruta.replace(".wav", "_solo-olas.wav"))
mono = (w.astype(float) / 32768).mean(axis=1)
f = v4.bordes(na)
env_audio = []
for k in range(na):
    sos = signal.butter(4, [f[k] * 1.05, min(f[k + 1] * 0.95, sr / 2 * 0.95)], btype="band", fs=sr, output="sos")
    yb = signal.sosfiltfilt(sos, mono) ** 2
    env_audio.append(np.sqrt(yb[: (len(yb) // n) * n].reshape(n, -1).mean(axis=1)))
dr = olas["dist_max"] / na                                    # ancho de cada anillo en metros
v_audio, v_visual = [], []
for k in range(na - 1):
    v_audio.append(dr / (retraso(env_audio[k], env_audio[k + 1]) / fps))
    v_visual.append(dr / (retraso(np.array(olas["anillo%d" % k]), np.array(olas["anillo%d" % (k + 1)])) / fps))
v_teorica = 3.2 / (n / fps)                                   # longitud de onda (3,2 m) / periodo
print("C) velocidad a la que la cresta sale del centro (m/s):")
print("   en el audio:        mediana %.2f  (por par de bandas: %s)" % (np.median(v_audio), " ".join("%.2f" % v for v in v_audio)))
print("   en el movimiento:   mediana %.2f  (calculada igual, con las alturas reales)" % np.median(v_visual))
print("   teórica de la onda: %.2f  (longitud de onda 3,2 m / periodo %.2f s)" % (v_teorica, n / fps))
print("   audio vs movimiento: diferencia %.0f %%" % (100 * abs(np.median(v_audio) / np.median(v_visual) - 1)))
