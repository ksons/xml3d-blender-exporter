import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] # get all args after "--"

obj_out = argv[0]

if not bpy.ops.export_scene.xml3d:
    sys.exit("XML3D Exporter script is not registered.")

bpy.ops.export_scene.xml3d(filepath=obj_out)