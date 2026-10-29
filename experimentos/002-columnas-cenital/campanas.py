"""Experimento 002: esferas "campana" = las esferas que suenan (la caja de música).

Antes sonaban 28 notas elegidas al azar entre 608 esferas: no había forma de saber cuál esfera era "la que suena".
Ahora una esfera de cada N columnas (en filas y columnas de la grilla) es una CAMPANA: más grande y más brillante,
y es la única que toca una nota, en el instante en que nace. Lo que se ve y lo que se oye se corresponden uno a uno.

Selección (solo con posiciones, sin azar, así el audio la reproduce exactamente):
  ix = redondear((x - x_mín) / paso),  iy = redondear((y - y_mín) / paso)
  campana = (ix mod N == 0) y (iy mod N == 0)           con la grilla 19 x 32 y N = 4 -> 5 x 8 = 40 campanas
Efecto: diámetro de la esfera x TAMAÑO y brillo (destello) x BRILLO si es campana. Con TAMAÑO = 1 y BRILLO = 1 el
resultado es idéntico al de antes.

Parámetros nuevos en el panel del modificador, panel "Campanas":
  Separación de campanas (entero, 4)   cada cuántas columnas hay una campana (1 = todas son campana)
  Tamaño de campana (1.8)              multiplicador del diámetro
  Brillo de campana (1.8)              multiplicador del destello

Uso con el archivo abierto (después de exponer_parametros.py; antes de ordenar_nodos.py):
  exec(open("experimentos/002-columnas-cenital/campanas.py", encoding="utf-8").read())
Es idempotente. El audio (sonido/sintetizar_002_v4.py) usa la misma regla; si se cambia la separación aquí, hay que
pasar el mismo valor allí.
"""
import bpy

g = bpy.data.node_groups["Columnas_cenital"]
N, L = g.nodes, g.links.new
CAMPANA_PASO, CAMPANA_TAMANO, CAMPANA_BRILLO = 4, 1.8, 1.8


def agregar():
    if "C_flag" in N:
        print("Las campanas ya existen: no se hace nada.")
        return
    etiqueta = {n.label: n for n in N if n.label}
    grid = N["Grid"]
    tam_x, tam_y = grid.inputs["Size X"].default_value, grid.inputs["Size Y"].default_value
    paso_x = tam_x / (grid.inputs["Vertices X"].default_value - 1)
    paso_y = tam_y / (grid.inputs["Vertices Y"].default_value - 1)
    xyz = N["Separate XYZ"]

    # --- Parámetros nuevos en la interfaz del grupo ---
    panel = g.interface.new_panel("Campanas")
    nuevos = [
        ("Separación de campanas", "NodeSocketInt", CAMPANA_PASO, 1, 32,
         "Cada cuántas columnas (en filas y columnas de la grilla) hay una esfera campana, la que toca una nota. 1 = todas."),
        ("Tamaño de campana", "NodeSocketFloat", CAMPANA_TAMANO, 1.0, 4.0, "Multiplicador del diámetro de las esferas campana. 1 = igual que las demás."),
        ("Brillo de campana", "NodeSocketFloat", CAMPANA_BRILLO, 1.0, 4.0, "Multiplicador del destello de las esferas campana. 1 = igual que las demás."),
    ]
    for nombre, tipo, d, mn, mx, desc in nuevos:
        s = g.interface.new_socket(nombre, in_out="INPUT", socket_type=tipo, parent=panel)
        s.default_value, s.min_value, s.max_value, s.description = d, mn, mx, desc
    # (los modificadores existentes inicializan los sockets nuevos en 0: copiar los valores por defecto)
    for o in bpy.data.objects:
        for m in o.modifiers:
            if m.type == "NODES" and m.node_group == g:
                m.node_group = None
                m.node_group = g
                for i in g.interface.items_tree:
                    if i.item_type == "SOCKET" and i.in_out == "INPUT" and hasattr(i, "default_value"):
                        getattr(m.properties.inputs, i.identifier).value = i.default_value
                o.update_tag()

    # --- Marco, entrada local y nodos ---
    padre = N.get("Marco 9")
    marco = N.new("NodeFrame")
    marco.name = "Marco 9f"
    marco.label = "CAMPANAS: ESFERAS QUE SUENAN"
    marco.label_size = 20
    marco.use_custom_color = False
    marco.shrink = True
    if padre:
        marco.parent = padre
    ent = N.new("NodeGroupInput")
    ent.name, ent.label, ent.parent = "Entrada Marco 9f", "Parámetros", marco
    ref = etiqueta["× Diámetro"]
    ox, oy = ref.location_absolute

    def mat_(nombre, etq, op, a, b=None):
        n = N.new("ShaderNodeMath")
        n.name, n.label, n.operation, n.parent = nombre, etq, op, marco
        n.location_absolute = (ox, oy)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if hasattr(v, "node"):
                L(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    sep = ent.outputs["Separación de campanas"]
    # posición en la grilla -> índice entero -> ¿es múltiplo de la separación?
    fx = mat_("C_fx", "Columna X es campana", "LESS_THAN",
              mat_("C_ix_m", "Índice X mod separación", "FLOORED_MODULO",
                   mat_("C_ix", "Índice X (entero)", "ROUND",
                        mat_("C_ix_b", "÷ paso", "MULTIPLY",
                             mat_("C_ix_a", "x + mitad de la grilla", "ADD", xyz.outputs["X"], tam_x / 2), 1 / paso_x)), sep), 0.5)
    fy = mat_("C_fy", "Fila Y es campana", "LESS_THAN",
              mat_("C_iy_m", "Índice Y mod separación", "FLOORED_MODULO",
                   mat_("C_iy", "Índice Y (entero)", "ROUND",
                        mat_("C_iy_b", "÷ paso", "MULTIPLY",
                             mat_("C_iy_a", "y + mitad de la grilla", "ADD", xyz.outputs["Y"], tam_y / 2), 1 / paso_y)), sep), 0.5)
    flag = mat_("C_flag", "ES CAMPANA (1 / 0)", "MULTIPLY", fx, fy)
    # factor de tamaño = 1 + campana * (tamaño - 1)
    f_tam = mat_("C_tam", "Factor de tamaño", "ADD",
                 mat_("C_t2", "campana × (tamaño − 1)", "MULTIPLY", flag,
                      mat_("C_t1", "tamaño − 1", "SUBTRACT", ent.outputs["Tamaño de campana"], 1.0)), 1.0)
    diam = mat_("C_diam", "Diámetro efectivo", "MULTIPLY", ent.outputs["Diámetro de esfera"], f_tam)
    # factor de brillo = 1 + campana * (brillo - 1), aplicado al destello (1 − edad)²
    f_bri = mat_("C_bri", "Factor de brillo", "ADD",
                 mat_("C_b2", "campana × (brillo − 1)", "MULTIPLY", flag,
                      mat_("C_b1", "brillo − 1", "SUBTRACT", ent.outputs["Brillo de campana"], 1.0)), 1.0)
    cuad = etiqueta["(1 − edad)²  = destello"].outputs[0]
    brillo = mat_("C_g", "Destello × brillo", "MULTIPLY", cuad, f_bri)

    def reemplazar(sock, origen):
        for l in list(sock.links):
            g.links.remove(l)
        L(origen, sock)

    reemplazar(etiqueta["× Diámetro"].inputs[1], diam)          # el diámetro de cada esfera depende de si es campana
    reemplazar(N["P_radio"].inputs[0], diam)                    # y su punto de partida (apoyada en la punta) también
    reemplazar(etiqueta["Guardar g (destello)"].inputs["Value"], brillo)

    # el nodo de entrada local solo muestra lo que usa; y los demás, tras perder un enlace, vuelven a ocultar lo que sobra
    for n in N:
        if n.type == "GROUP_INPUT":
            for s in n.outputs:
                s.hide = not s.is_linked
    print("Campanas agregadas: %d nodos, %d enlaces | separación %d, tamaño x%.1f, brillo x%.1f"
          % (len(N), len(g.links), CAMPANA_PASO, CAMPANA_TAMANO, CAMPANA_BRILLO))


agregar()
