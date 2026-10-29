"""Experimento 002, sonido v1: PROPUESTA PROVISIONAL de sonidos mecánicos sincronizados con el movimiento.

Todo se sintetiza con código (numpy/scipy): sin muestras de terceros, sin derechos ajenos. El carácter del
sonido (timbres, densidad, tonos) lo define el autor; esto es un punto de partida para escuchar y corregir.

Capas:
  - ticks:   un clic mecánico en el instante exacto en que cada columna llega a su pico (el mismo en que se
             desprende su esfera). Tono según la posición Y, panorámica según X.
  - zumbido: motor grave y constante, cuyo volumen "respira" con la densidad de picos por fotograma.

Bucle: el audio dura exactamente lo mismo que la animación (fotogramas / fps) y cierra sin corte: se sintetizan
tres vueltas seguidas y se toma la del medio, y el zumbido tiene un número entero de ciclos por vuelta.

Uso:  python sintetizar_002.py eventos_002.json sonido_002_v1.wav     (los eventos salen de extraer_eventos.py)
Parámetros al inicio; cambiar uno y volver a ejecutar. La semilla es fija: el mismo resultado cada vez.
"""
import sys
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

# --- Parámetros (propuesta v1) ---
SR = 48000
SEMILLA = 2
TICK_NIVEL = 0.07          # volumen de cada tick (antes de normalizar)
TICK_HZ = (1600, 5200)     # tono del tick: de Y mínimo a Y máximo
TICK_CAIDA = 0.0028        # segundos: cuánto dura el clic (menor = más seco)
TICK_VARIACION = 0.25      # variación aleatoria de volumen por tick (0 a 1)
ZUMBIDO_NIVEL = 0.05
ZUMBIDO_CICLOS = (200, 204)  # ciclos enteros por vuelta de dos osciladores (≈48 y ≈49 Hz): cierra sin corte
ZUMBIDO_RESPIRA = 0.35     # cuánto varía el volumen del zumbido con la densidad de picos (0 a 1)
PANORAMA = 0.8             # 0 = mono, 1 = extremo a extremo
PICO_DBFS = -3.0           # nivel máximo del audio final


def cargar(ruta):
    d = json.load(open(ruta))
    return d["fps"], d["fotogramas"], np.array(d["picos"], dtype=float)


def banco_clics(rng, n_tonos=24):
    """Un clic por cada tono posible: ruido filtrado + un golpe resonante, con caída exponencial."""
    largo = int(SR * 0.030)
    t = np.arange(largo) / SR
    banco = []
    for fc in np.geomspace(*TICK_HZ, n_tonos):
        ruido = rng.standard_normal(largo)
        sos = signal.butter(2, [fc / 1.35, min(fc * 1.35, SR / 2 * 0.95)], btype="band", fs=SR, output="sos")
        ruido = signal.sosfilt(sos, ruido) * np.exp(-t / TICK_CAIDA)
        golpe = np.sin(2 * np.pi * fc / 3.2 * t) * np.exp(-t / (TICK_CAIDA * 1.6)) * 0.6
        clic = ruido / (np.max(np.abs(ruido)) + 1e-9) + golpe
        banco.append(clic / (np.max(np.abs(clic)) + 1e-9))
    return banco


def capa_ticks(fps, n, picos, rng, vueltas=3):
    T = int(round(n / fps * SR))
    L = np.zeros(vueltas * T)
    R = np.zeros(vueltas * T)
    banco = banco_clics(rng)
    ys = picos[:, 2]
    y0, y1 = ys.min(), ys.max()
    xs = picos[:, 1]
    x_ext = max(abs(xs.min()), abs(xs.max()))
    for pos, x, y in picos:
        tono = int(round((y - y0) / (y1 - y0) * (len(banco) - 1)))
        clic = banco[tono] * TICK_NIVEL * (1 - TICK_VARIACION * rng.random())
        pan = np.clip(x / x_ext, -1, 1) * PANORAMA
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)      # reparto de potencia constante
        for v in range(vueltas):
            i = int(round(pos / fps * SR)) + v * T
            fin = min(i + len(clic), len(L))
            L[i:fin] += clic[:fin - i] * gl
            R[i:fin] += clic[:fin - i] * gr
    return L, R


def capa_zumbido(fps, n, picos, vueltas=3):
    T = int(round(n / fps * SR))
    t = np.arange(vueltas * T) / SR
    dur = T / SR
    zz = np.zeros_like(t)
    for ciclos, nivel in zip(ZUMBIDO_CICLOS, (1.0, 0.7)):
        f = ciclos / dur
        for k in range(1, 9):                                    # diente de sierra aditivo, parciales hasta el 8
            zz += nivel * np.sin(2 * np.pi * f * k * t + 0.7 * k) / k
    # densidad de picos por fotograma, suavizada de forma circular -> volumen del zumbido
    cuenta = np.bincount(np.floor(picos[:, 0]).astype(int) % n, minlength=n).astype(float)
    ventana = np.ones(7) / 7
    suave = np.convolve(np.concatenate([cuenta[-3:], cuenta, cuenta[:3]]), ventana, mode="valid")
    suave = (suave - suave.min()) / (suave.max() - suave.min() + 1e-9)
    env_frames = (1 - ZUMBIDO_RESPIRA) + ZUMBIDO_RESPIRA * suave
    env = np.interp(t % dur, (np.arange(n) + 0.5) / fps, env_frames, period=dur)
    sos = signal.butter(2, 700, btype="low", fs=SR, output="sos")
    zz = signal.sosfilt(sos, zz) * env
    return zz / (np.max(np.abs(zz)) + 1e-9) * ZUMBIDO_NIVEL


def main(ruta_eventos, ruta_wav):
    rng = np.random.default_rng(SEMILLA)
    fps, n, picos = cargar(ruta_eventos)
    T = int(round(n / fps * SR))
    tl, tr = capa_ticks(fps, n, picos, rng)
    zumbido = capa_zumbido(fps, n, picos)
    L, R = tl + zumbido, tr + zumbido
    L, R = L[T:2 * T], R[T:2 * T]                          # la vuelta del medio: sin transitorios de arranque
    pico = max(np.max(np.abs(L)), np.max(np.abs(R)))
    g = 10 ** (PICO_DBFS / 20) / pico
    estereo = np.stack([L * g, R * g], axis=1)
    wavfile.write(ruta_wav, SR, (estereo * 32767).astype(np.int16))
    print("Escrito %s: %d muestras (%.4f s) a %d Hz, estéreo 16 bits" % (ruta_wav, T, T / SR, SR))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
