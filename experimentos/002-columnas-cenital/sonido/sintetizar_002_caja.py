"""Experimento 002, sonido v2: PROPUESTA PROVISIONAL de caja de música mecánica sincronizada con la animación.

Todo se sintetiza con código (numpy/scipy): sin muestras de terceros. La escala, el registro y la densidad de
notas son decisiones musicales del autor; esto es un punto de partida para escuchar y corregir.

Cómo se decide cada nota (todo sale de los datos de eventos.json, que salen del .blend):
  - Cuándo:   en el instante exacto en que una columna llega a su pico (el mismo en que se desprende su esfera).
  - Cuál:     el tono depende de la posición de la columna (MAPEO = "y": su altura en el plano; también "distancia"
              al centro de la onda o "angulo" alrededor de él), mapeada a una escala de 3 octavas.
  - Cuántas:  los picos se agrupan en tramos de RANURA fotogramas. Los tramos con pocos picos quedan en SILENCIO,
              los intermedios tocan 1 nota y los de mucha actividad hasta MAX_NOTAS: el ritmo sigue la densidad
              visual. Las notas se eligen al azar (semilla fija) entre los picos reales del tramo.
              Una caja de música no toca 146 notas por segundo.
  - Dónde:    la panorámica sigue a la posición X de la columna.
Timbre: lengüeta de peine (parciales inarmónicos de una barra en voladizo: 1, 6.27 y 17.55 veces la fundamental)
con un diminuto golpe de púa; las notas graves duran más que las agudas. Debajo, el zumbido de motor de la v1, muy bajo.

Bucle: dura lo mismo que la animación y cierra sin corte (se sintetizan tres vueltas y se toma la del medio).

Uso:  python sintetizar_002_caja.py eventos_002.json sonido_002_v2a.wav mayor     (o "menor")
Escribe también <salida>.notas.json con la partitura generada.
"""
import os
import sys
import json
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sintetizar_002 import capa_zumbido, cargar          # el zumbido de motor de la v1

# --- Parámetros (propuesta v2) ---
SR = 48000
SEMILLA = 2
RAIZ_MIDI = 72                 # do5 (523 Hz): punto de partida de la escala
ESCALAS = {"mayor": [0, 2, 4, 7, 9], "menor": [0, 3, 5, 7, 10]}     # pentatónicas
GRADOS = 15                    # 3 octavas de escala pentatónica (15 notas distintas)
CENTRO = (0.0, 0.5)            # origen de la onda ("Centro X/Y" del modificador)
MAPEO = "y"                    # qué decide el tono: "y", "distancia" o "angulo"
RANURA = 4                     # fotogramas por tramo (menor = más notas)
MAX_NOTAS = 2                  # notas máximas por tramo
SILENCIO_BAJO = 0.25           # los tramos con menos picos que este cuantil quedan en silencio
DOS_NOTAS_ALTO = 0.60          # los tramos con más picos que este cuantil tocan MAX_NOTAS
NOTA_NIVEL = 0.25
ZUMBIDO_FACTOR = 0.5           # el zumbido de la v1 multiplicado por esto (muy bajo)
PANORAMA = 0.8
PICO_DBFS = -3.0
NOMBRES = ["do", "do#", "re", "re#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]


def frecuencia(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def nombre(midi):
    return "%s%d" % (NOMBRES[midi % 12], midi // 12 - 1)


def lengueta(f, rng):
    """Una nota de caja de música: parciales inarmónicos de una barra en voladizo + golpe de púa."""
    N = int(SR * 1.6)
    t = np.arange(N) / SR
    tau = 0.55 * (523.25 / f) ** 0.55               # graves más largas, agudas más cortas
    y = np.zeros(N)
    for razon, amp, duracion in ((1.0, 1.0, 1.0), (6.27, 0.22, 0.35), (17.55, 0.06, 0.15)):
        fr = f * razon
        if fr < SR * 0.45:
            y += amp * np.sin(2 * np.pi * fr * t + rng.random() * 2 * np.pi) * np.exp(-t / (tau * duracion))
    y += 0.05 * rng.standard_normal(N) * np.exp(-t / 0.0006)              # púa
    y *= np.minimum(1.0, t / 0.0004)                                       # entrada de 0,4 ms: evita un pop
    return y / (np.max(np.abs(y)) + 1e-9)


def elegir_notas(picos, escala, rng):
    """[(posición en fotogramas, midi, x)]. El tono sale de MAPEO; la cantidad, de la densidad de picos del tramo."""
    x, y = picos[:, 1], picos[:, 2]
    if MAPEO == "y":
        v = (y - y.min()) / (y.max() - y.min())
    elif MAPEO == "distancia":
        d = np.hypot(x - CENTRO[0], y - CENTRO[1])
        v = d / d.max()
    else:                                                       # "angulo"
        v = (np.arctan2(y - CENTRO[1], x - CENTRO[0]) + np.pi) / (2 * np.pi)
    grado = np.rint(v * (GRADOS - 1)).astype(int)
    tramo = np.floor(picos[:, 0] / RANURA).astype(int)
    tramos, cuentas = np.unique(tramo, return_counts=True)
    bajo, alto = np.quantile(cuentas, [SILENCIO_BAJO, DOS_NOTAS_ALTO])
    notas = []
    for t, c in zip(tramos, cuentas):
        if c < bajo:
            continue                                            # silencio
        idx = np.where(tramo == t)[0]
        quiero = MAX_NOTAS if c > alto else 1
        usados = set()
        for i in rng.permutation(idx):
            if len(usados) >= quiero:
                break
            if grado[i] in usados:
                continue                                        # no repetir el mismo tono en el tramo
            usados.add(grado[i])
            oct_, k = divmod(int(grado[i]), 5)
            notas.append((float(picos[i, 0]), RAIZ_MIDI + 12 * oct_ + escala[k], float(x[i])))
    return sorted(notas)


def main(ruta_eventos, ruta_wav, modo):
    rng = np.random.default_rng(SEMILLA)
    fps, n, picos = cargar(ruta_eventos)
    T = int(round(n / fps * SR))
    notas = elegir_notas(picos, ESCALAS[modo], np.random.default_rng(SEMILLA + 1))
    x_ext = max(abs(picos[:, 1].min()), abs(picos[:, 1].max()))
    banco = {m: lengueta(frecuencia(m), rng) for m in {m for _, m, _ in notas}}
    L, R = np.zeros(3 * T), np.zeros(3 * T)
    for pos, midi, x in notas:
        pan = np.clip(x / x_ext, -1, 1) * PANORAMA
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        s = banco[midi] * NOTA_NIVEL * (0.85 + 0.15 * rng.random())
        for v in range(3):
            i = int(round(pos / fps * SR)) + v * T
            fin = min(i + len(s), len(L))
            L[i:fin] += s[:fin - i] * gl
            R[i:fin] += s[:fin - i] * gr
    z = capa_zumbido(fps, n, picos) * ZUMBIDO_FACTOR
    L, R = (L + z)[T:2 * T], (R + z)[T:2 * T]
    g = 10 ** (PICO_DBFS / 20) / max(np.max(np.abs(L)), np.max(np.abs(R)))
    wavfile.write(ruta_wav, SR, (np.stack([L, R], axis=1) * g * 32767).astype(np.int16))
    json.dump([{"t_s": round(p / fps, 4), "midi": m, "nota": nombre(m), "hz": round(frecuencia(m), 2), "x": x}
               for p, m, x in notas], open(ruta_wav + ".notas.json", "w"), ensure_ascii=False)
    print("Escrito %s (%s): %d notas en %.4f s (%.1f notas/s), %d notas distintas"
          % (ruta_wav, modo, len(notas), T / SR, len(notas) / (T / SR), len({m for _, m, _ in notas})))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "mayor")
