import os
import io
import bpy
import math
import json
from . import xml_writer, export_asset, context
from . import tools
from .data import write_generic_entry_html
from shutil import copytree

VERSION = "0.2.0"
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


def blender_lamp_to_xml3d_light(model):
    if model in LIGHTMODELMAP:
        result = LIGHTMODELMAP[model]
        return result[0], result[1]
    return None, None


class XML3DExporter():
    context = None

    def __init__(self, blender_context, dirname, options, progress):
        self.blender_context = blender_context
        self.context = context.Context(dirname, blender_context.scene, options)
        self._output = io.StringIO()
        self._writer = xml_writer.XMLWriter(self._output, 0)
        self._resource = {}
        self._object_progress = progress
        self.asset_collections = {}

    def create_asset_directory(self):
        assetDir = os.path.join(self.context.base_url, ASSETDIR)
        if not os.path.exists(assetDir):
            os.makedirs(assetDir)
        return assetDir

    def stats(self):
        return self.context.stats

    def warning(self, message, category=None, issue=None):
        self.context.warning(message, category, issue)

    def get_or_create_asset_collection(self, obj):
        asset_collection_name = self.context.get_asset_collection(obj)
        path = os.path.join(self.create_asset_directory(), asset_collection_name + ".xml")

        if path in self.asset_collections:
            return self.asset_collections[path]

        asset_collection = export_asset.AssetCollection(asset_collection_name, self.context, path, self.blender_context.scene)
        self.asset_collections[path] = asset_collection
        return asset_collection

    def add_to_asset_collection(self, geo_obj):
        assert geo_obj.type in {"MESH", "FONT", "SURFACE", "CURVE", "ARMATURE"}

        asset_collection = self.get_or_create_asset_collection(geo_obj)
        fragment, asset_config = asset_collection.add_asset(geo_obj)

        if not asset_config:
            return None, None

        url = "%s/%s.xml#%s" % (ASSETDIR, asset_collection.name, fragment)
        return url, asset_config

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
        self._writer.attribute("id", tools.escape_html_id(prefix + obj.name))

    def write_event_attributes(self, obj):
        for event in {"click", "dblclick", "mousedown", "mouseup", "mouseover", "mousemove", "mouseout", "mousewheel"}:
            if event in obj:
                self._writer.attribute("on" + event, obj[event])

    def write_transformation(self, obj):
        # try:
        matrix = obj.matrix_basis

        options = self.context.options
        if options.transform_representation == "css":
            matrices = []

            if not tools.is_identity(obj.matrix_parent_inverse):
                matrices.append(
                    tools.matrix_to_ccs_matrix3d(obj.matrix_parent_inverse))

            old_rotation_mode = obj.rotation_mode
            obj.rotation_mode = "AXIS_ANGLE"
            if not tools.is_identity_translate(obj.location):
                matrices.append("translate3d(%.6f,%.6f,%.6f)" %
                                tuple(obj.location))
            rot = obj.rotation_axis_angle
            if rot[0] != 0.0:
                matrices.append("rotate3d(%.6f,%.6f,%.6f,%.2fdeg)" % (
                    rot[1], rot[2], rot[3], math.degrees(rot[0])))
            if not tools.is_identity_scale(obj.scale):
                matrices.append("scale3d(%.6f,%.6f,%.6f)" % tuple(obj.scale))
            transform = " ".join(matrices)
            obj.rotation_mode = old_rotation_mode
        else:
            matrix = obj.matrix_parent_inverse * matrix
            if tools.is_identity(matrix):
                return
            transform = tools.matrix_to_ccs_matrix3d(matrix)

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

    def create_model_configuration(self, model_config):
        for child_config in model_config.children:
            if child_config is not None:
                self._writer.start_element("assetdata", name=child_config.name)
                for entry in child_config.data:
                        write_generic_entry_html(self._writer, entry)
                self._writer.end_element("assetdata")

    def create_geometry(self, original_obj):
        url, model_config = self.add_to_asset_collection(original_obj)
        if not url:
            return

        self._writer.start_element("model")
        self._writer.attribute("src", url)

        if model_config:
            self.create_model_configuration(model_config)

        self._writer.end_element("model")

    def create_lamp(self, obj):

        lightdata = obj.data

        if not blender_lamp_to_xml3d_light(lightdata.type)[0]:
            # Warning already reported in lightshader
            return

        self._writer.start_element(
            "light", shader="#" + tools.escape_html_id("ls_" + lightdata.name))
        self._writer.end_element("light")
        self.context.stats.lights += 1

    def create_object(self, this_object, parent, children):

        self._object_progress()

        self._writer.start_element("group")
        self.write_defaults(this_object, prefix="")
        self.write_transformation(this_object)
        self.write_event_attributes(this_object)

        if this_object.type == "CAMERA":
            self.create_camera(this_object)
        elif this_object.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
            self.create_geometry(this_object)
        elif this_object.type == "ARMATURE":
            self.context.armatures.create_armature(this_object)
        elif this_object.type == "LAMP":
            self.create_lamp(this_object)
        elif this_object.type == "EMPTY":
            pass
        else:
            self.warning("Object '%s' is of type '%s', which is not (yet) supported." % (this_object.name, this_object.type))

        for obj, object_children in children:
            self.create_object(obj, this_object, object_children)

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

    def check_scene(self, scene):
        if scene.world.ambient_color.v > 0.0:
            self.warning("World '{0:s}' has Ambient Color set, which is only partially supported.".format(scene.world.name), "world", issue=6)

    def create_scene(self, scene):
        self.check_scene(scene)

        self._writer.start_element("xml3d", id=scene.name)
        if scene.camera:
            self._writer.attribute("activeView", "#v_%s" % tools.escape_html_id(scene.camera.name))
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

    def finalize(self):
        for collection in self.asset_collections.values():
            collection.save()

        self.context.finalize()


def write_xml3d_info(dir, stats):
    with open(os.path.join(dir, "xml3d-info.json"), "w") as stats_file:
        stats_file.write(stats.to_JSON())
        stats_file.close()


def create_active_views(blender_context):
    result = []
    camera = blender_context.scene.camera
    if camera:
        result.append({
            "view_matrix": tools.matrix_to_ccs_matrix3d(camera.matrix_world.inverted()),
            "perspective_matrix": "",  # TODO: Perspective matrix
            "translation": [e for e in camera.matrix_world.translation],
            "rotation": [e for e in camera.matrix_world.to_quaternion()]
        })

    for area in blender_context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    result.append({
                        "view_matrix": tools.matrix_to_ccs_matrix3d(space.region_3d.view_matrix),
                        "perspective_matrix": tools.matrix_to_ccs_matrix3d(space.region_3d.perspective_matrix),
                        "translation": [e for e in space.region_3d.view_matrix.inverted().translation],
                        "rotation": [e for e in space.region_3d.view_matrix.inverted().to_quaternion()]
                    })

    return result


def write_blender_config(dir, context):
    with open(os.path.join(dir, "blender-config.json"), "w") as stats_file:
        stats_file.write(json.dumps({
            "layers": [e for e in context.scene.layers],
            "views": create_active_views(context),
            "render-settings": {
                "fps": context.scene.render.fps
            }
        }))
        stats_file.close()


def save(operator, context, options):
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

    version = options['xml3djs_selection'] + ("-min" if options['xml3d_minimized'] else "") + ".js"

    dirName = os.path.dirname(__file__)
    file_path = options['filepath']
    output_dir = os.path.dirname(file_path)

    # export the scene with all its assets
    xml3d_exporter = XML3DExporter(context, output_dir, options, object_progress())
    scene = xml3d_exporter.scene()
    xml3d_exporter.finalize()

    template_dir = os.path.join(dirName, "templates/%s/" % options['template_selection'])
    template_path = os.path.join(template_dir, 'index.html')
    # TODO: Handle case if template file does not exist
    with open(template_path, "r") as templateFile:
        data = Template(templateFile.read())
        file = open(file_path, 'w')
        file.write(data.substitute(title=context.scene.name, xml3d=scene,
                                   version=version, generator="xml3d-blender-exporter v" + VERSION))
        file.close()
        size = os.path.getsize(file_path)
        xml3d_exporter.stats().scene = {"name": os.path.basename(file_path), "size": size}

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
