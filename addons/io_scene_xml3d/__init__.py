# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

bl_info = {
    "name": "XML3D Exporter",
    "author": "Kristian Sons",
    "blender": (2, 7, 0),
    "location": "File > Import-Export",
    "description": "Export XML3D, meshes, uvs, materials, textures, "
                   "cameras & lamps",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    if "export_xml3d" in locals():
        imp.reload(export_xml3d)


import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty

from bpy_extras.io_utils import (ExportHelper,
                                 axis_conversion,
                                 )



class ExportXML3D(bpy.types.Operator, ExportHelper):
    """Export to XML3D (.xml3d)"""
    bl_idname = "export_scene.xml3d"
    bl_label = 'Export XML3D'

    filename_ext = ".html"
    filter_glob = StringProperty(
            default="*.html",
            options={'HIDDEN'},
            )

    use_selection = BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )

    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='Y',
            )

    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Z',
            )

    def execute(self, context):
        from . import export_xml3d

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
        global_matrix = axis_conversion(to_forward=self.axis_forward,
                                        to_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return export_xml3d.save(self, context, **keywords)


# Add to a menu
def menu_func_export(self, context):
    self.layout.operator(ExportXML3D.bl_idname, text="XML3D (.html)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
