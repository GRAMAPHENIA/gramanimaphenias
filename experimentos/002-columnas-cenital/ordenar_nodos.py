"""Experimento 002: ordena el grafo "Columnas_cenital" en marcos compactos y legibles.

Qué hace (solo posiciones, marcos y etiquetas; no cambia valores ni conexiones):
  - Agrupa los nodos en 8 marcos de izquierda a derecha, y la esfera en un marco 9 con 5 submarcos.
  - Coloca cada marco en una cuadrícula usando el tamaño REAL de los nodos (columnas de izquierda a derecha,
    apiladas de arriba a abajo), así que no hay nodos superpuestos y los enlaces quedan cortos.
  - Los marcos usan el color por defecto y sus títulos van en MAYÚSCULAS.

Necesita una sesión de Blender con editor de nodos (usa node.dimensions). Uso, con el archivo abierto:
  exec(open("experimentos/002-columnas-cenital/ordenar_nodos.py", encoding="utf-8").read())
Es idempotente: borra los marcos anteriores y los vuelve a crear.
Depende de los nombres de nodo de make_002.py y de las etiquetas de anadir_esferas.py.
"""
import math
import bpy

g = bpy.data.node_groups["Columnas_cenital"]
N = g.nodes
ESC = bpy.context.preferences.system.ui_scale

GAP_X, GAP_Y = 60, 40            # entre nodos
PAD_X, PAD_ARRIBA, PAD_ABAJO = 40, 70, 40    # margen interior de un marco (arriba deja sitio al título)
GAP_MARCOS = 60


def tam(n):
    """(ancho, alto) del nodo en unidades de nodo."""
    if n.dimensions.y == 0:
        return (n.width, 150)
    return (n.dimensions.x / ESC, n.dimensions.y / ESC)


# --- Reunir los nodos antes de borrar los marcos viejos ---
esfera = {n.label: n for n in N if n.parent and n.parent.name.startswith("Marco 9") and n.type != "FRAME"}
union = next((n for n in N if n.type == "JOIN_GEOMETRY"), None)
# Nodos de entrada del grupo: los que alimentan a un solo marco van dentro de ese marco (como primera columna);
# los que alimentan a varios (o a ninguno) van juntos en un marco 0. Se decide ANTES de borrar los marcos.
entradas = [n for n in N if n.type == "GROUP_INPUT"]


def _marco_unico(ent):
    padres = {l.to_node.parent.name if l.to_node.parent else None for s in ent.outputs for l in s.links}
    return padres.pop() if len(padres) == 1 else None


locales = {}
for ent in entradas:
    p = _marco_unico(ent)
    if p:
        locales.setdefault(p, []).append(ent)
globales = [e for e in entradas if _marco_unico(e) is None]
for f in [n for n in N if n.type == "FRAME"]:
    N.remove(f)


def marco(nombre, titulo, padre=None):
    f = N.new("NodeFrame")
    f.name = nombre
    f.label = titulo.upper()
    f.label_size = 20
    f.use_custom_color = False       # color por defecto
    f.shrink = True
    if padre:
        f.parent = padre
    return f


def bloque(f, columnas, x, y):
    """Coloca 'columnas' (lista de listas de nodos) dentro del marco f con su esquina superior izquierda en (x, y).
    Devuelve (ancho, alto) del marco resultante."""
    if locales.get(f.name):
        columnas = [locales[f.name]] + columnas       # la entrada de parámetros, a la izquierda del marco
    cx = x + PAD_X
    alto = 0
    for col in columnas:
        cy = y - PAD_ARRIBA
        ancho = max(tam(n)[0] for n in col)
        for n in col:
            n.parent = f
            n.location_absolute = (cx, cy)
            cy -= tam(n)[1] + GAP_Y
        alto = max(alto, (y - PAD_ARRIBA) - (cy + GAP_Y))
        cx += ancho + GAP_X
    return (cx - GAP_X - x + PAD_X, alto + PAD_ARRIBA + PAD_ABAJO)


M = lambda *nombres: [N[n] for n in nombres if n in N]      # ignora los que aún no existen

# --- Fila superior: el flujo de la señal, de izquierda a derecha ---
x = 0
if globales:                      # entradas que alimentan a varios marcos o a ninguno
    for e in globales:
        e.label = "Parámetros" if any(s.is_linked for s in e.outputs) else "Entrada (sin uso)"
    f0 = marco("Marco 0", "0 · Parámetros del modificador")
    w0, h0 = bloque(f0, [globales], x, 0)
    x += w0 + GAP_MARCOS

f1 = marco("Marco 1", "1 · Coordenadas")
w1, h1 = bloque(f1, [M("Position"), M("Separate XYZ")], x, 0)
x += w1 + GAP_MARCOS

f2 = marco("Marco 2", "2 · Distancia al centro")
w2, h2 = bloque(f2, [M("Math", "Math.001"), M("Math.002", "Math.003"), M("Math.004"), M("Math.005")], x, 0)
f3 = marco("Marco 3", "3 · Deformación fija (no depende del tiempo)")
w3, h3 = bloque(f3, [M("Math.006", "Math.008"), M("Math.007", "Math.009"), M("Math.010"), M("Math.011")],
                x, -(h2 + GAP_MARCOS))
alto_filaA = h2 + GAP_MARCOS + h3
x += max(w2, w3) + GAP_MARCOS

f4 = marco("Marco 4", "4 · Fase de la onda")
w4, h4 = bloque(f4, [M("Scene Time", "P_omega", "P_K"), M("Math.012", "Math.013"), M("Math.014"), M("Math.015")], x, 0)
x += w4 + GAP_MARCOS

f5 = marco("Marco 5", "5 · Altura de la columna")
w5, h5 = bloque(f5, [M("Math.016"), M("Math.017"), M("Math.018"), M("Math.019")], x, 0)
f6 = marco("Marco 6", "6 · Destello: se enciende en el pico y se apaga al caer")
w6, h6 = bloque(f6, [M("Math.020"), M("Math.021"), M("Math.022", "P_decay"), M("Math.023", "Map Range"),
                     M("Math.024"), M("Math.025")], x, -(h5 + GAP_MARCOS))
x_f9 = x                                  # la esfera se ubica debajo, desde aquí
x += max(w5, w6) + GAP_MARCOS

f7 = marco("Marco 7", "7 · Columnas")
w7, h7 = bloque(f7, [M("Grid", "Cube", "Math.026"), M("Set Material", "Combine XYZ", "Combine XYZ.001"),
                     M("Instance on Points"), M("Translate Instances")], x, 0)
x += w7 + GAP_MARCOS

f8 = marco("Marco 8", "8 · Guardar y salir")
cols8 = [M("Store Named Attribute"), M("Store Named Attribute.001")]
if union:
    union.label = "Unir columnas + esferas"
    cols8.append([union])
cols8.append(M("Group Output"))
w8, h8 = bloque(f8, cols8, x, 0)

# --- Esfera: marco 9 con 5 submarcos en dos filas, debajo de la fila superior ---
if esfera:
    E = lambda *etiquetas: [esfera[e] if e in esfera else N[e] for e in etiquetas if e in esfera or e in N]
    y9 = -(max(alto_filaA, h5 + GAP_MARCOS + h6, h7) + 2 * GAP_MARCOS)
    f9 = marco("Marco 9", "9 · Esferas: se desprenden en el pico y suben apagándose")
    # fila 1
    xs = x_f9 + PAD_X
    ys = y9 - PAD_ARRIBA
    a = marco("Marco 9a", "Edad y destello", f9)
    wa, ha = bloque(a, [E("Edad (0 = nace en el pico, 1 = muere)"), E("1 − edad"),
                        E("(1 − edad)²  = destello")], xs, ys)
    b = marco("Marco 9b", "Ascenso", f9)
    wb, hb = bloque(b, [E("Avance (frena al subir)"), E("× Altura de ascenso"), E("P_radio", "P_z0"),
                        E("+ punta de la columna"), E("Posición (0, 0, z)")], xs + wa + GAP_MARCOS, ys)
    d = marco("Marco 9d", "Color", f9)
    wd, hd = bloque(d, [E("(1 − edad) × Amplitud"), E("+ Altura mínima = color")],
                    xs + wa + wb + 2 * GAP_MARCOS, ys)
    # fila 2
    ys2 = ys - max(ha, hb, hd) - GAP_MARCOS
    c = marco("Marco 9c", "Tamaño", f9)
    wc, hc = bloque(c, [E("Crece al nacer", "Se encoge al morir"), E("1 − encogimiento"), E("Tamaño (0 a 1)"),
                        E("× Diámetro"), E("Escala (d, d, d)")], xs, ys2)
    e = marco("Marco 9e", "Esfera e instancias", f9)
    bloque(e, [E("Esfera", "Suavizar", "Material de columna (el mismo)"), E("Esfera en cada punto"),
               E("Subir"), E("Guardar h (color base)", "Guardar g (destello)")], xs + wc + GAP_MARCOS, ys2)

for n in N:
    n.select = False


# --- Informe ---
def centro(n):
    w, h = tam(n)
    x, y = n.location_absolute
    return (x + w / 2, y - h / 2)


largo = sum(math.hypot(centro(l.from_node)[0] - centro(l.to_node)[0], centro(l.from_node)[1] - centro(l.to_node)[1])
            for l in g.links)
nodos = [n for n in N if n.type != "FRAME"]
print("Ordenado: %d nodos, %d enlaces | longitud total de enlaces: %.0f | extensión: %.0f x %.0f" % (
    len(nodos), len(g.links), largo,
    max(centro(n)[0] for n in nodos) - min(centro(n)[0] for n in nodos),
    max(centro(n)[1] for n in nodos) - min(centro(n)[1] for n in nodos)))
