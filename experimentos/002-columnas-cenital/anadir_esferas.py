"""Experimento 002: cada columna desprende una esfera al llegar a su punto más alto.

La esfera nace en el pico, sube frenando y se apaga. Usa el MISMO material de las columnas:
  h (color base) baja de "color alto" a "color bajo" y g (destello) cae con la edad al cuadrado,
  así que nace igual que el pico de la columna, pasa por naranja y termina oscura.

No usa simulación: todo sale del "ciclo" de la columna (fract de la fase, 0 = justo en el pico),
por eso el bucle sigue cerrando sin corte. Cada esfera vive menos de un ciclo (LIFE < 1), así que
nunca hay dos en la misma columna.

Uso sobre un archivo:
  blender -b experimentos/002-columnas-cenital/002.blend -P experimentos/002-columnas-cenital/anadir_esferas.py -- salida.blend
Uso en una sesión abierta (no guarda):
  exec(open("experimentos/002-columnas-cenital/anadir_esferas.py", encoding="utf-8").read())

Es idempotente: si ya existe "Marco 9" no hace nada.
Depende de los nombres de nodo de make_002.py / del orden del grupo "Columnas_cenital".
"""
import sys
import bpy

# --- Parámetros ---
LIFE = 0.55      # fracción del ciclo que vive la esfera (menor que 1)
RISE = 2.5       # metros que sube desde la punta de la columna
DIAM = 0.26      # diámetro de la esfera (m); la columna mide 0.34
NACE = 0.10      # tramo inicial de su vida en que crece desde 0
APAGA = 0.75     # desde esta fracción de su vida se encoge hasta desaparecer


def agregar_esferas(g):
    N, L = g.nodes, g.links.new
    if "Marco 9" in N:
        print("Las esferas ya existen: no se hace nada.")
        return
    ciclo = N["Math.022"].outputs[0]                    # 0 = en el pico, 0.5 = en el valle
    amp = 2 * N["Math.018"].inputs[1].default_value     # amplitud de la altura
    h_min = N["Math.019"].inputs[1].default_value
    h_max = h_min + amp
    # Punta real de la columna en el pico. Con "Local Space" activo en "Translate Instances", el
    # desplazamiento se multiplica por la escala (altura): punta = a*(a+1)/2 en vez de a.
    local = N["Translate Instances"].inputs["Local Space"].default_value
    punta = h_max * (h_max + 1) / 2 if local else h_max
    mat =N["Set Material"].inputs["Material"].default_value
    final_columnas = N["Store Named Attribute.001"]
    salida = N["Group Output"]
    marco8 = N.get("Marco 8")

    f = N.new("NodeFrame")
    f.name = "Marco 9"
    f.label = "9 · Esferas: se desprenden en el pico y suben apagándose"
    f.label_size = 22
    f.use_custom_color = True
    f.color = (0.36, 0.30, 0.40)
    f.shrink = True
    OX, OY, S = 3220, -1500, 240

    def nodo(kind, etq, cx, cy):
        n = N.new(kind)
        n.label = etq
        n.parent = f
        n.location_absolute = (OX + cx * S, OY + cy)
        return n

    def mat_(op, etq, a, b, cx, cy, clamp=False):
        n = nodo("ShaderNodeMath", etq, cx, cy)
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if hasattr(v, "node"):
                L(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    # Edad: 0 al nacer (en el pico), 1 al morir
    edad = mat_("DIVIDE", "Edad (0 = nace en el pico, 1 = muere)", ciclo, LIFE, 0, 0, clamp=True)
    resta = mat_("SUBTRACT", "1 − edad", 1.0, edad, 1, 0)
    cuad = mat_("MULTIPLY", "(1 − edad)²  = destello", resta, resta, 2, 0)

    # Posición: sube frenando
    avance = mat_("SUBTRACT", "Avance (frena al subir)", 1.0, cuad, 3, 0)
    alto = mat_("MULTIPLY", "× Altura de ascenso", avance, RISE, 4, 0)
    z = mat_("ADD", "+ punta de la columna", alto, punta + DIAM / 2, 5, 0)
    pos = nodo("ShaderNodeCombineXYZ", "Posición (0, 0, z)", 6, 0)
    L(z, pos.inputs["Z"])

    # Tamaño: crece al nacer, se encoge al morir
    crece = nodo("ShaderNodeMapRange", "Crece al nacer", 1, -260)
    crece.interpolation_type = "SMOOTHSTEP"
    crece.clamp = True
    crece.inputs["From Min"].default_value = 0.0
    crece.inputs["From Max"].default_value = NACE
    L(edad, crece.inputs["Value"])
    encoge = nodo("ShaderNodeMapRange", "Se encoge al morir", 1, -560)
    encoge.interpolation_type = "SMOOTHSTEP"
    encoge.clamp = True
    encoge.inputs["From Min"].default_value = APAGA
    encoge.inputs["From Max"].default_value = 1.0
    L(edad, encoge.inputs["Value"])
    inv = mat_("SUBTRACT", "1 − encogimiento", 1.0, encoge.outputs["Result"], 2, -560)
    tam = mat_("MULTIPLY", "Tamaño (0 a 1)", crece.outputs["Result"], inv, 3, -420)
    diam = mat_("MULTIPLY", "× Diámetro", tam, DIAM, 4, -420)
    escala = nodo("ShaderNodeCombineXYZ", "Escala (d, d, d)", 5, -420)
    for eje in ("X", "Y", "Z"):
        L(diam, escala.inputs[eje])

    # Color: mismo material de las columnas (h = color base, g = destello)
    h1 = mat_("MULTIPLY", "(1 − edad) × Amplitud", resta, amp, 2, -780)
    h2 = mat_("ADD", "+ Altura mínima = color", h1, h_min, 3, -780)

    # Esfera
    esf = nodo("GeometryNodeMeshUVSphere", "Esfera", 0, -1080)
    esf.inputs["Segments"].default_value = 24
    esf.inputs["Rings"].default_value = 12
    esf.inputs["Radius"].default_value = 0.5
    geo_esf = esf.outputs["Mesh"]
    try:
        liso = nodo("GeometryNodeSetShadeSmooth", "Suavizar", 1, -1080)
        L(geo_esf, liso.inputs["Geometry"])
        geo_esf = liso.outputs["Geometry"]
    except RuntimeError:
        pass
    set_mat = nodo("GeometryNodeSetMaterial", "Material de columna (el mismo)", 2, -1080)
    set_mat.inputs["Material"].default_value = mat
    L(geo_esf, set_mat.inputs["Geometry"])

    inst = nodo("GeometryNodeInstanceOnPoints", "Esfera en cada punto", 7, -300)
    L(N["Grid"].outputs["Mesh"], inst.inputs["Points"])
    L(set_mat.outputs["Geometry"], inst.inputs["Instance"])
    L(escala.outputs["Vector"], inst.inputs["Scale"])
    sube = nodo("GeometryNodeTranslateInstances", "Subir", 8, -300)
    sube.inputs["Local Space"].default_value = False   # si no, el desplazamiento se multiplica por el tamaño
    L(inst.outputs["Instances"], sube.inputs["Instances"])
    L(pos.outputs["Vector"], sube.inputs["Translation"])

    def guardar(geo, etq, nombre, valor, cx):
        s = nodo("GeometryNodeStoreNamedAttribute", etq, cx, -300)
        s.data_type = "FLOAT"
        s.domain = "INSTANCE"
        s.inputs["Name"].default_value = nombre
        L(geo, s.inputs["Geometry"])
        L(valor, s.inputs["Value"])
        return s.outputs["Geometry"]

    geo = guardar(sube.outputs["Instances"], "Guardar h (color base)", "h", h2, 9)
    geo = guardar(geo, "Guardar g (destello)", "g", cuad, 10)

    # Unir columnas + esferas antes de la salida
    join = N.new("GeometryNodeJoinGeometry")
    join.label = "Unir columnas + esferas"
    if marco8:
        join.parent = marco8
    x, y = salida.location_absolute
    join.location_absolute = (x, y)
    salida.location_absolute = (x + 260, y)
    for enlace in [l for l in g.links if l.to_node == salida]:
        g.links.remove(enlace)
    L(final_columnas.outputs["Geometry"], join.inputs[0])
    L(geo, join.inputs[0])
    L(join.outputs["Geometry"], salida.inputs["Geometry"])
    for n in N:
        n.select = False
    print("Esferas agregadas: nodos", len(N), "| enlaces", len(g.links))


agregar_esferas(bpy.data.node_groups["Columnas_cenital"])
if "--" in sys.argv:
    destino = sys.argv[sys.argv.index("--") + 1]
    bpy.ops.wm.save_as_mainfile(filepath=destino)
    print("Guardado:", destino)
