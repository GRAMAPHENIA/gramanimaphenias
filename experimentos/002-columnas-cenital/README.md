# 002 - Columnas cenital

Vista desde arriba de una grilla de 608 columnas instanciadas con Geometry Nodes. Una onda
deformada recorre la grilla; cada columna **se enciende al llegar al punto más alto y se va
apagando mientras cae**. Bucle perfecto de 6 s (144 fotogramas a 24 fps), vertical 1080x1920, EEVEE.

> Paleta (azul acero y ámbar), encuadre y ritmo **provisionales**: son una propuesta técnica,
> no una identidad visual. El autor decide la estética definitiva.

Preview: [`media/002-columnas-cenital.mp4`](../../media/002-columnas-cenital.mp4)

## Por qué existe
Nace de la revisión del [001](../001-ola-de-columnas/README.md): se veía el fondo (rompía la
inmersión), había demasiado protagonismo de efectos de luz (resplandor, grano) y parpadeos de color.
Aquí la cámara mira recto hacia abajo, no hay fondo visible y el único evento de luz es el destello
de cada columna.

## Requisitos
Blender 5.2 LTS. No necesita add-ons.

## Cómo reproducirlo
Desde la raíz del repositorio:
```powershell
$bl = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $bl -b --factory-startup -P scripts\setup_scene.py -- base\gramaphenia-base.blend
& $bl -b base\gramaphenia-base.blend -P experimentos\002-columnas-cenital\make_002.py -- experimentos\002-columnas-cenital\002.blend
.\scripts\render.ps1 -Blend experimentos\002-columnas-cenital\002.blend -Start 1 -End 144 -Out renders\002-cenital\f_
.\scripts\encode.ps1 -Pattern renders\002-cenital\f_%04d.png -Out renders\002-cenital\cenital.mp4
```

## Cómo funciona el destello
La altura sigue la fase de una onda, `p = ω·t − K·distancia + deformación(x, y)`:
```
altura  = H_MIN + (sin(p) + 1)/2 · AMP            # el pico ocurre en p = π/2
ciclo   = fract((p − π/2) / 2π)                    # 0 = recién en el pico, 0.5 = en el valle
brillo  = max( exp(−DECAY · ciclo),                # se apaga mientras cae
               smoothstep(0.88, 1.0, ciclo) )      # sube justo antes de llegar al pico
```
- La altura es simétrica (sube y baja igual), pero el brillo **no**: depende de cuánto tiempo pasó
  desde el último pico, por eso hace falta la fase y no solo la altura.
- La deformación depende solo de (x, y), no del tiempo; con `T_BUCLE` múltiplo de `T_ONDA` el
  bucle cierra sin corte.
- `Store Named Attribute` guarda `h` (altura) y `g` (brillo) en las instancias. El material lee `h`
  para el color base y `g` para la intensidad de emisión.

Para variar el resultado se cambian las constantes del inicio de `make_002.py`
(`DEFORM`, `LONG_ONDA`, `DECAY`, `EMISION`, colores...).

## Ajustes propios
- Cámara a 14 m mirando a -Z, focal 35 mm. Con sensor vertical es de 24 mm de alto.
- Un sol sin sombras. Las sombras entre columnas vecinas dejaban manchas claras que cambiaban
  de un fotograma al siguiente.
- Sin resplandor ni grano (se ponen a 0 sobre el compositor de la base). Sin suelo; mundo negro.

## Comprobaciones hechas
Sobre los 144 fotogramas, diferencia media entre fotogramas consecutivos:

| Medida | Resultado |
| --- | --- |
| Diferencia consecutiva (mín / media / máx) | 7,68 / 8,33 / 9,06 |
| Salto de segundo orden (máx / media) | 0,68 / 0,24 |
| Cierre del bucle, fotograma 144 a 1 | 7,91 |

Cambios graduales y sin picos: no hay parpadeo medible, y el cierre del bucle cae dentro del
rango normal. Es una medida de luminancia, no sustituye mirar el video.

## Medición
| Equipo | Fotogramas | s/frame | Pico de VRAM (toda la GPU) |
| --- | --- | --- | --- |
| i5-10500H, RTX 3050 Ti 4 GB | 144 | 2,04 | 1596 MiB |

Una corrida, con la GPU a unos 77 °C al empezar (ver el límite térmico en `docs/02-render-4gb.md`).

## Qué salió mal en el camino
- La primera versión quedó casi toda color crema: emisión de 5 y decaimiento lento hacían que todo
  lo alto brillara. Se bajó la emisión a 1,7 y se subió `DECAY` a 8.
- El color claro se veía blanco crema porque el mapeo de color desatura las luces fuertes. Se
  usó un naranja más saturado.
- Las sombras del sol dejaban manchas; se apagaron.
