# 002 - Columnas con esferas

Una ola deformada recorre una grilla de 608 columnas instanciadas con Geometry Nodes, vista en diagonal.
Cada columna **se enciende al llegar al punto más alto y se apaga mientras cae**, y en ese instante
**desprende una esfera** que sube frenando, se va achicando y se oscurece hasta desaparecer.
Bucle perfecto de 100 fotogramas (4,17 s a 24 fps), vertical 1080x1920, EEVEE.

> Paleta (azul acero y ámbar), cámara y ritmo **provisionales**: son una propuesta técnica, no una
> identidad visual. El autor decide la estética definitiva.

Preview de la versión actual, con el sonido de caja de música y el bucle repetido 3 veces (12,5 s):
[`media/002-columnas-esferas.mp4`](../../media/002-columnas-esferas.mp4).
`media/002-columnas-cenital.mp4` es de una versión anterior (cámara cenital, sin esferas) y se conserva.

## Evolución
1. Vista cenital con destello al llegar al pico (sin fondo visible, sin grano ni resplandor).
2. El autor eligió una cámara diagonal y bajó la velocidad de la onda; se volvió a cerrar el bucle (100 fotogramas).
3. Esferas que se desprenden de cada columna. Se probó una caída acelerada hasta la base y se descartó
   ("quedó rara"). Después se hizo que la esfera se achique de forma continua mientras sube.
4. Grafo ordenado en marcos y parámetros expuestos en el panel del modificador.

## Requisitos
Blender 5.2 LTS. No necesita add-ons.

## Cómo reproducirlo
Desde la raíz del repositorio. La cadena completa se verificó: genera un archivo idéntico (diferencia 0,0 en
las posiciones y escalas de las 1216 instancias en 6 fotogramas) al `002.blend` del repositorio.
```powershell
$bl = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$e = "experimentos\002-columnas-cenital"
& $bl -b --factory-startup -P scripts\setup_scene.py -- base\gramaphenia-base.blend
& $bl -b base\gramaphenia-base.blend `
  -P $e\make_002.py -P $e\anadir_esferas.py -P $e\exponer_parametros.py `
  -P $e\ordenar_nodos.py -P $e\distribuir_entradas.py -P $e\ordenar_nodos.py `
  --python-expr "import bpy; bpy.ops.wm.save_as_mainfile(filepath=r'$e\002.blend')" -- "$e\002.blend"
.\scripts\render.ps1 -Blend $e\002.blend -Start 1 -End 100 -Out renders\002\f_
.\scripts\encode.ps1 -Pattern renders\002\f_%04d.png -Out renders\002\columnas.mp4
```
El orden importa: `ordenar_nodos.py` va antes de `distribuir_entradas.py` (que reparte las entradas según los
marcos que ya existen) y otra vez después. Corrido sin interfaz, `ordenar_nodos.py` usa tamaños de nodo
aproximados; para el orden final, ejecutarlo con el archivo abierto en Blender:
`exec(open("experimentos/002-columnas-cenital/ordenar_nodos.py", encoding="utf-8").read())`.

| Script | Qué hace |
| --- | --- |
| `make_002.py` | Escena: columnas, material, sol sin sombras, cámara, grafo de la onda y el destello |
| `anadir_esferas.py` | Agrega las esferas (marco 9). Parámetros `LIFE`, `RISE`, `DIAM`, `NACE`, `APAGA` al inicio |
| `exponer_parametros.py` | Expone 11 parámetros en el panel del modificador |
| `distribuir_entradas.py` | Un nodo de entrada por marco, para que los cables sean cortos |
| `ordenar_nodos.py` | Marcos en color por defecto, títulos en mayúsculas, cuadrícula con tamaños reales |

## Cómo funciona
La altura sigue la fase de una onda, `p = 2π·fotograma/N − (2π/λ)·distancia + deformación(x, y)`:
```
altura  = H_MIN + (sin(p) + 1)/2 · AMP            # el pico ocurre en p = π/2
ciclo   = fract((p − π/2) / 2π)                    # 0 = recién en el pico, 0.5 = en el valle
brillo  = max( exp(−DECAY · ciclo),                # se apaga mientras cae
               smoothstep(0.88, 1.0, ciclo) )      # sube justo antes de llegar al pico
```
- La altura es simétrica, pero el brillo no: depende de cuánto tiempo pasó desde el último pico.
  Por eso hace falta la fase y no solo la altura.
- La **esfera** usa el mismo `ciclo`: edad = ciclo / vida. Sube con `1 − (1 − edad)²` (frena), se achica con
  un `smoothstep` desde el 15 % de su vida y su brillo es `(1 − edad)²`. Comparte el material de las columnas:
  nace igual que el pico y termina oscura. Sin simulación, por eso el bucle sigue cerrando.
- La deformación depende solo de (x, y): con `Frames por ciclo` = N y el rango de la animación igual a N
  (o múltiplo), el bucle cierra sin corte.
- `Store Named Attribute` guarda `h` (altura) y `g` (brillo) en las instancias; el material lee `h` para el
  color base y `g` para la intensidad de emisión.

## Parámetros del modificador
Aparecen en el panel del modificador "Columnas_cenital", sin abrir Geometry Nodes.

| Panel | Parámetro | Valor |
| --- | --- | --- |
| Onda | Frames por ciclo | 100 |
| Onda | Longitud de onda | 3,2 m |
| Onda | Deformación | 0,6 |
| Onda | Centro X / Centro Y | 0 / 0,5 |
| Destello | Apagado del destello | 8 |
| Columnas | Ancho de columna | 0,34 m |
| Esferas | Vida de la esfera | 0,55 |
| Esferas | Altura de ascenso | 2,5 m |
| Esferas | Diámetro de esfera | 0,26 m |
| Esferas | Inicio del encogimiento | 0,15 |

**Si se cambia "Frames por ciclo", hay que cambiar también el rango de la animación** al mismo valor para
que el bucle cierre (probado: con 50, el fotograma 1 y el 51 son idénticos).

No se exponen la amplitud ni la altura mínima: el material convierte altura en color con números fijos y
la esfera calcula su punto de partida con ellos. Los colores y la intensidad del destello viven en el
material, no en los nodos de geometría.

## Particularidades de Blender 5.2 encontradas
- Un modificador existente inicializa en 0 los sockets nuevos del grupo (no en su valor por defecto); hay que
  copiarlos. `exponer_parametros.py` lo hace.
- Por script, el modificador no reevalúa tras cambiar un valor si no se reasigna el grupo o se llama a
  `update_tag()` + `view_layer.update()`. Desde el panel funciona normal.
- El modificador no admite `keys()` ni claves de texto; los valores se leen con `mod.properties.inputs.Socket_N.value`.
- **"Local Space" de `Translate Instances`:** con el valor por defecto, el desplazamiento se multiplica por la
  escala de la instancia. En este grafo hace que las columnas altas queden **flotando** (a altura máxima el
  fondo queda a 1,2 m del suelo y la punta a 3,4 m). El autor decidió dejarlas así. Para apoyarlas en el
  suelo, desactivar "Local Space" en el nodo "Apoyar sobre el suelo" (cambia bastante el aspecto).

## Ajustes propios
- Cámara a (-27,69; 20,61; 24,58) con rotación (55,7°, 0°, -126,4°), focal 35 mm. Con sensor vertical es de 24 mm de alto.
- Sol sin sombras (las sombras entre columnas dejaban manchas claras que cambiaban entre fotogramas).
- Sin resplandor ni grano en el compositor, sin suelo y con mundo negro.

## Qué salió mal en el camino
- Versión inicial casi toda color crema (emisión de 5, decaimiento lento): se bajó la emisión a 1,7 y se subió
  `DECAY` a 8; el color se saturó a naranja porque el mapeo de color desatura las luces fuertes.
- Las sombras del sol dejaban manchas parpadeantes; se apagaron.
- La esfera con "Local Space" activo subía solo 1,2 m: el desplazamiento se multiplicaba por su tamaño (0,26).
- Mi primera comprobación de los parámetros dio una diferencia falsa de 2,63 m: los valores del modificador
  estaban en 0 hasta reasignar el grupo.
- Un solo nodo de entrada con 11 parámetros cruzaba el lienzo con cables largos e ilegibles; se repartió uno por marco.

## Sonido
**Elegida por el autor: la caja de música en pentatónica menor** (`sonido_002_v2b_pentatonica-menor.wav`). La mayor (v2a) y los ticks de la v1 se conservan como alternativas. El resto sigue siendo provisional hasta oírla junto al video.

Todo está en `sonido/`. El sonido se sintetiza con código (numpy/scipy), sin muestras de terceros, y los eventos
salen de los datos reales del `.blend`: el instante en que cada columna llega a su pico (el mismo en que se
desprende su esfera). El carácter del sonido, la escala y el registro son decisiones del autor.

| Archivo | Qué es |
| --- | --- |
| `extraer_eventos.py` | Lee el `.blend` (solo lectura) y guarda `eventos_002.json`: 608 picos con su instante sub-fotograma |
| `sintetizar_002.py` → `sonido_002_v1.wav` | v1: un tick mecánico por pico + zumbido de motor. A 146 clics por segundo se funden en una textura continua |
| `sintetizar_002_caja.py` → `sonido_002_v2a_pentatonica-mayor.wav`, `sonido_002_v2b_pentatonica-menor.wav` | v2: caja de música mecánica. Lengüeta de peine (parciales 1, 6,27 y 17,55) + zumbido muy bajo |
| `verificar_audio.py` | Comprobaciones objetivas (no sustituyen escucharlo) |

**v2:** el tono depende de la posición Y de la columna (escala pentatónica de 3 octavas desde do5); los picos se
agrupan en tramos de 4 fotogramas, los tramos con pocos picos quedan en silencio y los de mucha actividad tocan
hasta 2 notas. 28 notas en 4,17 s (6,7 por segundo, 13 tonos distintos, silencio más largo de 0,46 s). Parámetros al
inicio de `sintetizar_002_caja.py`: `MAPEO` (`y`, `distancia`, `angulo`), `RANURA`, `MAX_NOTAS`, escala, `RAIZ_MIDI`.

El audio dura exactamente lo mismo que la animación (200 000 muestras a 48 kHz = 100 fotogramas a 24 fps) y cierra
el bucle: se sintetizan tres vueltas y se toma la del medio. Regenerar:
```powershell
$bl = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$e = "experimentos\002-columnas-cenital"
$s = "$e\sonido"
& $bl -b $e\002.blend -P $s\extraer_eventos.py -- $s\eventos_002.json
python $s\sintetizar_002_caja.py $s\eventos_002.json $s\sonido_002_v2a_pentatonica-mayor.wav mayor
python $s\verificar_audio.py $s\eventos_002.json $s\sonido_002_v2a_pentatonica-mayor.wav $s\sonido_002_v2a_pentatonica-mayor.wav.notas.json
```

**Comprobado (v2a / v2b):** duración exacta, pico −3,0 dBFS sin recortes, RMS −16,9 / −17,2 dBFS, empalme del bucle
dentro del rango normal de saltos, y el tono medido de la nota coincide con el esperado: 26 de 28 y 25 de 28 notas suben
más de 6 dB en su frecuencia (las que no, repiten un tono que aún suena de una nota anterior). **No comprobado:** cómo
suena. Los ataques de las notas destacan poco sobre las colas de las anteriores (mediana ×1,3 a ×1,4 en agudos): las
notas se solapan y puede sonar a "velo"; si es así, acortar la caída (`tau` en `lengueta()`).
Mezcla con el video: `scripts/encode.ps1` acepta `-Audio` y `-Repetir` (probado con 100 fotogramas: video y audio duran lo mismo, 4,1667 s; con `-Repetir 3`, 12,5 s y 300 fotogramas).
```powershell
.\scripts\encode.ps1 -Pattern renders\002\f_%04d.png -Out renders\002\columnas.mp4 `
  -Audio experimentos\002-columnas-cenital\sonido\sonido_002_v2b_pentatonica-menor.wav -Repetir 3
```
Pendiente: renderizar la versión actual y oírla junto a la imagen.

## Medición
Versión actual (608 columnas + 608 esferas, 100 fotogramas, 1080x1920, EEVEE, 64 muestras):

| Equipo | Fotogramas | s/frame | Pico de VRAM (toda la GPU) |
| --- | --- | --- | --- |
| i5-10500H, RTX 3050 Ti 4 GB, GPU a 62 °C al empezar | 100 | 0,68 (67,5 s en total) | 2691 MiB |

Una sola corrida. El pico incluye otros programas abiertos (Blender con el archivo, el navegador...). Es 3 veces más
rápido que el 001 con grano y sombras (1,45 a 4,15 s): aquí no hay grano ni resplandor y el sol no proyecta sombras.
La versión cenital anterior (sin esferas, 144 fotogramas) tardó 2,04 s/fotograma.

**Comprobado en los 100 fotogramas:** diferencia de luminancia entre fotogramas consecutivos entre 1,86 y 2,38
(sin saltos: segundo orden máximo 0,08) y cierre del bucle fotograma 100 → 1 de 2,08, dentro de ese rango.
Revisado a tamaño real en el fotograma 50: las esferas nacen de un durazno claro, pasan por naranja y terminan marrón
oscuro y más pequeñas; las columnas van de azul oscuro (bajas) a durazno brillante (altas).

**Observación de composición:** el objeto ocupa solo el 41 % del alto del cuadro vertical; el resto es negro.
Es una decisión de encuadre del autor (cámara y focal), anotada por si se quiere acercar.
