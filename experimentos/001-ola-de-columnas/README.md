# 001 - Ola de columnas

Una ola circular recorre una grilla de 319 columnas instanciadas con Geometry Nodes.
Bucle perfecto de 4 s (96 fotogramas a 24 fps), vertical 1080x1920, EEVEE.

> Paleta y encuadre **provisionales**: son una propuesta técnica neutra, no una identidad
> visual. El autor decide la estética definitiva.

Preview: [`media/001-ola-de-columnas.mp4`](../../media/001-ola-de-columnas.mp4)

## Qué muestra
- Instancias con Geometry Nodes (una sola malla de cubo repetida 319 veces).
- Animación 100 % procedural: no hay fotogramas clave, todo sale del tiempo de la escena.
- Un atributo guardado en las instancias (`h`) que el material lee para colorear.
- Grano de película en el compositor (ruido blanco 4D que cambia en cada fotograma).

## Requisitos
Blender 5.2 LTS. No necesita add-ons.

## Cómo reproducirlo
Desde la raíz del repositorio:
```powershell
$bl = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $bl -b --factory-startup -P scripts\setup_scene.py -- base\gramaphenia-base.blend
& $bl -b base\gramaphenia-base.blend -P experimentos\001-ola-de-columnas\make_001.py -- experimentos\001-ola-de-columnas\001.blend
.\scripts\render.ps1 -Blend experimentos\001-ola-de-columnas\001.blend -Start 1 -End 96 -Out renders\001-ola\f_
.\scripts\encode.ps1 -Pattern renders\001-ola\f_%04d.png -Out renders\001-ola\ola.mp4
```

## Receta de nodos
```
Grid (11 x 29 puntos, 5 x 14 m)
   -> Instance on Points (instancia: Cubo 1 m con material, escala = (0.42, 0.42, altura))
   -> Translate Instances (sube altura / 2 para que apoyen en el suelo)
   -> Store Named Attribute "h" (dominio Instancia)
   -> salida
altura = 0.25 + (sin(distancia_al_origen * 1.2 - 2π * segundos / 4) + 1) / 2 * 2.2
```
- El periodo de 4 s coincide con el rango de fotogramas: el cuadro 96 vuelve a la fase del 0.
- Material: Attribute (tipo *Instancer*, nombre `h`) -> Map Range -> ColorRamp -> Base Color.

## Ajustes propios de este experimento
- Luces fijadas en valores absolutos (450 W y 240 W) y mundo (0,04, 0,04, 0,05), para que
  la imagen no dependa de cambios futuros en la escena base.
- Cámara en (0, -10, 9) mirando a (0, 1.5, 0.8), focal 24 mm. Con ajuste de sensor vertical,
  Blender usa un sensor de 24 mm de alto, así que 50 mm da un campo muy estrecho.
- Luces de la escena base multiplicadas por 3.

## Medición
| Equipo | Fotogramas | s/frame | Pico de VRAM (toda la GPU) |
| --- | --- | --- | --- |
| i5-10500H, RTX 3050 Ti 4 GB, máquina fría, sin grano | 96 | 1,45 | 2853 MiB |
| ídem, con grano, tras varios renders seguidos (GPU a 88 °C) | 96 | 4,15 | 1676 MiB |

El grano no cambia el tiempo: un mismo fotograma tarda lo mismo con y sin él (2,67 s contra
2,78 s). La diferencia entre filas es **límite térmico** de la laptop. El pico de VRAM es de toda
la GPU, incluye otros programas (ver `docs/02-render-4gb.md`). Una sola corrida por fila.

## Qué salió mal en el camino
- Primera cámara baja con 50 mm: las columnas cercanas llenaban el cuadro y la escena salía oscura.
  Se corrigió con vista elevada, focal de 24 mm y paleta más clara.
- Se verificó con un script que el modificador generaba 319 instancias (11 x 29): el problema
  era la cámara, no la grilla.

- Se publicó primero un `.blend` construido con una base antigua (luces de 450 W y mundo de 0,04)
  mientras la receta, al rehacerse desde cero, daba una imagen más quemada (1800 W). Se detectó
  comparando los dos archivos; la solución fue fijar los valores en `make_001.py`.
- Mi primer grano usaba el modo Overlay y quemaba la imagen (valores de luz lineal por encima
  de 1). Se cambió a Linear Light, que suma ruido centrado en cero y no altera el brillo medio.

## Ideas para variar
Cambiar `FREQ`, `PERIODO_S`, `PASO` y la rampa de color al inicio de `make_001.py`.
