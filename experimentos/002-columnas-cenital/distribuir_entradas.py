"""Experimento 002: reparte el nodo de entrada del grupo en uno por marco, para que los cables sean cortos.

Un solo "Group Input" con 11 parámetros obliga a cruzar el lienzo con cables largos. Blender permite varios
nodos de entrada del grupo: aquí se crea uno dentro de cada marco que usa parámetros, mostrando solo los
sockets que ese marco necesita (los demás se ocultan). Los parámetros siguen siendo los mismos y aparecen
igual en el panel del modificador.

Solo cambia nodos y cables de entrada; los valores y el resultado no cambian.
Se ejecuta DESPUÉS de exponer_parametros.py y ANTES de ordenar_nodos.py (que coloca cada entrada en su marco):
  exec(open("experimentos/002-columnas-cenital/distribuir_entradas.py", encoding="utf-8").read())
Es idempotente: solo reparte un Group Input cuyos destinos estén en más de un marco.
"""
import bpy

g = bpy.data.node_groups["Columnas_cenital"]
N = g.nodes


def marco_de(n):
    return n.parent.name if n.parent else None


def distribuir():
    creados = 0
    for original in [n for n in N if n.type == "GROUP_INPUT"]:
        # (socket de salida, socket de destino) de cada cable
        cables = [(s, l.to_socket) for s in original.outputs for l in s.links]
        marcos = {marco_de(d.node) for _, d in cables}
        if len(marcos) < 2:
            continue                      # ya es local (o no se usa): nada que repartir
        por_marco = {}
        for s, destino in cables:
            por_marco.setdefault(marco_de(destino.node), []).append((s, destino))
        for nombre_marco, lista in por_marco.items():
            nuevo = N.new("NodeGroupInput")
            nuevo.name = "Entrada " + (nombre_marco or "sin marco")
            nuevo.label = "Parámetros"
            if nombre_marco:
                nuevo.parent = N[nombre_marco]
            nuevo.location_absolute = lista[0][1].node.location_absolute
            for s, destino in lista:
                g.links.new(nuevo.outputs[s.name], destino)
            for s in nuevo.outputs:        # mostrar solo los sockets que este marco usa
                if not s.is_linked:
                    s.hide = True
            creados += 1
        N.remove(original)
    print("Entradas repartidas: %d nodos de entrada | enlaces %d" % (creados, len(g.links)))


distribuir()
