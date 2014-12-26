import os
import bpy
import re
import base64
from xml.dom.minidom import Document
from bpy_extras.io_utils import path_reference, path_reference_copy
from .tools import Vertex, Stats, EntityExporter

BLENDER2XML_MATERIAL = "(diffuseColor, specularColor, shininess, ambientIntensity) = xflow.blenderMaterial(diffuse_color, diffuse_intensity, specular_color, specular_intensity, specular_hardness)"

TEXTURE_EXTENSION_MAP = dict(REPEAT="repeat", EXTEND="clamp")


def appendUnique(mlist, value):
    if value in mlist:
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True


class AssetExporter(EntityExporter):
    def __init__(self, path, scene):
        super().__init__(Stats(materials=0, meshes=[], assets=[], textures=0, warnings=[]))
        self._path = path
        self._dir = os.path.dirname(path)
        self._scene = scene
        self._asset = {u"mesh": [], u"data": {}}
        self._material = {}
        self._copy_set = set()

    def add_default_material(self):
        if "defaultMaterial" in self._material:
            return

        data = [{"type": "float3", "name": "diffuseColor", "value": "0.8 0.8 0.8"},
                {"type": "float3", "name": "specularColor", "value": "1.0 1.0 0.1"},
                {"type": "float", "name": "ambientIntensity", "value": "0.5"}]

        self._material["defaultMaterial"] = {
            "content": {"data": data}, "script": "urn:xml3d:shader:phong"}

    def add_material(self, material):
        materialName = material.name
        if materialName in self._material:
            return
        data = []
        data.append({"type": "float", "name": "diffuse_intensity",
                     "value": material.diffuse_intensity})
        data.append({"type": "float3", "name": "diffuse_color",
                     "value": [tuple(material.diffuse_color)]})
        data.append({"type": "float", "name": "specular_intensity",
                     "value": material.specular_intensity})
        data.append({"type": "float3", "name": "specular_color",
                     "value": [tuple(material.specular_color)]})
        data.append({"type": "float", "name": "specular_hardness",
                     "value": material.specular_hardness})
        data.append(
            {"type": "float", "name": "ambient", "value": material.ambient})

        self._material[materialName] = {"content": {
            "data": data}, "script": "urn:xml3d:shader:phong", "compute": BLENDER2XML_MATERIAL}

        # if material.use_face_texture:
        # print("Warning: Material '%s' uses 'Face Textures', which are not (yet) supported. Skipping texture..." % materialName)
        # return

        for texture_index, texture_slot in enumerate(material.texture_slots):
            if not material.use_textures[texture_index] or texture_slot is None:
                continue

            # TODO: Support uses of textures other than diffuse
            if not texture_slot.use_map_color_diffuse or texture_slot.diffuse_color_factor < 0.0001:
                print("No use")
                continue

            if texture_slot.texture_coords != 'UV':
                self.warning(
                    u"Texture '{0:s}' of material '{1:s}' uses '{2:s}' mapping, which is not (yet) supported. Dropped Texture."
                    .format(texture_slot.name, materialName, texture_slot.texture_coords), "texture", 5)
                continue

            texture = texture_slot.texture
            if texture.type != 'IMAGE':
                print(
                    "Warning: Texture '%s' of material '%s' is of type '%s' which is not (yet) supported. Dropped Texture."
                    % (texture_slot.name, materialName, texture.type), "texture")
                continue

            image_src = self.export_image(texture.image)

            if texture.extension in {'REPEAT', 'EXTEND'}:
                wrap = TEXTURE_EXTENSION_MAP[texture.extension]
            else:
                wrap = None
                self.warning(
                    u"Texture '{0:s}' of material '{1:s}' has extension '{2:s}' which is not (yet) supported. Using default 'Extend' instead..."
                    .format(texture_slot.name, materialName, texture.extension), "texture")

            if image_src:
                # TODO: extension/clamp, filtering, sampling parameters
                # FEATURE: Resize / convert / optimize texture
                data.append(
                    {"type": "texture", "name": "diffuseTexture", "wrap": wrap, "value": image_src})

    def export_image(self, image):
        if image.source not in {'FILE', 'VIDEO'}:
            self.warning(u"Image '{0:s}' is of source '{1:s}' which is not (yet) supported. Using default ...".format(image.name, image.source), "texture")
            return None

        if image.packed_file:
            mime_type = "image/png"
            image_data = base64.b64encode(image.packed_file.data).decode("utf-8")
            image_src = "data:%s;base64,%s" % (mime_type, image_data)
        else:
            base_src = os.path.dirname(bpy.data.filepath)
            filepath_full = bpy.path.abspath(image.filepath, library=image.library)
            image_src = path_reference(filepath_full, base_src, self._dir, 'COPY', "textures", self._copy_set, image.library)

            # print("image", image_src, image.filepath, self._copy_set)
            image_src = image_src.replace('\\', '/')

        return image_src

    def add_mesh(self, original_object, derived_object):
        if derived_object.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            return

        try:
            data = derived_object.to_mesh(self._scene, True, 'RENDER', True)
        except:
            data = None

        if data:
            self.addMeshData(data)

    def export_tessfaces(self, mesh):
        if not len(mesh.tessfaces):
            self.warning(u"Mesh '{0:s}' has no triangles. Pure line geometry not (yet) supported. Try extruding a little.".format(mesh.name), "geometry")
            return None, None

        materialCount = len(mesh.materials)

        # Mesh indices:
        # For each material allocate an array
        # @UnusedVariable
        indices = [[] for m in range(1 if materialCount == 0 else materialCount)]

        # All vertices of the mesh, trying to keep the number of vertices small
        vertices = []
        # Vertex cache
        vertex_dict = {}

        uv_data = None
        if len(mesh.tessface_uv_textures):
            uv_data = [uv.data for uv in mesh.tessface_uv_textures]
            uv_data = list(zip(*uv_data))

        '''	@type bpytypes.MeshTessFace '''
        faces = mesh.tessfaces
        for faceIndex, face in enumerate(faces):

            if uv_data:
                ''' @type tuple(bpy.types.MeshTextureFace) '''
                uv_faces = uv_data[faceIndex]
                uv_vertices = [uv_face.uv for uv_face in uv_faces]
                uv_vertices = list(zip(*uv_vertices))

            faceIndices = []

            for i, vertexIndex in enumerate(face.vertices):
                normal = mesh.vertices[
                    vertexIndex].normal if face.use_smooth else face.normal
                uv_vertex = uv_vertices[i][0] if uv_data else None

                mv = Vertex(vertexIndex, normal, uv_vertex)

                index, added = appendUnique(vertex_dict, mv)
                faceIndices.append(index)
                # print("enumerate: %d -> %d (%d)" % (i, vertexIndex, index))
                if added:
                    vertices.append(mv)

            if len(faceIndices) == 3:
                indices[face.material_index].extend(faceIndices)
            elif len(faceIndices) == 4:
                face2 = [faceIndices[2], faceIndices[3], faceIndices[0]]
                faceIndices[3:] = face2
                indices[face.material_index].extend(faceIndices)
            else:
                print("Found %s vertices" % len(faceIndices))

        return vertices, indices

    def export_mesh_textures(self, mesh):
        textures = [None] * len(mesh.materials)
        for i, material in enumerate(mesh.materials):
            if material.use_face_texture:
                try:
                    textures[i] = {"image": mesh.tessface_uv_textures[i].data[
                        0].image, "alpha": material.use_face_texture_alpha}
                except:
                    textures[i] = None
        return textures

    def addMeshData(self, mesh):
        meshName = self.safe_include_name(mesh.name)
        # print("Writing mesh %s" % meshName)
        materialCount = len(mesh.materials)

        # Export based on tess_faces:
        vertices, indices = self.export_tessfaces(mesh)

        if not (vertices and indices):
            return

        content = []
        # Vertex positions and normals
        positions = []
        normals = []
        texcoord = []
        has_texcoords = vertices[0].texcoord
        for v in vertices:
            positions.append(tuple(mesh.vertices[v.index].co))
            normals.append(tuple(v.normal))
            if has_texcoords:
                texcoord.append(tuple(v.texcoord))

        content.append(
            {"type": "float3", "name": "position", "value": positions})
        content.append({"type": "float3", "name": "normal", "value": normals})
        if has_texcoords:
            content.append(
                {"type": "float2", "name": "texcoord", "value": texcoord})

        self._asset['data'][meshName] = {"content": content}

        mesh_textures = self.export_mesh_textures(mesh)

        for materialIndex, material in enumerate(mesh.materials if materialCount else [None]):
            if len(indices[materialIndex]) == 0:
                continue

            materialName = material.name if material else "defaultMaterial"

            data = []
            data.append(
                {"type": "int", "name": "index", "value": indices[materialIndex]})

            # Mesh Textures
            if material and mesh_textures[materialIndex] and mesh_textures[materialIndex]["image"]:
                image_src = self.export_image(mesh_textures[materialIndex]["image"])
                if image_src:
                    # TODO: Image Sampling parameters
                    # FEATURE: Resize / convert / optimize texture
                    data.append(
                        {"type": "texture", "name": "diffuseTexture", "value": image_src, "wrap": None})
                if mesh_textures[materialIndex]["alpha"]:
                    data.append(
                        {"type": "float", "name": "transparency", "value": "0.002"})

            submeshName = meshName + "_" + materialName
            self._asset['mesh'].append(
                {"name": submeshName, "includes": meshName, "data": data, "shader": "#" + materialName})

            if material:
                self.add_material(material)
            else:
                self.add_default_material()

    def safe_include_name(self, name):
        return re.sub('[\.]+', '-', name)

    def saveXML(self, f, stats):
        doc = Document()
        xml3d = doc.createElement("xml3d")
        doc.appendChild(xml3d)

        asset = doc.createElement("asset")
        asset.setAttribute("id", "root")
        xml3d.appendChild(asset)

        for name, material in self._material.items():
            shader = doc.createElement("shader")
            shader.setAttribute("id", name)
            shader.setAttribute("script", material["script"])
            if "compute" in material:
                shader.setAttribute("compute", material["compute"])
            xml3d.appendChild(shader)
            content = material["content"]
            for entry in content["data"]:
                entryElement = AssetExporter.writeGenericContent(
                    doc, entry, stats)
                shader.appendChild(entryElement)
            stats.materials += 1

        for name, value in self._asset["data"].items():
            assetData = doc.createElement("assetdata")
            assetData.setAttribute("name", name)
            asset.appendChild(assetData)
            for entry in value["content"]:
                entryElement = AssetExporter.writeGenericContent(
                    doc, entry, stats)
                assetData.appendChild(entryElement)

        for mesh in self._asset["mesh"]:
            assetMesh = doc.createElement("assetmesh")
            assetMesh.setAttribute("name", mesh["name"])
            assetMesh.setAttribute("includes", mesh["includes"])
            assetMesh.setAttribute("shader", mesh["shader"])
            asset.appendChild(assetMesh)
            for entry in mesh["data"]:
                entryElement = AssetExporter.writeGenericContent(
                    doc, entry, stats)
                assetMesh.appendChild(entryElement)
            stats.meshes.append(mesh["name"])

        doc.writexml(f, "", "  ", "\n", "UTF-8")

    def writeGenericContent(doc, entry, stats=None):
        entry_type = entry["type"]
        entryElement = doc.createElement(entry_type)
        entryElement.setAttribute("name", entry["name"])

        value = entry["value"]
        value_str = None
        if entry_type == "int":
            value_str = " ".join(str(e) for e in value)
        elif entry_type == "texture":

            if entry["wrap"] is not None:
                entryElement.setAttribute("wrapS", entry["wrap"])
                entryElement.setAttribute("wrapT", entry["wrap"])

            imgElement = doc.createElement("img")
            imgElement.setAttribute("src", value)
            entryElement.appendChild(imgElement)
            stats.textures += 1
        else:
            if not isinstance(value, list):
                value_str = str(value)
            else:
                value_str = ""
                for t in value:
                    length = len(t) if isinstance(t, tuple) else 1
                    fs = length * "%.6f "
                    value_str += fs % t

        if value_str:
            textNode = doc.createTextNode(value_str)
            entryElement.appendChild(textNode)
        return entryElement

    def copy_report(self, str):
        print("Report: " + str)

    def save(self):
        stats = self._stats
        stats.assets.append({"url": self._path})

        with open(self._path, "w") as assetFile:
            self.saveXML(assetFile, stats)
            assetFile.close()
            os.path.getsize(self._path)
            stats.assets[0]["size"] = os.path.getsize(self._path)

        try:
            path_reference_copy(self._copy_set, self.copy_report)
        except PermissionError:
            print('ERROR: While copying textures: %s' % self._copy_set)

        return stats
