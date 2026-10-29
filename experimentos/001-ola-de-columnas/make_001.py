"""Experimento 001: ola de columnas con Geometry Nodes (instancias), en bucle de 4 s.

Uso: blender -b base/gramaphenia-base.blend -P experimentos/001-ola-de-columnas/make_001.py -- experimentos/001-ola-de-columnas/001.blend

Receta de nodos:
  Grid (puntos) -> Instance on Points (cubo) con escala Z = altura de la ola
  -> Translate Instances (sube media altura) -> Store Named Attribute "h" -> Set Material
  altura = 0.25 + (sin(distancia * 1.2 - 2*pi*segundos/4) + 1) / 2 * 2.2
El material lee el atributo "h" (Attribute, tipo Instancer) y lo pasa por un ColorRamp.
"""
import sys
import math
import bpy

out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 96  # 4 s a 24 fps: bucle sin corte

PERIODO_S = 4.0
FREQ = 1.2        # cuántas ondas por metro de distancia
H_MIN, H_RANGO = 0.25, 2.2
PASO = 0.5        # separación entre columnas (m)
ANCHO_COL = 0.42

# --- Material (paleta PROVISIONAL, la define el autor) ---
mat = bpy.data.materials.new("Columna_mat")
if mat.node_tree is None:
    mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.55
attr = nt.nodes.new("ShaderNodeAttribute")
attr.attribute_type = "INSTANCER"
attr.attribute_name = "h"
norm = nt.nodes.new("ShaderNodeMapRange")
norm.inputs["From Min"].default_value = H_MIN
norm.inputs["From Max"].default_value = H_MIN + H_RANGO
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.22, 0.30, 0.55, 1)
ramp.color_ramp.elements[1].color = (1.0, 0.62, 0.40, 1)
nt.links.new(attr.outputs["Fac"], norm.inputs["Value"])
nt.links.new(norm.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

# --- Nodos de geometría ---
tree = bpy.data.node_groups.new("Ola_de_columnas", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = tree.nodes
L = tree.links.new

def node(kind, x, y):
    n = N.new(kind)
    n.location = (x, y)
    return n

gin = node("NodeGroupInput", -1400, 0)
gout = node("NodeGroupOutput", 1400, 0)

grid = node("GeometryNodeMeshGrid", -1200, 200)
grid.inputs["Size X"].default_value = 5.0
grid.inputs["Size Y"].default_value = 14.0
grid.inputs["Vertices X"].default_value = int(5.0 / PASO) + 1
grid.inputs["Vertices Y"].default_value = int(14.0 / PASO) + 1

# altura de la ola
pos = node("GeometryNodeInputPosition", -1200, -200)
dist = node("ShaderNodeVectorMath", -1000, -200)
dist.operation = "LENGTH"
L(pos.outputs["Position"], dist.inputs[0])
k = node("ShaderNodeMath", -800, -200)          # distancia * FREQ
k.operation = "MULTIPLY"
k.inputs[1].default_value = FREQ
L(dist.outputs["Value"], k.inputs[0])
time = node("GeometryNodeInputSceneTime", -1000, -450)
fase_t = node("ShaderNodeMath", -800, -450)     # segundos * 2pi/periodo
fase_t.operation = "MULTIPLY"
fase_t.inputs[1].default_value = 2 * math.pi / PERIODO_S
L(time.outputs["Seconds"], fase_t.inputs[0])
fase = node("ShaderNodeMath", -600, -300)
fase.operation = "SUBTRACT"
L(k.outputs["Value"], fase.inputs[0])
L(fase_t.outputs["Value"], fase.inputs[1])
seno = node("ShaderNodeMath", -400, -300)
seno.operation = "SINE"
L(fase.outputs["Value"], seno.inputs[0])
mas1 = node("ShaderNodeMath", -200, -300)       # (seno + 1) / 2
mas1.operation = "ADD"
mas1.inputs[1].default_value = 1.0
L(seno.outputs["Value"], mas1.inputs[0])
mitad = node("ShaderNodeMath", 0, -300)
mitad.operation = "MULTIPLY"
mitad.inputs[1].default_value = 0.5 * H_RANGO
L(mas1.outputs["Value"], mitad.inputs[0])
altura = node("ShaderNodeMath", 200, -300)
altura.operation = "ADD"
altura.inputs[1].default_value = H_MIN
L(mitad.outputs["Value"], altura.inputs[0])

escala = node("ShaderNodeCombineXYZ", 400, -300)
escala.inputs["X"].default_value = ANCHO_COL
escala.inputs["Y"].default_value = ANCHO_COL
L(altura.outputs["Value"], escala.inputs["Z"])
medio = node("ShaderNodeMath", 400, -500)       # sube media altura
medio.operation = "MULTIPLY"
medio.inputs[1].default_value = 0.5
L(altura.outputs["Value"], medio.inputs[0])
sube = node("ShaderNodeCombineXYZ", 600, -500)
L(medio.outputs["Value"], sube.inputs["Z"])

cubo = node("GeometryNodeMeshCube", -1000, 450)
cubo.inputs["Size"].default_value = (1.0, 1.0, 1.0)
set_mat = node("GeometryNodeSetMaterial", -800, 450)
set_mat.inputs["Material"].default_value = mat
L(cubo.outputs["Mesh"], set_mat.inputs["Geometry"])

inst = node("GeometryNodeInstanceOnPoints", 600, 200)
L(grid.outputs["Mesh"], inst.inputs["Points"])
L(set_mat.outputs["Geometry"], inst.inputs["Instance"])
L(escala.outputs["Vector"], inst.inputs["Scale"])

trans = node("GeometryNodeTranslateInstances", 850, 200)
L(inst.outputs["Instances"], trans.inputs["Instances"])
L(sube.outputs["Vector"], trans.inputs["Translation"])

store = node("GeometryNodeStoreNamedAttribute", 1100, 200)
store.data_type = "FLOAT"
store.domain = "INSTANCE"
store.inputs["Name"].default_value = "h"
L(trans.outputs["Instances"], store.inputs["Geometry"])
L(altura.outputs["Value"], store.inputs["Value"])
L(store.outputs["Geometry"], gout.inputs["Geometry"])

# Cámara y luz propias de este experimento: vista elevada sobre la ola
from mathutils import Vector
cam = scene.camera
cam.data.lens = 24  # más abierta: con ajuste vertical el sensor es de 24 mm de alto
cam.location = (0, -10, 9)
cam.rotation_euler = (Vector((0, 1.5, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
# Valores absolutos (no relativos a la base) para que la receta dé siempre la misma imagen
scene.objects["Luz_principal"].data.energy = 450
scene.objects["Luz_contra"].data.energy = 240
bg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1)

# Objeto portador del modificador
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Ola"
mod = obj.modifiers.new("Ola_de_columnas", "NODES")
mod.node_group = tree

bpy.ops.wm.save_as_mainfile(filepath=out)
print("Guardado:", out)
