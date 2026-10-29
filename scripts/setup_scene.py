"""Construye la escena base del lab desde cero (sin depender de un .blend).

Uso:  blender -b --factory-startup -P scripts/setup_scene.py -- base/gramaphenia-base.blend
"""
import sys
import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "gramaphenia-base"

# Formato: vertical 1080x1920, 24 fps
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 24
scene.frame_start, scene.frame_end = 1, 96  # 4 s
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"
r.film_transparent = False

# Motor: EEVEE (leer el id válido, no fijarlo a ciegas)
engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
r.engine = next(e for e in engines if "EEVEE" in e)

ev = scene.eevee
for name, value in (("taa_render_samples", 64), ("taa_samples", 16),
                    ("use_raytracing", False), ("use_gtao", False)):
    if hasattr(ev, name):
        setattr(ev, name, value)

# Gestión de color: AgX si existe
try:
    scene.view_settings.view_transform = "AgX"
except TypeError:
    pass

# Mundo neutro
world = bpy.data.worlds.new("Mundo")
if world.node_tree is None:  # use_nodes quedará obsoleto en Blender 6.0
    world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# Cámara vertical, mirando al origen
cam_data = bpy.data.cameras.new("Camara")
cam_data.lens = 50
cam_data.sensor_fit = "VERTICAL"
cam = bpy.data.objects.new("Camara", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -13, 3.2)
target = Vector((0, 0, 1.6))  # punto al que mira la cámara
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# Luces: principal + contraluz suave
def add_light(name, kind, loc, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.location = loc
    scene.collection.objects.link(o)
    return o

add_light("Luz_principal", "AREA", (3, -4, 5), 150).data.size = 3
add_light("Luz_contra", "AREA", (-3, 3, 4), 80).data.size = 2

# Suelo neutro
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
suelo = bpy.context.active_object
suelo.name = "Suelo"
mat = bpy.data.materials.new("Suelo_mat")
mat.diffuse_color = (0.12, 0.12, 0.14, 1)
if mat.node_tree is None:
    mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.14, 1)
bsdf.inputs["Roughness"].default_value = 0.8
suelo.data.materials.append(mat)

# Compositor (Blender 5.x: grupo de nodos en scene.compositing_node_group)
# Capa de render -> glare (resplandor suave) -> viñeta -> salida
def build_compositor():
    tree = bpy.data.node_groups.new("Compositor_base", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n = tree.nodes
    rl = n.new("CompositorNodeRLayers")
    glare = n.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Strength"].default_value = 0.4
    mask = n.new("CompositorNodeEllipseMask")
    mask.width, mask.height = 0.9, 0.95
    blur = n.new("CompositorNodeBlur")
    blur.inputs["Size"].default_value = (120.0, 120.0)
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.6
    out_node = n.new("NodeGroupOutput")
    l = tree.links.new
    l(rl.outputs["Image"], glare.inputs["Image"])
    l(mask.outputs[0], blur.inputs["Image"])
    l(glare.outputs[0], mix.inputs["A"])
    l(blur.outputs[0], mix.inputs["B"])
    l(mix.outputs["Result"], out_node.inputs["Image"])
    scene.compositing_node_group = tree

try:
    build_compositor()
except Exception as exc:  # la API de nodos cambia entre versiones: avisar, no abortar
    print("AVISO compositor no creado:", repr(exc))

if out:
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("Guardado:", out)
