"""Experimento 002, sonido v4: PROPUESTA PROVISIONAL. Esferas campana = caja de música; torres = oleaje que viaja.

Pedido del autor sobre la v3: que el oleaje tenga la misma velocidad que el movimiento y que las esferas estén
sincronizadas con la caja de música. Lo que cambia:

  - CAMPANAS (esferas -> caja de música). En Blender, una esfera de cada N columnas (campanas.py) es más grande y más
    brillante: es una campana. Aquí cada campana toca UNA nota, en el instante en que nace (cuando su columna llega al
    pico). Lo que se ve y lo que se oye se corresponden uno a uno; el resto de las esferas no suena. La selección usa
    solo posiciones (ix, iy múltiplos de N), igual que el grafo, sin azar. Tono: 70 % altura Y + 30 % posición X
    (la altura sola daría solo 8 notas); pentatónica menor, 3 octavas desde do5. Panorámica según X.
  - OLEAJE QUE VIAJA (torres). 8 anillos finos (~0,95 m) alrededor del centro de la onda; cada anillo es una banda de
    ruido (de 140 Hz a 5,5 kHz, del centro hacia afuera; más ancha en estéreo cuanto más lejos) con el volumen de la
    ALTURA REAL media de su anillo. La cresta recorre los anillos a su velocidad real, así que se oye un barrido de grave
    a agudo que sale del centro a la misma velocidad que se ve (v = longitud de onda / periodo = 0,77 m/s).
  - La mezcla se calcula, no se tantea: el oleaje queda OLAS_DB dB por debajo de las notas (RMS de banda ancha).

Bucle: dura lo mismo que la animación y cierra sin corte (tres vueltas, se toma la del medio).

Uso:  python sintetizar_002_v4.py eventos_002.json olas_002_8anillos.json sonido_002_v4_campanas-y-olas.wav [separacion]
La separación (4 por defecto) debe ser la misma que "Separación de campanas" en el modificador.
Escribe también <salida>.notas.json y <salida sin .wav>_solo-olas.wav. Semilla fija: el mismo resultado cada vez.
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

# --- Parámetros (propuesta v4) ---
SR = caja.SR
SEMILLA = 2
SEPARACION = 4                    # "Separación de campanas" del modificador
PESO_Y = 0.7                      # el resto del tono lo decide la posición X
MODO = "menor"
NOTA_NIVEL = 0.25
OLAS_DB = -6.0                    # nivel del oleaje respecto de las notas (RMS de banda ancha)
F_MIN, F_MAX = 140.0, 5500.0      # el anillo 0 (centro) suena en F_MIN; el último, en F_MAX
PISO = 0.05                       # volumen mínimo de cada banda
CURVA = 2.0                       # mayor = el oleaje se concentra más en la cresta
SUAVIZADO = 3                     # fotogramas de suavizado circular
PANORAMA = 0.8
PICO_DBFS = -3.0


def bordes(n_anillos):
    return np.geomspace(F_MIN, F_MAX, n_anillos + 1)


def elegir_campanas(picos, escala):
    """[(posición en fotogramas, midi, x)]: una nota por campana (ix e iy múltiplos de SEPARACION)."""
    x, y = picos[:, 1], picos[:, 2]
    paso = np.min(np.diff(np.unique(np.round(x, 3))))
    ix = np.rint((x - x.min()) / paso).astype(int)
    iy = np.rint((y - y.min()) / paso).astype(int)
    es = (ix % SEPARACION == 0) & (iy % SEPARACION == 0)
    v = PESO_Y * (y - y.min()) / (y.max() - y.min()) + (1 - PESO_Y) * (x - x.min()) / (x.max() - x.min())
    grado = np.rint(v * (caja.GRADOS - 1)).astype(int)
    notas = []
    for i in np.where(es)[0]:
        octava, k = divmod(int(grado[i]), 5)
        notas.append((float(picos[i, 0]), caja.RAIZ_MIDI + 12 * octava + escala[k], float(x[i])))
    return sorted(notas)


def envolvente(valores, n, fps, T):
    v = np.asarray(valores, dtype=float)
    v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    k = SUAVIZADO // 2
    if k:
        v = np.convolve(np.concatenate([v[-k:], v, v[:k]]), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
        v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    v = PISO + (1 - PISO) * v ** CURVA
    dur = T / SR
    t = np.arange(3 * T) / SR
    return np.interp(t % dur, (np.arange(n) + 0.5) / fps, v, period=dur)


def capa_olas(olas, fps, n, rng, anillos=None):
    """Oleaje de banda ancha: una banda de ruido por anillo. Devuelve (L, R) de tres vueltas, sin escalar."""
    T = int(round(n / fps * SR))
    na = olas["n_anillos"]
    f = bordes(na)
    L, R = np.zeros(3 * T), np.zeros(3 * T)
    for k in (range(na) if anillos is None else anillos):
        env = envolvente(olas["anillo%d" % k], n, fps, T)
        sos = signal.butter(2, [f[k], min(f[k + 1], SR / 2 * 0.95)], btype="band", fs=SR, output="sos")
        ancho = k / max(na - 1, 1)                                 # 0 = mono (centro) ... 1 = canales independientes
        # El ruido de base dura exactamente UNA vuelta y se repite tres veces: así, tras filtrar, la vuelta del medio es
        # periódica y el bucle cierra sin clic (con ruido distinto en cada vuelta, el final no enlazaba con el comienzo).
        comun = signal.sosfilt(sos, np.tile(rng.standard_normal(T), 3))
        for canal in (L, R):
            propio = signal.sosfilt(sos, np.tile(rng.standard_normal(T), 3))
            mezcla = (1 - ancho) * comun + ancho * propio
            canal += mezcla / (np.std(mezcla) + 1e-9) * env * (f[k] / F_MIN) ** -0.25   # un poco menos de agudos
    return L, R


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)))


def main(ruta_eventos, ruta_olas, ruta_wav):
    rng = np.random.default_rng(SEMILLA)
    fps, n, picos = cargar(ruta_eventos)
    olas = json.load(open(ruta_olas))
    T = int(round(n / fps * SR))
    notas = elegir_campanas(picos, caja.ESCALAS[MODO])
    x_ext = max(abs(picos[:, 1].min()), abs(picos[:, 1].max()))
    rng_n = np.random.default_rng(caja.SEMILLA)
    banco = {m: caja.lengueta(caja.frecuencia(m), rng_n) for m in {m for _, m, _ in notas}}
    NL, NR = np.zeros(3 * T), np.zeros(3 * T)
    for pos, midi, x in notas:
        pan = np.clip(x / x_ext, -1, 1) * PANORAMA
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        s = banco[midi] * NOTA_NIVEL * (0.9 + 0.1 * rng_n.random())
        for v in range(3):
            i = int(round(pos / fps * SR)) + v * T
            fin = min(i + len(s), len(NL))
            NL[i:fin] += s[:fin - i] * gl
            NR[i:fin] += s[:fin - i] * gr
    OL, OR = capa_olas(olas, fps, n, rng)
    k = 10 ** (OLAS_DB / 20) * (rms(np.concatenate([NL[T:2 * T], NR[T:2 * T]])) / rms(np.concatenate([OL[T:2 * T], OR[T:2 * T]])))
    L, R = (NL + OL * k)[T:2 * T], (NR + OR * k)[T:2 * T]
    g = 10 ** (PICO_DBFS / 20) / max(np.max(np.abs(L)), np.max(np.abs(R)))
    wavfile.write(ruta_wav, SR, (np.stack([L, R], axis=1) * g * 32767).astype(np.int16))
    so = max(np.max(np.abs(OL[T:2 * T])), np.max(np.abs(OR[T:2 * T])))
    solo = np.stack([OL[T:2 * T], OR[T:2 * T]], axis=1) * 10 ** (PICO_DBFS / 20) / so
    wavfile.write(ruta_wav.replace(".wav", "_solo-olas.wav"), SR, (solo * 32767).astype(np.int16))
    json.dump([{"t_s": round(p / fps, 4), "midi": m, "nota": caja.nombre(m), "hz": round(caja.frecuencia(m), 2), "x": x}
               for p, m, x in notas], open(ruta_wav + ".notas.json", "w"), ensure_ascii=False)
    print("Escrito %s: %d campanas (una nota cada una, %d tonos distintos) + oleaje de %d bandas, %.4f s"
          % (ruta_wav, len(notas), len({m for _, m, _ in notas}), olas["n_anillos"], T / SR))


if __name__ == "__main__":
    if len(sys.argv) > 4:
        SEPARACION = int(sys.argv[4])
    main(sys.argv[1], sys.argv[2], sys.argv[3])
