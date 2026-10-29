# 002 - Columnas con esferas

Una ola deformada recorre una grilla de 608 columnas instanciadas con Geometry Nodes, vista en diagonal.
Cada columna **se enciende al llegar al punto más alto y se apaga mientras cae**, y en ese instante
**desprende una esfera** que sube frenando, se va achicando y se oscurece hasta desaparecer.
Bucle perfecto de 100 fotogramas (4,17 s a 24 fps), vertical 1080x1920, EEVEE.

> Paleta (azul acero y ámbar), cámara y ritmo **provisionales**: son una propuesta técnica, no una
> identidad visual. El autor decide la estética definitiva.

> **El video de `media/002-columnas-cenital.mp4` es de una versión anterior** (cámara cenital, sin esferas,
> 144 fotogramas). Todavía no hay render de la versión actual.

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

## Medición
No hay medición de la versión actual (con esferas). La de la versión cenital anterior (608 columnas, 144
fotogramas): 2,04 s/fotograma, pico de VRAM 1596 MiB en toda la GPU, con la GPU a unos 77 °C al empezar
(ver el límite térmico en `docs/02-render-4gb.md`).
