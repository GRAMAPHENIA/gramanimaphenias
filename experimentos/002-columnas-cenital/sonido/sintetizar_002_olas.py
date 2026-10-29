"""Experimento 002, sonido v3: PROPUESTA PROVISIONAL. Las esferas son la caja de música; las torres, el oleaje.

Hasta la v2 todo sonaba en los picos, pero el movimiento de ola de las torres es continuo y nada en el sonido lo
seguía. Aquí cada elemento visual tiene su capa:

  - ESFERAS -> caja de música (pentatónica menor, la elegida por el autor en la v2): una nota por esfera
    lanzada, en el instante del lanzamiento. Misma selección que sintetizar_002_caja.py.
  - TORRES  -> oleaje: tres capas de ruido filtrado, una por anillo concéntrico alrededor del centro de la onda,
    cada una con el volumen de la ALTURA MEDIA REAL de su anillo en cada fotograma:
        anillo interior -> retumbo grave y centrado          (120-500 Hz)
        anillo medio    -> ruido de rango medio              (500-1800 Hz)
        anillo exterior -> siseo agudo, ancho en estéreo     (1800-6000 Hz)
    La cresta pasa del centro hacia afuera, así que las tres capas suben y bajan desfasadas y el oído la sigue.
    Los anillos no dependen de la cámara.

Bucle: dura lo mismo que la animación y cierra sin corte (tres vueltas, se toma la del medio; las envolventes
son periódicas).

Uso:  python sintetizar_002_olas.py eventos_002.json olas_002.json sonido_002_v3_olas-y-caja-menor.wav
Escribe también <salida>.notas.json y <salida sin .wav>_solo-olas.wav (la capa de oleaje sola). Parámetros al inicio; la semilla es fija (el mismo resultado cada vez).
"""
import os
import sys
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sintetizar_002_caja as caja
from sintetizar_002 import cargar

# --- Parámetros (propuesta v3) ---
SR = caja.SR
SEMILLA = 2
OLAS_NIVEL = 0.10                  # volumen general del oleaje
NOTAS_FACTOR = 0.6                 # las notas se bajan a este factor (1 = como en la v2)
CAPAS = [                          # (señal del .json, banda en Hz, ganancia, ancho estéreo 0..1)
    # Medido (ver verificar_olas.py): con ganancias 1.0 / 0.6 / 0.35 y notas al 100 %, el oleaje medio y exterior
    # quedaba ~20 dB por debajo de las notas, es decir, inaudible. Con lo de abajo queda ~7 dB por debajo.
    ("anillo0", (120, 500), 1.0, 0.0),
    ("anillo1", (500, 1800), 1.5, 0.5),
    ("anillo2", (1800, 6000), 1.0, 1.0),
]
PISO = 0.12                        # volumen mínimo de cada capa (0 = puede callar del todo)
CURVA = 1.5                        # mayor = el oleaje se concentra más en las crestas
SUAVIZADO = 5                      # fotogramas de suavizado circular de las señales
MODO = "menor"
PICO_DBFS = -3.0


def envolvente(valores, n, fps, T):
    """Señal por fotograma -> envolvente por muestra, normalizada 0..1, suavizada y periódica."""
    v = np.asarray(valores, dtype=float)
    v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    k = SUAVIZADO // 2
    v = np.convolve(np.concatenate([v[-k:], v, v[:k]]), np.ones(SUAVIZADO) / SUAVIZADO, mode="valid")
    v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    v = PISO + (1 - PISO) * v ** CURVA
    dur = T / SR
    t = np.arange(3 * T) / SR
    return np.interp(t % dur, (np.arange(n) + 0.5) / fps, v, period=dur)


def capa_olas(olas, fps, n, rng):
    T = int(round(n / fps * SR))
    L, R = np.zeros(3 * T), np.zeros(3 * T)
    for nombre, (f1, f2), ganancia, ancho in CAPAS:
        env = envolvente(olas[nombre], n, fps, T)
        sos = signal.butter(2, [f1, f2], btype="band", fs=SR, output="sos")
        comun = signal.sosfilt(sos, rng.standard_normal(3 * T))
        izq = signal.sosfilt(sos, rng.standard_normal(3 * T))
        der = signal.sosfilt(sos, rng.standard_normal(3 * T))
        for canal, propio in ((L, izq), (R, der)):
            mezcla = (1 - ancho) * comun + ancho * propio              # ancho 0 = mono, 1 = canales independientes
            canal += ganancia * mezcla / (np.std(mezcla) + 1e-9) * env
    return L * OLAS_NIVEL / 3, R * OLAS_NIVEL / 3


def main(ruta_eventos, ruta_olas, ruta_wav):
    rng = np.random.default_rng(SEMILLA)
    fps, n, picos = cargar(ruta_eventos)
    olas = json.load(open(ruta_olas))
    T = int(round(n / fps * SR))
    # Caja de música: exactamente la selección y el timbre de la v2 (mismas semillas)
    rng_caja = np.random.default_rng(caja.SEMILLA)
    notas = caja.elegir_notas(picos, caja.ESCALAS[MODO], np.random.default_rng(caja.SEMILLA + 1))
    x_ext = max(abs(picos[:, 1].min()), abs(picos[:, 1].max()))
    banco = {m: caja.lengueta(caja.frecuencia(m), rng_caja) for m in {m for _, m, _ in notas}}
    L, R = np.zeros(3 * T), np.zeros(3 * T)
    for pos, midi, x in notas:
        pan = np.clip(x / x_ext, -1, 1) * caja.PANORAMA
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        s = banco[midi] * caja.NOTA_NIVEL * NOTAS_FACTOR * (0.85 + 0.15 * rng_caja.random())
        for v in range(3):
            i = int(round(pos / fps * SR)) + v * T
            fin = min(i + len(s), len(L))
            L[i:fin] += s[:fin - i] * gl
            R[i:fin] += s[:fin - i] * gr
    ol, orr = capa_olas(olas, fps, n, rng)
    # La capa de oleaje sola (para oírla aparte y para verificar que sigue a las torres sin que las notas la tapen)
    so = max(np.max(np.abs(ol[T:2 * T])), np.max(np.abs(orr[T:2 * T])))
    solo = np.stack([ol[T:2 * T], orr[T:2 * T]], axis=1) * 10 ** (PICO_DBFS / 20) / so
    wavfile.write(ruta_wav.replace(".wav", "_solo-olas.wav"), SR, (solo * 32767).astype(np.int16))
    L, R = (L + ol)[T:2 * T], (R + orr)[T:2 * T]
    g = 10 ** (PICO_DBFS / 20) / max(np.max(np.abs(L)), np.max(np.abs(R)))
    wavfile.write(ruta_wav, SR, (np.stack([L, R], axis=1) * g * 32767).astype(np.int16))
    json.dump([{"t_s": round(p / fps, 4), "midi": m, "nota": caja.nombre(m), "hz": round(caja.frecuencia(m), 2), "x": x}
               for p, m, x in notas], open(ruta_wav + ".notas.json", "w"), ensure_ascii=False)
    print("Escrito %s: %d notas (esferas) + %d capas de oleaje (torres), %.4f s" % (ruta_wav, len(notas), len(CAPAS), T / SR))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
