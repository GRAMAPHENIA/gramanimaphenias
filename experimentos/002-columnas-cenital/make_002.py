"""Experimento 002: columnas vistas desde arriba; cada una destella al llegar al pico y se apaga al caer.

Uso: blender -b base/gramaphenia-base.blend -P experimentos/002-columnas-cenital/make_002.py -- experimentos/002-columnas-cenital/002.blend

Idea central: la altura sigue una onda con fase  p = w*t - K*distancia + deformacion(x, y).
  altura = H_MIN + (sin(p) + 1)/2 * AMP
  El pico ocurre en p = pi/2. Con  ciclo = fract((p - pi/2)/(2*pi))  (0 = recién en el pico):
  brillo = max( exp(-DECAY * ciclo),  subida corta justo antes del pico )
  -> la columna se enciende al llegar arriba y se apaga mientras baja.
La deformación depende solo de (x, y): el bucle de T_BUCLE segundos cierra sin corte.
"""
import sys
import math
import bpy

out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene

# --- Parámetros (cambiar aquí para variar el resultado) ---
T_ONDA = 2.0               # segundos por ciclo de la onda
T_BUCLE = 6.0              # debe ser múltiplo de T_ONDA
PASO = 0.4                 # separación entre columnas (m)
ANCHO = 0.34               # lado de cada columna (deja un hueco oscuro de 0.06 m)
GRID_X, GRID_Y = 7.2, 12.4
LONG_ONDA = 3.2            # m entre crestas
AMP, H_MIN = 2.0, 0.15
DEFORM = 0.6               # cuánto se tuerce la onda (0 = anillos perfectos)
CENTRO = (0.0, 0.5)
DECAY = 8.0                # más alto = el destello se apaga más rápido
EMISION = 1.7              # intensidad del destello
COLOR_BAJO, COLOR_ALTO = (0.015, 0.02, 0.04, 1), (0.08, 0.11, 0.18, 1)   # PROVISIONAL
COLOR_DESTELLO = (1.0, 0.38, 0.10, 1)                                      # PROVISIONAL

# 100 fotogramas = un ciclo de la onda (parámetro "Frames por ciclo" de exponer_parametros.py, también 100)
scene.frame_start, scene.frame_end = 1, 100
K = 2 * math.pi / LONG_ONDA
W = 2 * math.pi / T_ONDA

# --- Limpiar lo que no se usa de la base: suelo y luces de área ---
for o in list(scene.objects):
    if o.name == "Suelo" or o.type == "LIGHT":
        bpy.data.objects.remove(o, do_unlink=True)

sol_data = bpy.data.lights.new("Sol", "SUN")
sol_data.energy = 1.6
sol_data.angle = math.radians(2)
sol_data.use_shadow = False   # las sombras entre columnas vecinas dejaban manchas que parpadean
sol = bpy.data.objects.new("Sol", sol_data)
sol.rotation_euler = (math.radians(20), math.radians(-15), 0)
scene.collection.objects.link(sol)

bg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0, 0, 0, 1)

# --- Cámara: la "D" que eligió el autor (acimut 113°, elevación 46°, llena el 60 % del alto del cuadro vertical).
# Antes: cenital en (0, 0.5, 14); luego diagonal en (-27.69, 20.61, 24.58), que llenaba solo el 44 % del alto. ---
cam = scene.camera
cam.data.lens = 35
cam.location = (-9.45378, 23.21843, 27.98142)
cam.rotation_euler = (0.766954, 0.0, -2.734384)

# --- Compositor: sin resplandor ni grano en este experimento ---
tree_c = scene.compositing_node_group
if tree_c:
    for n in tree_c.nodes:
        if n.type == "GLARE":
            n.inputs["Strength"].default_value = 0.0
        if n.type == "MIX" and getattr(n, "blend_type", "") == "LINEAR_LIGHT":
            n.inputs["Factor"].default_value = 0.0

# --- Material: el color base sube con la altura (h), el destello (g) va a la emisión ---
mat = bpy.data.materials.new("Columna_mat")
if mat.node_tree is None:
    mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.6
bsdf.inputs["Emission Color"].default_value = COLOR_DESTELLO

attr_h = nt.nodes.new("ShaderNodeAttribute")
attr_h.attribute_type = "INSTANCER"
attr_h.attribute_name = "h"
rango = nt.nodes.new("ShaderNodeMapRange")
rango.inputs["From Min"].default_value = H_MIN
rango.inputs["From Max"].default_value = H_MIN + AMP
rampa = nt.nodes.new("ShaderNodeValToRGB")
rampa.color_ramp.elements[0].color = COLOR_BAJO
rampa.color_ramp.elements[1].color = COLOR_ALTO
nt.links.new(attr_h.outputs["Fac"], rango.inputs["Value"])
nt.links.new(rango.outputs["Result"], rampa.inputs["Fac"])
nt.links.new(rampa.outputs["Color"], bsdf.inputs["Base Color"])

attr_g = nt.nodes.new("ShaderNodeAttribute")
attr_g.attribute_type = "INSTANCER"
attr_g.attribute_name = "g"
fuerza = nt.nodes.new("ShaderNodeMath")
fuerza.operation = "MULTIPLY"
fuerza.inputs[1].default_value = EMISION
nt.links.new(attr_g.outputs["Fac"], fuerza.inputs[0])
nt.links.new(fuerza.outputs["Value"], bsdf.inputs["Emission Strength"])

# --- Nodos de geometría ---
tree = bpy.data.node_groups.new("Columnas_cenital", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = tree.nodes, tree.links.new
_x = [-1500]


def nodo(kind, y=0):
    n = N.new(kind)
    _x[0] += 180
    n.location = (_x[0], y)
    return n


def conectar(sock, valor):
    if hasattr(valor, "node"):
        L(valor, sock)
    else:
        sock.default_value = valor


def mat_(op, a, b=None, c=None):
    n = nodo("ShaderNodeMath", y=-300)
    n.operation = op
    conectar(n.inputs[0], a)
    if b is not None:
        conectar(n.inputs[1], b)
    if c is not None:
        conectar(n.inputs[2], c)
    return n.outputs["Value"]


pos = nodo("GeometryNodeInputPosition", y=-100)
xyz = nodo("ShaderNodeSeparateXYZ", y=-100)
L(pos.outputs["Position"], xyz.inputs["Vector"])
x, y = xyz.outputs["X"], xyz.outputs["Y"]

dx = mat_("SUBTRACT", x, CENTRO[0])
dy = mat_("SUBTRACT", y, CENTRO[1])
dist = mat_("SQRT", mat_("ADD", mat_("MULTIPLY", dx, dx), mat_("MULTIPLY", dy, dy)))
deform = mat_("MULTIPLY", mat_("ADD", mat_("SINE", mat_("MULTIPLY", x, 1.1)),
                               mat_("SINE", mat_("MULTIPLY", y, 0.9))), DEFORM)

tiempo = nodo("GeometryNodeInputSceneTime", y=-600)
fase = mat_("ADD", mat_("SUBTRACT", mat_("MULTIPLY", tiempo.outputs["Seconds"], W),
                         mat_("MULTIPLY", dist, K)), deform)

altura = mat_("ADD", mat_("MULTIPLY", mat_("ADD", mat_("SINE", fase), 1.0), 0.5 * AMP), H_MIN)

ciclo = mat_("FRACT", mat_("DIVIDE", mat_("SUBTRACT", fase, math.pi / 2), 2 * math.pi))
caida = mat_("EXPONENT", mat_("MULTIPLY", ciclo, -DECAY))
subida = nodo("ShaderNodeMapRange", y=-700)
subida.interpolation_type = "SMOOTHSTEP"
subida.clamp = True
conectar(subida.inputs["Value"], ciclo)
subida.inputs["From Min"].default_value = 0.88
subida.inputs["From Max"].default_value = 1.0
brillo = mat_("MAXIMUM", caida, subida.outputs["Result"])

grid = nodo("GeometryNodeMeshGrid", y=300)
grid.inputs["Size X"].default_value = GRID_X
grid.inputs["Size Y"].default_value = GRID_Y
grid.inputs["Vertices X"].default_value = round(GRID_X / PASO) + 1
grid.inputs["Vertices Y"].default_value = round(GRID_Y / PASO) + 1

cubo = nodo("GeometryNodeMeshCube", y=500)
cubo.inputs["Size"].default_value = (1.0, 1.0, 1.0)
set_mat = nodo("GeometryNodeSetMaterial", y=500)
set_mat.inputs["Material"].default_value = mat
L(cubo.outputs["Mesh"], set_mat.inputs["Geometry"])

escala = nodo("ShaderNodeCombineXYZ", y=-100)
escala.inputs["X"].default_value = ANCHO
escala.inputs["Y"].default_value = ANCHO
L(altura, escala.inputs["Z"])
sube = nodo("ShaderNodeCombineXYZ", y=-200)
L(mat_("MULTIPLY", altura, 0.5), sube.inputs["Z"])

inst = nodo("GeometryNodeInstanceOnPoints", y=300)
L(grid.outputs["Mesh"], inst.inputs["Points"])
L(set_mat.outputs["Geometry"], inst.inputs["Instance"])
L(escala.outputs["Vector"], inst.inputs["Scale"])
trans = nodo("GeometryNodeTranslateInstances", y=300)
L(inst.outputs["Instances"], trans.inputs["Instances"])
L(sube.outputs["Vector"], trans.inputs["Translation"])


def guardar(geo, nombre, valor):
    s = nodo("GeometryNodeStoreNamedAttribute", y=300)
    s.data_type = "FLOAT"
    s.domain = "INSTANCE"
    s.inputs["Name"].default_value = nombre
    L(geo, s.inputs["Geometry"])
    L(valor, s.inputs["Value"])
    return s.outputs["Geometry"]


geo = guardar(trans.outputs["Instances"], "h", altura)
geo = guardar(geo, "g", brillo)

N.new("NodeGroupInput")
gout = N.new("NodeGroupOutput")
gout.location = (_x[0] + 250, 300)
L(geo, gout.inputs["Geometry"])

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Columnas"
obj.modifiers.new("Columnas_cenital", "NODES").node_group = tree

bpy.ops.wm.save_as_mainfile(filepath=out)
print("Guardado:", out, "| instancias esperadas:",
      (round(GRID_X / PASO) + 1) * (round(GRID_Y / PASO) + 1))
