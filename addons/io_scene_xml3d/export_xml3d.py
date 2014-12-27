import os
import io
import re
import bpy
import math
import json
from . import xml_writer, export_asset, context
from bpy_extras.io_utils import create_derived_objects, free_derived_objects
from .tools import is_identity, is_identity_scale, is_identity_translate, matrix_to_ccs_matrix3d
from shutil import copytree

ASSETDIR = "assets"
LIGHTMODELMAP = {
    "POINT": ("point", "intensity = xflow.blenderPoint(color, energy)"),
    "SPOT": ("spot", "intensity = xflow.blenderSpot(color, energy)"),
    "SUN": ("directional", "intensity = xflow.blenderSun(color, energy)")
}


def gamma(color):
    return [pow(c, 1.0 / 2.2) * 255 for c in color]


def dump(obj):
    for attr in dir(obj):
        print("obj %s", attr)


def clamp_color(col):
    return tuple([max(min(c, 1.0), 0.0) for c in col])


def escape_html_id(_id):
    # HTML: ID tokens must begin with a letter ([A-Za-z])
    if not _id[:1].isalpha():
        _id = "a" + _id

    # and may be followed by any number of letters, digits ([0-9]),
    # hyphens ("-"), underscores ("_"), colons (":"), and periods (".")
    _id = re.sub('[^a-zA-Z0-9-_:\.]+', '-', _id)
    return _id


def blender_lamp_to_xml3d_light(model):
    if model in LIGHTMODELMAP:
        result = LIGHTMODELMAP[model]
        return result[0], result[1]
    return None, None


class XML3DExporter():
    context = context.Context()

    def __init__(self, context, dirname, transform, progress):
        self.blender_context = context
        self._output = io.StringIO()
        self._writer = xml_writer.XMLWriter(self._output, 0)
        self._resource = {}
        self._transform = transform
        self._object_progress = progress
        self.context.set_base_path(dirname)

    def create_asset_directory(self):
        assetDir = os.path.join(self.context.base_path, ASSETDIR)
        if not os.path.exists(assetDir):
            os.makedirs(assetDir)
        return assetDir

    def create_resource_from_mesh(self, original_object, derived_object):
        mesh_data_name = original_object.data.name
        path = self.create_asset_directory()
        path = os.path.join(path, mesh_data_name + ".xml")
        url = "%s/%s.xml" % (ASSETDIR, mesh_data_name)

        exporter = export_asset.AssetExporter(original_object.name, self.context, path, self.blender_context.scene)
        exporter.add_mesh(original_object, derived_object)
        exporter.save()

        # stats.assets[0]["url"] = url
        return url + "#root"

    def stats(self):
        return self.context.stats

    def warning(self, message, category=None, issue=None):
        self.context.warning(message, category, issue)

    def create_resource(self, obj, derived):
        url = ""

        if obj.type in {"MESH", "FONT", "SURFACE", "CURVE"}:
            mesh_data = obj.data
            key = "mesh." + mesh_data.name
            if key in self._resource:
                return self._resource[key]

            url = self.create_resource_from_mesh(obj, derived)
            self._resource[key] = url
        else:
            self.warning(u"Object '{0:s}' is of type '{1:s}', which is not (yet) supported.".format(obj.name, obj.type))

        return url

    def build_hierarchy(self, objects):
        """ returns parent child relationships, skipping
        """
        objects_set = set(objects)
        par_lookup = {}

        def test_parent(parent):
            while (parent is not None) and (parent not in objects_set):
                parent = parent.parent
            return parent

        for obj in objects:
            par_lookup.setdefault(
                test_parent(obj.parent), []).append((obj, []))

        for parent, children in par_lookup.items():
            for obj, subchildren in children:
                subchildren[:] = par_lookup.get(obj, [])

        return par_lookup.get(None, [])

    def write_id(self, obj, prefix=""):
        self._writer.attribute("id", escape_html_id(prefix + obj.name))

    def write_transformation(self, obj, derived_matrix):
        # try:
        matrix = obj.matrix_basis

        if self._transform == "cssl":
            matrices = []

            if not is_identity(obj.matrix_parent_inverse):
                matrices.append(
                    matrix_to_ccs_matrix3d(obj.matrix_parent_inverse))

            old_rotation_mode = obj.rotation_mode
            obj.rotation_mode = "AXIS_ANGLE"
            if not is_identity_translate(obj.location):
                matrices.append("translate3d(%.6f,%.6f,%.6f)" %
                                tuple(obj.location))
            rot = obj.rotation_axis_angle
            if rot[0] != 0.0:
                matrices.append("rotate3d(%.6f,%.6f,%.6f,%.2fdeg)" % (
                    rot[1], rot[2], rot[3], math.degrees(rot[0])))
            if not is_identity_scale(obj.scale):
                matrices.append("scale3d(%.6f,%.6f,%.6f)" % tuple(obj.scale))
            transform = " ".join(matrices)
            obj.rotation_mode = old_rotation_mode
        else:
            matrix = obj.matrix_parent_inverse * derived_matrix
            if is_identity(matrix):
                return
            transform = matrix_to_ccs_matrix3d(matrix)

        self._writer.attribute("style", "transform:" + transform + ";")

    def write_class(self, obj):
        layers = []
        for i in range(len(obj.layers)):
            if obj.layers[i] is True:
                layers.append("layer-%d" % i)
        class_name = " ".join(layers)
        self._writer.attribute("class", class_name)

    def write_defaults(self, obj, prefix=""):
        self.write_id(obj, prefix)
        self.write_class(obj)

    def create_camera(self, obj):
        self._writer.start_element("view")
        self.write_id(obj, "v_")
        self._writer.end_element("view")
        self.context.stats.views += 1

    def create_geometry(self, derived_object, original_obj):
        self._writer.start_element(
            "model", id=escape_html_id(original_obj.data.name))
        self._writer.attribute(
            "src", self.create_resource(derived_object, original_obj))
        self._writer.end_element("model")

    def create_lamp(self, obj):

        lightdata = obj.data

        if not blender_lamp_to_xml3d_light(lightdata.type)[0]:
            # Warning already reported in lightshader
            return

        self._writer.start_element(
            "light", shader="#" + escape_html_id("ls_" + lightdata.name))
        self._writer.end_element("light")
        self.context.stats.lights += 1

    def create_object(self, this_object, parent, children):

        free, derived_objects = create_derived_objects(
            self.blender_context.scene, this_object)
        if derived_objects is None:
            return

        self._object_progress()

        for derived_object, derived_matrix in derived_objects:

            self._writer.start_element("group")
            self.write_defaults(derived_object, prefix="")
            self.write_transformation(derived_object, derived_matrix)

            if this_object.type == "CAMERA":
                self.create_camera(derived_object)
            elif this_object.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                self.create_geometry(derived_object, this_object)
            elif this_object.type == "LAMP":
                self.create_lamp(derived_object)
            else:
                self.warning("Object '%s' is of type '%s', which is not (yet) supported." % (this_object.name, this_object.type))

            for obj, object_children in children:
                self.create_object(obj, this_object, object_children)

            if free:
                free_derived_objects(this_object)

            self._writer.end_element("group")
            self.context.stats.groups += 1

    def create_def(self):
        self._writer.start_element("defs")
        for lamp_data in bpy.data.lamps:
            light_model, compute = blender_lamp_to_xml3d_light(lamp_data.type)

            if not light_model:
                self.warning("Lamp '%s' is of type '%s', which is not (yet) supported. Skipped lamp." % (lamp_data.name, lamp_data.type), "lamp", 4)
                continue

            self._writer.start_element(
                "lightshader", script="urn:xml3d:lightshader:" + light_model, compute=compute)
            self.write_id(lamp_data, "ls_")

            if lamp_data.type == "SPOT":
                self._writer.element("float", name="falloffAngle", _content="%.4f" % (lamp_data.spot_size / 2.0))
                # TODO: How do spot light softness and blend correlate?
                self._writer.element("float", name="softness", _content="%.4f" % lamp_data.spot_blend)

            if lamp_data.type in {"POINT", "SPOT"}:
                attens = [1.0, 0.0, 0.0]
                if lamp_data.falloff_type == 'CONSTANT':
                    attens = [1.0, 0.0, 0.0]
                elif lamp_data.falloff_type == 'INVERSE_LINEAR':
                    attens = [1.0, 1.0 / lamp_data.distance, 0.0]
                elif lamp_data.falloff_type == 'INVERSE_SQUARE':
                    attens = [
                        1.0, 0.0, 1.0 / (lamp_data.distance * lamp_data.distance)]
                elif lamp_data.falloff_type == 'LINEAR_QUADRATIC_WEIGHTED':
                    attens = [
                        1.0, lamp_data.linear_attenuation, lamp_data.quadratic_attenuation]
                else:
                    self.warning("Lamp '%s' has falloff type '%s', which is not (yet) supported. Using CONSTANT instead." % (lamp_data.name, lamp_data.falloff_type))

                self._writer.element(
                    "float3", name="attenuation", _content="%.4f %.4f %.4f" % tuple(attens))

            self._writer.element(
                "float3", name="color", _content="%.4f %.4f %.4f" % tuple(lamp_data.color))
            self._writer.element(
                "float", name="energy", _content="%.4f" % lamp_data.energy)

            # if lamp_data.shadow_method == 'RAY_SHADOW':
            #    self._writer.element("bool", name="castShadow", _content="true")

            self._writer.end_element("lightshader")

        self._writer.end_element("defs")

    def create_scene(self, scene):
        self._writer.start_element("xml3d", id=scene.name)
        if scene.camera:
            self._writer.attribute("activeView", "#v_%s" % escape_html_id(scene.camera.name))
        else:
            self.warning("Scene '{0:s}' has no active camera set.".format(scene.name), "camera")

        # render = scene.render
        # resolution = render.resolution_x * render.resolution_percentage / 100, render.resolution_y * render.resolution_percentage / 100
        style = "width: 100%; height: 100%;"  # % (resolution[1])
        if scene.world:
            bgColor = scene.world.horizon_color
            style += " background-color:rgb(%i,%i,%i);" % tuple(gamma(bgColor))

        self._writer.attribute("style", style)

        self.create_def()
        self._writer.element("view", id="v_view")
        hierarchy = self.build_hierarchy(scene.objects)
        for obj, children in hierarchy:
            self.create_object(obj, None, children)

        # xml3dElem.writexml(output)
        self._writer.end_element("xml3d")

    def scene(self):
        self.create_scene(self.blender_context.scene)
        return self._output.getvalue()


def write_xml3d_info(dir, stats):
    with open(os.path.join(dir, "xml3d-info.json"), "w") as stats_file:
        stats_file.write(stats.to_JSON())
        stats_file.close()


def create_active_views(blender_context):
    result = []
    camera = blender_context.scene.camera
    if camera:
        result.append({
            "view_matrix": matrix_to_ccs_matrix3d(camera.matrix_world.inverted()),
            "perspective_matrix": "",  # TODO: Perspective matrix
            "translation": [e for e in camera.matrix_world.translation],
            "rotation": [e for e in camera.matrix_world.to_quaternion()]
        })

    for area in blender_context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    result.append({
                        "view_matrix": matrix_to_ccs_matrix3d(space.region_3d.view_matrix),
                        "perspective_matrix": matrix_to_ccs_matrix3d(space.region_3d.perspective_matrix),
                        "translation": [e for e in space.region_3d.view_matrix.inverted().translation],
                        "rotation": [e for e in space.region_3d.view_matrix.inverted().to_quaternion()]
                    })

    return result


def write_blender_config(dir, context):
    with open(os.path.join(dir, "blender-config.json"), "w") as stats_file:
        stats_file.write(json.dumps({
            "layers": [e for e in context.scene.layers],
            "views": create_active_views(context)
        }))
        stats_file.close()


def save(operator,
         context, filepath="",
         use_selection=True,
         global_matrix=None,
         template_selection="preview",
         xml3djs_selection="",
         xml3d_minimzed=False,
         transform_representation="css"
         ):
    """Save the Blender scene to a XML3D/HTML file."""

    from string import Template

    def object_progress():
        count = 0
        context.window_manager.progress_begin(0, len(context.scene.objects))

        def progress():
            nonlocal count
            count += 1
            context.window_manager.progress_update(count)
        return progress

    # TODO: Time the export
    # time1 = time.clock()

    version = xml3djs_selection + ("-min" if xml3d_minimzed else "") + ".js"

    dirName = os.path.dirname(__file__)
    output_dir = os.path.dirname(filepath)

    # export the scene with all its assets
    xml3d_exporter = XML3DExporter(context, os.path.dirname(filepath), transform_representation, object_progress())
    scene = xml3d_exporter.scene()

    template_dir = os.path.join(dirName, "templates\\%s\\" % template_selection)
    template_path = os.path.join(template_dir, 'index.html')
    # TODO: Handle case if template file does not exist
    with open(template_path, "r") as templateFile:
        data = Template(templateFile.read())
        file = open(filepath, 'w')
        file.write(data.substitute(title=context.scene.name, xml3d=scene,
                                   version=version, generator="xml3d-blender-exporter v0.1.0"))
        file.close()

    # TODO: Make writing out stats optional
    info_dir = os.path.join(output_dir, "info")
    if not os.path.exists(info_dir):
        os.makedirs(info_dir)

    write_xml3d_info(info_dir, xml3d_exporter.stats())
    write_blender_config(info_dir, context)

    # copy all common files
    target_dir = os.path.join(output_dir, "common")
    if not os.path.exists(target_dir):
        copytree(os.path.join(dirName, "common"), target_dir)

    # copy template specific files
    target_dir = os.path.join(output_dir, "public")
    if not os.path.exists(target_dir):
        copytree(os.path.join(template_dir, "public"), target_dir)

    # context.window_manager.progress_end()

    return {'FINISHED'}
