import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] # get all args after "--"

obj_out = argv[0]

bpy.ops.export_scene.xml3d(filepath=obj_out)