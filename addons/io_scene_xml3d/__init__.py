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
    "blender": (2, 71, 0),
    "location": "File > Export",
    "description": "Export XML3D, meshes, uvs, materials, textures, "
                   "cameras & lamps",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"
}

# if "bpy" in locals():
#     import imp
#     if "export_xml3d" in locals():
#         imp.reload(export_xml3d)


import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy_extras.io_utils import ExportHelper


class ExportXML3D(bpy.types.Operator, ExportHelper):
    """Export to XML3D (.xml3d)"""
    bl_idname = "export_scene.xml3d"
    bl_label = 'Export XML3D'

    filename_ext = ".html"
    filter_glob = StringProperty(
        default="*.html",
        options={'HIDDEN'},
    )

    # TODO: Feature: Export selected objects only
    # use_selection = BoolProperty(
    #     name="Selection Only",
    #     description="Export selected objects only",
    #     default=False,
    # )

    template_selection = EnumProperty(
        name="Template",
        items=(('html', "Simple HTML", ""),
               ('xml3d', "XML3D only", ""),
               ('preview', "Blender Preview", ""),
               ),
        default='preview',
    )

    xml3djs_selection = EnumProperty(
        name="xml3d.js",
        items=(('http://www.xml3d.org/xml3d/scripts/xml3d', "Latest Stable (online)", "Latest Stable from xml3d.org"),
               ('http://www.xml3d.org/xml3d/scripts/xml3d-dev', "Development (online)", "Development Snapshot from xml3d.org"),
               ('./common/scripts/xml3d/xml3d-4.8', "4.8", "Local version 4.8"),
               ('./common/scripts/xml3d/xml3d-4.9', "4.9", "Local version 4.9"),
               ),
        default='./common/scripts/xml3d/xml3d-4.9',
    )

    transform_representation = EnumProperty(
        name="Transforms",
        items=(('css', "CSS Combination", ""),
               ('css-matrix', "CSS Matrix", "")
               ),
        default='css-matrix',
    )

    xml3d_minimized = BoolProperty(
        name="Minimized",
        description="Uses minimized version of xml3d.js",
        default=True,
    )

    asset_cluster_strategy = EnumProperty(
        name="Asset clustering",
        items=(('none', "None", "Do not cluster assets."),
               ('layers', "Layer", "Cluster assets per layer."),
               ('bins', "Fixed", "Distribute assets over fixed number of files."),
               ),
        default='bins',
    )

    asset_cluster_bins_limit = IntProperty(
        name="Bin Limit",
        description="Limit number of asset files.",
        default=8,
        soft_min=1,
    )

    asset_material_selection = EnumProperty(
        name="Materials",
        items=(('include', "Include all", "Store all materials within asset."),
               ('external', "External", "Store materials in external library."),
               ('shared', "Shared", "Store single user materials in asset, shared materials in external library."),
               ('none', "None", "Do not save materials for assets."),
               ),
        default='external',
    )

    asset_export_armature = BoolProperty(
        name="Export armatures",
        description="Export armatures including animations. Exports static mesh otherwise.",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        template_box = layout.box()
        template_box.label("Template Options:", icon="FILE_SCRIPT")
        template_box.prop(self, "template_selection")
        template_box.prop(self, "xml3djs_selection")

        row = template_box.row()
        row.alignment = "RIGHT"
        row.prop(self, "xml3d_minimized")

        asset_box = layout.box()
        asset_box.label("Asset Options:", icon="OBJECT_DATA")

        row = asset_box.row()
        row.label("Clustering:")
        row.operator("wm.url_open", text="", icon="QUESTION").url = "https://github.com/ksons/xml3d-blender-exporter/wiki/Exporter-Options#asset-clustering"

        row = asset_box.row()
        row.prop(self, "asset_cluster_strategy", expand=True)

        if self.asset_cluster_strategy == "bins":
            row = asset_box.row()
            row.prop(self, "asset_cluster_bins_limit")

        asset_box.separator()

        asset_box.prop(self, "asset_material_selection")
        asset_box.prop(self, "asset_export_armature")

        scene_box = layout.box()
        scene_box.label("Scene Options:", icon="SCENE_DATA")
        scene_box.prop(self, "transform_representation")

    def execute(self, context):
        from . import export_xml3d

        keywords = self.as_keywords(ignore=("filter_glob",
                                            "check_existing",
                                            ))
        # global_matrix = axis_conversion(to_forward=self.axis_forward,
        #                                 to_up=self.axis_up,
        #                                 ).to_4x4()
        # keywords["global_matrix"] = global_matrix
        return export_xml3d.save(self, context, keywords)


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
