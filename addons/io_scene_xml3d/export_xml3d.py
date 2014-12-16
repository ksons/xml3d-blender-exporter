import os, io, re, bpy, math
from . import xml_writer, export_asset
from bpy_extras.io_utils import create_derived_objects, free_derived_objects
from .tools import *
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

def bender_lamp_to_xml3d_light(model):
    if model in LIGHTMODELMAP:
        result = LIGHTMODELMAP[model]
        return result[0], result[1]
    return None, None

class XML3DExporter:
    def __init__(self, context, dirname,transform, progress):
        self._context = context
        self._output = io.StringIO()
        self._writer = xml_writer.XMLWriter(self._output, 0)
        self._resource = {}
        self._dirname = dirname
        self._transform = transform
        self._object_progress = progress
        self._stats = Stats(assets = [], lights = 0, views = 0, groups = 0)

    def create_asset_directory(self):
        assetDir = os.path.join(self._dirname, ASSETDIR)
        if not os.path.exists(assetDir):
            os.makedirs(assetDir)
        return assetDir

    def create_resource_from_mesh(self, original_object, derived_object):
        mesh_data_name = original_object.data.name
        path = self.create_asset_directory()
        path = os.path.join(path, mesh_data_name + ".xml")
        url  = "%s/%s.xml" % (ASSETDIR, mesh_data_name)

        exporter = export_asset.AssetExporter(path, self._context.scene)
        exporter.add_mesh(original_object, derived_object)
        stats = exporter.save()

        stats.assets[0]["url"] = url
        self._stats.join(stats)
        return url + "#root"

    def create_resource(self, obj, derived):
        free = None
        url = ""

        if obj.type in {"MESH", "FONT", "SURFACE", "CURVE"}:
            meshData = obj.data
            key = "mesh." + meshData.name
            if key in self._resource:
                return self._resource[key]


            url = self.create_resource_from_mesh(obj, derived)
            self._resource[key] = url
        else:
            print("Warning: Object '%s' is of type '%s', which is not (yet) supported." % (obj.name, obj.type))

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
            par_lookup.setdefault(test_parent(obj.parent), []).append((obj, []))

        for parent, children in par_lookup.items():
            for obj, subchildren in children:
                subchildren[:] = par_lookup.get(obj, [])

        return par_lookup.get(None, [])


    def write_id(self, obj, prefix = ""):
        self._writer.attribute("id", escape_html_id(prefix + obj.name))

    def write_transformation(self, obj, derived_matrix) :
        #try:
        matrix = obj.matrix_basis


        if self._transform == "cssl":
            matrices = []

            if not is_identity(obj.matrix_parent_inverse):
                matrices.append(matrix_to_ccs_matrix3d(obj.matrix_parent_inverse))

            old_rotation_mode = obj.rotation_mode
            obj.rotation_mode = "AXIS_ANGLE"
            if not is_identity_translate(obj.location):
                matrices.append("translate3d(%.6f,%.6f,%.6f)" % tuple(obj.location))
            rot = obj.rotation_axis_angle
            if rot[0] != 0.0:
                matrices.append("rotate3d(%.6f,%.6f,%.6f,%.2fdeg)" % (rot[1],rot[2],rot[3],math.degrees(rot[0])))
            if not is_identity_scale(obj.scale):
                matrices.append("scale3d(%.6f,%.6f,%.6f)" % tuple(obj.scale))
            transform = " ".join(matrices);
            obj.rotation_mode = old_rotation_mode
        else:
            matrix = obj.matrix_parent_inverse * derived_matrix
            if is_identity(matrix):
                return
            transform = matrix_to_ccs_matrix3d(matrix)


        self._writer.attribute("style", "transform:" + transform + ";")

    def write_class(self,obj):
        layers = []
        for i in range(len(obj.layers)):
            if obj.layers[i] == True:
                layers.append("layer-%d" % i)
        className = " ".join(layers)
        self._writer.attribute("class", className)

    def write_defaults(self, obj, prefix = ""):
        self.write_id(obj, prefix)
        self.write_class(obj)

    def create_camera(self, obj):
        self._writer.startElement("view")
        self.write_id(obj, "v_")
        self._writer.endElement("view")
        self._stats.views += 1

    def create_geometry(self, derived_object, original_obj):
        self._writer.startElement("model", id=escape_html_id(original_obj.data.name))
        self._writer.attribute("src", self.create_resource(derived_object, original_obj))
        self._writer.endElement("model")

    def create_lamp(self, obj):

        lightdata = obj.data

        if not bender_lamp_to_xml3d_light(lightdata.type)[0]:
            # Warning already reported in lightshader
            return

        self._writer.startElement("light", shader="#"+escape_html_id("ls_"+lightdata.name))
        self._writer.endElement("light")
        self._stats.lights += 1


    def create_object(self, this_object, parent, children):

        free, derived_objects = create_derived_objects(self._context.scene, this_object)
        if derived_objects is None:
            return

        self._object_progress()

        for derived_object, derived_matrix in derived_objects:

            self._writer.startElement("group")
            self.write_defaults(derived_object, prefix="")
            self.write_transformation(derived_object, derived_matrix)

            if this_object.type == "CAMERA":
                self.create_camera(derived_object)
            elif this_object.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                self.create_geometry(derived_object, this_object)
            elif this_object.type == "LAMP":
                self.create_lamp(derived_object)
            else:
                print("Warning: Object '%s' is of type '%s', which is not (yet) supported." % (this_object.name, this_object.type))

            for obj, object_children in children:
                self.create_object(obj, this_object, object_children)

            if free:
                free_derived_objects(this_object)

            self._writer.endElement("group")
            self._stats.groups += 1

    def create_def(self):
        self._writer.startElement("defs")
        for lamp_data in bpy.data.lamps:
            light_model, compute = bender_lamp_to_xml3d_light(lamp_data.type)

            if not light_model:
                print("Warning: Lamp '%s' is of type '%s', which is not (yet) supported." % (lamp_data.name, lamp_data.type))
                continue

            self._writer.startElement("lightshader", script="urn:xml3d:lightshader:" + light_model, compute= compute)
            self.write_id(lamp_data, "ls_")

            if lamp_data.type in {"POINT", "SPOT"}:
                attens = [1.0, 0.0, 0.0]
                if lamp_data.falloff_type == 'CONSTANT' :
                    attens = [1.0, 0.0, 0.0]
                elif lamp_data.falloff_type == 'INVERSE_LINEAR' :
                    attens = [1.0, 1.0 / light.distance, 0.0]
                elif lamp_data.falloff_type == 'INVERSE_SQUARE' :
                    attens = [1.0, 0.0, 1.0 / (lamp_data.distance * lamp_data.distance)]
                elif light.falloff_type == 'LINEAR_QUADRATIC_WEIGHTED' :
                    attens = [1.0, lamp_data.linear_attenuation, lamp_data.quadratic_attenuation]
                else :
                    print("WARNING: Lamp '%s' has falloff type '%s', which is not (yet) supported. Using CONSTANT instead." % (lamp_data.name, light.falloff_type))

                self._writer.element("float3", name="attenuation", _content="%.4f %.4f %.4f" % tuple(attens))

            self._writer.element("float3", name="color", _content="%.4f %.4f %.4f" % tuple(lamp_data.color))
            self._writer.element("float", name="energy", _content="%.4f" % lamp_data.energy)

            #if lamp_data.shadow_method == 'RAY_SHADOW':
            #    self._writer.element("bool", name="castShadow", _content="true")

            self._writer.endElement("lightshader")

        self._writer.endElement("defs")


    def create_scene(self, scene):
        self._writer.startElement("xml3d", id=scene.name)
        if scene.camera:
            self._writer.attribute("activeView", "#v_%s" % escape_html_id(scene.camera.name))

        render = scene.render
        resolution = render.resolution_x * render.resolution_percentage / 100, render.resolution_y * render.resolution_percentage / 100
        style = "width: 100%; height: 100%;" #% (resolution[1])
        if scene.world :
            bgColor = scene.world.horizon_color
            style += " background-color:rgb(%i,%i,%i);" % tuple(gamma(bgColor))

        self._writer.attribute("style", style)

        self.create_def()
        hierarchy = self.build_hierarchy(scene.objects)
        for obj, children in hierarchy:
            self.create_object(obj, None, children)

        #xml3dElem.writexml(output)
        self._writer.endElement("xml3d")

    def scene(self):
        self.create_scene(self._context.scene)
        return self._output.getvalue()

def save(operator,
         context, filepath="",
         use_selection=True,
         global_matrix=None,
         template_selection="preview",
         xml3djs_selection = "",
         xml3d_minimzed = False,
         transform_representation = "css"
         ):
    """Save the Blender scene to a XML3D/HTML file."""

    import mathutils

    import time
    from bpy_extras.io_utils import create_derived_objects, free_derived_objects
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

    version = "%s%s.js" % (xml3djs_selection, "-min" if xml3d_minimzed else "")

    dirName = os.path.dirname(__file__)
    outputDir = os.path.dirname(filepath)
    templatePath = os.path.join(dirName, 'templates\\%s.html' % template_selection)
    #TODO: Handle case if template file does not exist
    with open (templatePath, "r") as templateFile:
        data=Template(templateFile.read())
        file = open(filepath, 'w')
        xml3d_exporter = XML3DExporter(context, os.path.dirname(filepath), transform_representation, object_progress())
        scene = xml3d_exporter.scene()
        file.write(data.substitute(title=context.scene.name,xml3d=scene,version=version,generator="xml3d-blender-exporter v0.1.0"))
        file.close()

        # TODO: Write out stats (optionally)
        #print(xml3d_exporter._stats.to_JSON())

    publicDir = os.path.join(outputDir, "public")
    if not os.path.exists(publicDir):
        copytree(os.path.join(dirName, "public"), publicDir)

    #context.window_manager.progress_end()

    return {'FINISHED'}