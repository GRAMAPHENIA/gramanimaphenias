"""Prueba del pipeline: cubo que gira y rebota sobre la escena base.
Uso: blender -b base/gramaphenia-base.blend -P experimentos/000-prueba-cubo/make_cubo.py -- experimentos/000-prueba-cubo/cubo.blend
"""
import sys, math
import bpy

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0.75))
cube = bpy.context.active_object
cube.name = "Cubo"
mat = bpy.data.materials.new("Cubo_mat")
if mat.node_tree is None:
    mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (0.9, 0.35, 0.2, 1)
cube.data.materials.append(mat)

for f, z, rot in ((1, 0.75, 0), (12, 2.5, 90), (24, 0.75, 180)):
    cube.location.z = z
    cube.rotation_euler.z = math.radians(rot)
    cube.keyframe_insert("location", index=2, frame=f)
    cube.keyframe_insert("rotation_euler", index=2, frame=f)
bpy.context.scene.frame_end = 24
bpy.ops.wm.save_as_mainfile(filepath=out)
