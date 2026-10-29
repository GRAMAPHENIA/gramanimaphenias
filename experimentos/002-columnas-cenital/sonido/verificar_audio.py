"""Experimento 002, sonido: comprobaciones objetivas del WAV (no sustituyen escucharlo).

  1. Duración exacta = fotogramas / fps.
  2. Nivel: pico y RMS, y que no haya recortes.
  3. Bucle: salto entre la última y la primera muestra, comparado con el salto típico entre muestras vecinas,
     y diferencia de energía en los 20 ms a cada lado del empalme.
  4. Sincronía: la energía de agudos por fotograma (los ticks) debe seguir la cantidad de picos por fotograma.

  5. (con la partitura <wav>.notas.json) Tono: la frecuencia medida de cada nota aislada coincide con la esperada.
  6. (con la partitura) Ataques: hay un aumento real de energía en el instante de cada nota.

Uso:  python verificar_audio.py eventos_002.json sonido_002_v1.wav [sonido_002_v2a.wav.notas.json]
"""
import sys
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

d = json.load(open(sys.argv[1]))
fps, n, picos = d["fps"], d["fotogramas"], np.array(d["picos"])
sr, x = wavfile.read(sys.argv[2])
x = x.astype(float) / 32768
mono = x.mean(axis=1)

esperado = int(round(n / fps * sr))
print("1) duración: %d muestras, esperado %d -> %s" % (len(x), esperado, "OK" if len(x) == esperado else "DISTINTA"))

pico = np.max(np.abs(x))
rms = np.sqrt(np.mean(mono ** 2))
print("2) nivel: pico %.1f dBFS | RMS %.1f dBFS | muestras al máximo (recorte): %d"
      % (20 * np.log10(pico), 20 * np.log10(rms), int(np.sum(np.abs(x) >= 0.9999))))

salto = abs(mono[0] - mono[-1])
tipico = np.median(np.abs(np.diff(mono)))
v = int(0.020 * sr)
e_fin, e_ini = np.sqrt(np.mean(mono[-v:] ** 2)), np.sqrt(np.mean(mono[:v] ** 2))
saltos = np.abs(np.diff(mono))
percentil = 100 * np.mean(saltos < salto)
print("3) bucle: salto de empalme %.4f (mayor que el %.1f%% de los saltos entre muestras vecinas; mediana %.4f; máximo %.4f)"
      " | RMS 20 ms antes %.4f, después %.4f" % (salto, percentil, tipico, saltos.max(), e_fin, e_ini))

notas = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
sos = signal.butter(4, 1500, btype="high", fs=sr, output="sos")
agudos = signal.sosfilt(sos, mono) ** 2
por_frame = agudos[: n * (len(mono) // n)].reshape(n, -1).sum(axis=1)
cuenta = np.bincount(np.floor(picos[:, 0]).astype(int) % n, minlength=n).astype(float)
r = np.corrcoef(por_frame, cuenta)[0, 1]
r_desfase = np.corrcoef(np.roll(por_frame, n // 2), cuenta)[0, 1]
if notas is None:
    print("4) sincronía: correlación energía de agudos vs picos por fotograma = %.3f (con desfase de media vuelta: %.3f)" % (r, r_desfase))
else:
    ts = np.array([e["t_s"] for e in notas])
    dur = len(mono) / sr
    print("4) notas: %d en %.2f s (%.1f por segundo), %d tonos distintos, silencio más largo %.2f s"
          % (len(notas), dur, len(notas) / dur, len({e["midi"] for e in notas}),
             max(np.diff(np.concatenate([ts, [ts[0] + dur]])))))
    # 5) tono: la energía en la banda de la nota (±2 %) sube al menos 6 dB justo después de su ataque
    def banda_db(i, hz):
        seg = mono[i:i + int(0.05 * sr)]
        if len(seg) < int(0.05 * sr):
            seg = np.concatenate([seg, mono[: int(0.05 * sr) - len(seg)]])      # el bucle es circular
        w = np.hanning(len(seg))
        f = np.fft.rfftfreq(1 << 15, 1 / sr)
        e = np.abs(np.fft.rfft(seg * w, 1 << 15)) ** 2
        sel = (f > hz * 0.98) & (f < hz * 1.02)
        return 10 * np.log10(e[sel].sum() + 1e-12)
    sube = []
    for e in notas:
        i = int(e["t_s"] * sr)
        antes = banda_db((i - int(0.05 * sr)) % len(mono), e["hz"])
        despues = banda_db((i + int(0.003 * sr)) % len(mono), e["hz"])
        sube.append(despues - antes)
    sube = np.array(sube)
    print("5) tono: %d de %d notas suben >= 6 dB en su propia frecuencia tras el ataque (mediana +%.0f dB)"
          % (int(np.sum(sube >= 6)), len(notas), np.median(sube)))
    # 6) ataque: energía justo después del instante de la nota frente a la anterior
    razones = []
    agudos_f = signal.sosfilt(signal.butter(4, 450, btype="high", fs=sr, output="sos"), mono)
    for e in notas:
        i = int(e["t_s"] * sr)
        antes = np.sqrt(np.mean(agudos_f[max(i - int(0.02 * sr), 0):max(i - int(0.002 * sr), 1)] ** 2)) if i > 200 else None
        despues = np.sqrt(np.mean(agudos_f[i:i + int(0.01 * sr)] ** 2))
        if antes:
            razones.append(despues / (antes + 1e-9))
    razones = np.array(razones)
    print("6) ataques: %.0f%% de las notas suben la energía de agudos al menos 1,5x en sus primeros 10 ms (mediana x%.1f)"
          % (100 * np.mean(razones > 1.5), np.median(razones)))
