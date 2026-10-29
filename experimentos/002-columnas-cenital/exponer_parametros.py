"""Experimento 002: expone parámetros en el panel del modificador (nodo "Group Input").

Así se pueden cambiar sin abrir Geometry Nodes (y animar con drivers o fotogramas clave). Los valores por
defecto son los que ya tenía el grafo, por lo que el resultado no cambia.

Se exponen solo parámetros SEGUROS. Quedan fuera, a propósito:
  - Amplitud / altura mínima: el material mapea altura a color con números fijos (Map Range del material) y
    la esfera calcula su punto de partida con ellos; cambiarlos desde aquí descuadraría el color.
  - Colores e intensidad del destello: viven en el material, no en los nodos de geometría.

Bucle: la fase usa el FOTOGRAMA (no los segundos). Con "Frames por ciclo" = N la onda repite cada N fotogramas;
para un bucle sin corte, el rango de la animación debe ser N (o un múltiplo).

Uso con el archivo abierto:
  exec(open("experimentos/002-columnas-cenital/exponer_parametros.py", encoding="utf-8").read())
Es idempotente: si "Frames por ciclo" ya existe, no hace nada.
Depende de los nombres de nodo de make_002.py y de las etiquetas de anadir_esferas.py.
"""
import math
import bpy

g = bpy.data.node_groups["Columnas_cenital"]
N, L = g.nodes, g.links.new
TAU = 2 * math.pi


def exponer():
    if any(i.name == "Frames por ciclo" for i in g.interface.items_tree):
        print("Los parámetros ya están expuestos: no se hace nada.")
        return
    gi = N["Group Input"]
    etiqueta = {n.label: n for n in N if n.label}

    # (panel, nombre, tipo, por defecto, mínimo, máximo, es_distancia, descripción)
    P = [
        ("Onda", "Frames por ciclo", "NodeSocketInt", 100, 10, 1000, False,
         "Duración de un ciclo de la onda. Para un bucle sin corte, el rango de la animación debe ser este valor o un múltiplo."),
        ("Onda", "Longitud de onda", "NodeSocketFloat", 3.2, 0.5, 20.0, True, "Distancia entre crestas."),
        ("Onda", "Deformación", "NodeSocketFloat", 0.6, 0.0, 3.0, False,
         "Cuánto se tuerce la onda. 0 = anillos perfectos."),
        ("Onda", "Centro X", "NodeSocketFloat", 0.0, -10.0, 10.0, True, "Posición X del origen de la onda."),
        ("Onda", "Centro Y", "NodeSocketFloat", 0.5, -10.0, 10.0, True, "Posición Y del origen de la onda."),
        ("Destello", "Apagado del destello", "NodeSocketFloat", 8.0, 0.0, 30.0, False,
         "Mayor = el destello de la columna se apaga más rápido al caer."),
        ("Columnas", "Ancho de columna", "NodeSocketFloat", 0.34, 0.05, 0.39, True,
         "Lado de cada columna. La separación entre columnas es 0.4 m."),
        ("Esferas", "Vida de la esfera", "NodeSocketFloat", 0.55, 0.05, 0.95, False,
         "Fracción del ciclo que vive cada esfera. Debe ser menor que 1 para que no haya dos en la misma columna."),
        ("Esferas", "Altura de ascenso", "NodeSocketFloat", 2.5, 0.0, 10.0, True, "Metros que sube desde la punta de la columna."),
        ("Esferas", "Diámetro de esfera", "NodeSocketFloat", 0.26, 0.02, 0.6, True, "Diámetro máximo de la esfera."),
        ("Esferas", "Inicio del encogimiento", "NodeSocketFloat", 0.15, 0.0, 0.95, False,
         "Fracción de su vida a partir de la cual empieza a achicarse hasta desaparecer."),
    ]
    paneles = {}
    for panel, nombre, tipo, defecto, mn, mx, distancia, desc in P:
        if panel not in paneles:
            paneles[panel] = g.interface.new_panel(panel)
        s = g.interface.new_socket(nombre, in_out="INPUT", socket_type=tipo, parent=paneles[panel])
        s.default_value, s.min_value, s.max_value, s.description = defecto, mn, mx, desc
        if distancia:
            try:
                s.subtype = "DISTANCE"
            except (TypeError, AttributeError):
                pass
    # Los modificadores que ya existen inicializan los sockets nuevos en 0 (no en su valor por defecto):
    # hay que copiar el valor por defecto a cada modificador que use este grupo.
    for o in bpy.data.objects:
        for m in o.modifiers:
            if m.type == "NODES" and m.node_group == g:
                m.node_group = None      # sin reasignar el grupo, 5.2 sigue evaluando con los valores en 0
                m.node_group = g
                for i in g.interface.items_tree:
                    if i.item_type == "SOCKET" and i.in_out == "INPUT" and hasattr(i, "default_value"):
                        getattr(m.properties.inputs, i.identifier).value = i.default_value
                o.update_tag()
    ent = lambda nombre: gi.outputs[nombre]

    def mat_(nombre, etq, op, a, b):
        n = N.new("ShaderNodeMath")
        n.name, n.label, n.operation = nombre, etq, op
        for i, v in enumerate((a, b)):
            if hasattr(v, "node"):
                L(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n

    def reemplazar(sock, origen):
        for l in list(sock.links):
            g.links.remove(l)
        L(origen, sock)

    # Onda: fase = fotograma * 2π/N - distancia * 2π/λ + deformación
    t = next(n for n in N if n.type == "INPUT_SCENE_TIME")
    omega = mat_("P_omega", "2π ÷ frames por ciclo", "DIVIDE", TAU, ent("Frames por ciclo"))
    reemplazar(N["Math.012"].inputs[0], t.outputs["Frame"])
    reemplazar(N["Math.012"].inputs[1], omega.outputs[0])
    N["Math.012"].label = "Fotograma × 2π / frames por ciclo"
    k = mat_("P_K", "2π ÷ longitud de onda", "DIVIDE", TAU, ent("Longitud de onda"))
    reemplazar(N["Math.013"].inputs[1], k.outputs[0])
    reemplazar(N["Math.011"].inputs[1], ent("Deformación"))
    reemplazar(N["Math"].inputs[1], ent("Centro X"))
    reemplazar(N["Math.001"].inputs[1], ent("Centro Y"))
    # Destello
    decay = mat_("P_decay", "− apagado", "MULTIPLY", ent("Apagado del destello"), -1.0)
    reemplazar(N["Math.023"].inputs[1], decay.outputs[0])
    # Columnas
    for eje in ("X", "Y"):
        reemplazar(N["Combine XYZ"].inputs[eje], ent("Ancho de columna"))
    # Esferas
    reemplazar(etiqueta["Edad (0 = nace en el pico, 1 = muere)"].inputs[1], ent("Vida de la esfera"))
    reemplazar(etiqueta["× Altura de ascenso"].inputs[1], ent("Altura de ascenso"))
    reemplazar(etiqueta["× Diámetro"].inputs[1], ent("Diámetro de esfera"))
    reemplazar(etiqueta["Se encoge al morir"].inputs["From Min"], ent("Inicio del encogimiento"))
    # La esfera nace apoyada en la punta de la columna: punta + radio (el radio depende del diámetro)
    amp = 2 * N["Math.018"].inputs[1].default_value
    h_max = N["Math.019"].inputs[1].default_value + amp
    local = N["Translate Instances"].inputs["Local Space"].default_value
    punta = h_max * (h_max + 1) / 2 if local else h_max
    radio = mat_("P_radio", "Diámetro ÷ 2", "MULTIPLY", ent("Diámetro de esfera"), 0.5)
    z0 = mat_("P_z0", "Punta de la columna + radio", "ADD", radio.outputs[0], punta)
    reemplazar(etiqueta["+ punta de la columna"].inputs[1], z0.outputs[0])
    gi.label = "Parámetros (entrada del modificador)"
    print("Parámetros expuestos: %d sockets, %d nodos, %d enlaces" % (len(P), len(N), len(g.links)))


exponer()
