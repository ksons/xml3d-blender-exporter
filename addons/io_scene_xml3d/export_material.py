import os
from xml.dom.minidom import Document
from .cycles_material import CyclesMaterial
from .data import DataType, DataEntry, TextureEntry, write_generic_entry
from .export_image import export_image
from . import tools

BLENDER2XML_MATERIAL = "(diffuseColor, specularColor, shininess, transparency) = xflow.blenderMaterial(diffuse_color, diffuse_intensity, specular_color, specular_intensity, specular_hardness, alpha)"

TEXTURE_EXTENSION_MAP = dict(REPEAT="repeat", EXTEND="clamp")



class Material:
    context = None
    id = ""
    script = "urn:xml3d:shader:phong"
    data = None
    compute = None
    dir = None
    copy_set = set()

    def __init__(self, name, context, path):
        self.id = name
        self.context = context
        self.path = path
        self.data = []

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @staticmethod
    def from_blender_material(material, context, path):
        material_id = tools.safe_query_selector_id(material.name)
        mat = Material(material_id, context, path)
        mat.from_material(material)
        mat.compute = BLENDER2XML_MATERIAL
        return mat

    @staticmethod
    def evaluate_location(material, option):
        if option == "external":
            return "external"
        if option == "include":
            return "internal"
        # Single user means one user plus python environment which adds another user
        if option == "shared" and material and material.users <= 2:
            return "internal"
        if option == "none":
            return None
        return "external"

    def from_material(self, material):
        print("Material", material.name)
        if material.node_tree:
            script, err = CyclesMaterial(material.node_tree).create()
            if err:
                self.context.warning("In material '{0:s}': {1:s}. Fallback to standard material model.".format(material.name, err))
            else:
                self.script = script

        data = self.data
        data.append(DataEntry("diffuse_intensity", DataType.float, material.diffuse_intensity))
        data.append(DataEntry("diffuse_color", DataType.float3, list(material.diffuse_color)))
        data.append(DataEntry("specular_intensity", DataType.float, material.specular_intensity))
        data.append(DataEntry("specular_color", DataType.float3, list(material.specular_color)))
        data.append(DataEntry("specular_hardness", DataType.float, material.specular_hardness))

        world_ambient = self.context.scene.world.ambient_color
        if world_ambient.v > 0.0:
            local_ambient = material.ambient
            data.append(DataEntry("ambientIntensity", DataType.float, local_ambient * pow(world_ambient.v, 1.0 / 2.2)))

        if material.use_transparency:
            data.append(DataEntry("alpha", DataType.float, material.alpha))
        else:
            data.append(DataEntry("alpha", DataType.float, 1))

        # if material.use_face_texture:
        # print("Warning: Material '%s' uses 'Face Textures', which are not (yet) supported. Skipping texture..." % materialName)
        # return

        for texture_index, texture_slot in enumerate(material.texture_slots):
            if not material.use_textures[texture_index] or texture_slot is None:
                continue

            # TODO: Support uses of textures other than diffuse
            if not texture_slot.use_map_color_diffuse or texture_slot.diffuse_color_factor < 0.0001:
                # print("No use")
                continue

            if texture_slot.texture_coords != 'UV':
                self.context.warning(
                    u"Texture '{0:s}' of material '{1:s}' uses '{2:s}' mapping, which is not (yet) supported. Dropped Texture."
                    .format(texture_slot.name, material.name, texture_slot.texture_coords), "texture", 5)
                continue

            texture = texture_slot.texture
            if texture.type != 'IMAGE':
                self.context.warning(
                    "Warning: Texture '%s' of material '%s' is of type '%s' which is not (yet) supported. Dropped Texture."
                    % (texture_slot.name, material.name, texture.type), "texture")
                continue

            image_src = export_image(texture.image, self.context)

            if texture.extension in {'REPEAT', 'EXTEND'}:
                wrap = TEXTURE_EXTENSION_MAP[texture.extension]
            else:
                wrap = None
                self.context.warning(
                    u"Texture '{0:s}' of material '{1:s}' has extension '{2:s}' which is not (yet) supported. Using default 'Extend' instead..."
                    .format(texture_slot.name, material.name, texture.extension), "texture")

            if image_src:
                # TODO: extension/clamp, filtering, sampling parameters
                # FEATURE: Resize / convert / optimize texture
                data.append(TextureEntry("diffuseTexture", image_src, wrap_type=wrap))

DefaultMaterial = Material("defaultMaterial", None, None)
DefaultMaterial.data = [
    DataEntry("diffuseColor", DataType.float3, "0.8 0.8 0.8"),
    DataEntry("specularColor", DataType.float3, "1.0 1.0 1.0"),
    DataEntry("ambientIntensity", DataType.float, "0.5")
]


class MaterialLibrary:
    materials = None
    url = None

    def __init__(self, context, url):
        self.materials = []
        self.context = context
        self.url = url

    def add_material(self, material):
        if material not in self.materials:
            self.materials.append(material)
        return "./" + self.url + "#" + material.id

    def __save_xml(self, file):
        doc = Document()
        xml3d = doc.createElement("xml3d")
        doc.appendChild(xml3d)

        for material in self.materials:
            MaterialLibrary.save_material_xml(material, xml3d)

        doc.writexml(file, "", "  ", "\n", "UTF-8")

    @staticmethod
    def save_material_xml(material, parent):
        doc = parent.ownerDocument
        shader = doc.createElement("shader")
        shader.setAttribute("id", material.id)

        if material.script.startswith("urn:"):
            shader.setAttribute("script", material.script)
        else:
            shader.setAttribute("script", "#s_" + material.id)
            script = doc.createElement("script")
            script.setAttribute("id", "s_" + material.id)
            script.setAttribute("type", "text/shade-javascript")
            text = doc.createTextNode(material.script)
            script.appendChild(text)
            parent.appendChild(script)

        if material.compute:
            shader.setAttribute("compute", material.compute)
        for entry in material.data:
            entry_element = write_generic_entry(shader.ownerDocument, entry)
            shader.appendChild(entry_element)
        parent.appendChild(shader)
        pass

    def save(self):
        if not len(self.materials):
            return

        with open(self.url, "w") as materialFile:
            self.__save_xml(materialFile)
            materialFile.close()
            size = os.path.getsize(self.url)

        self.context.stats.materials.append({"name": os.path.basename(self.url), "size": size})


