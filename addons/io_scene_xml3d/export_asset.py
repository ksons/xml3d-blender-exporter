import os
from xml.dom.minidom import Document
from bpy_extras.io_utils import path_reference_copy
from .export_material import Material, DefaultMaterial, export_image
from .tools import Vertex, safe_query_selector_id


def appendUnique(mlist, value):
    if value in mlist:
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True


class AssetExporter:
    context = None

    def __init__(self, context, path, scene):
        self.context = context
        self._path = path
        self._dir = os.path.dirname(path)
        self._scene = scene
        self._asset = {u"mesh": [], u"data": {}}
        self._material = {}

    def add_material(self, material):
        if material.id in self._material:
            return

        self._material[material.id] = material

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
            self.context.warning(u"Mesh '{0:s}' has no triangles. Pure line geometry not (yet) supported. Try extruding a little.".format(mesh.name), "geometry")
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
        meshName = safe_query_selector_id(mesh.name)
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
                image_src = export_image(mesh_textures[materialIndex]["image"], self._dir, self.context)
                if image_src:
                    # TODO: Image Sampling parameters
                    # FEATURE: Resize / convert / optimize texture
                    data.append(
                        {"type": "texture", "name": "diffuseTexture", "value": image_src, "wrap": None})
                if mesh_textures[materialIndex]["alpha"]:
                    data.append(
                        {"type": "float", "name": "transparency", "value": "0.002"})

            submeshName = meshName + "_" + materialName

            material_url = "#"
            if material:
                converted = Material.from_blender_material(material, self.context, self._dir)
                self.add_material(converted)
                material_url += converted.id
            else:
                self.add_material(DefaultMaterial)
                material_url += DefaultMaterial.id

            self._asset['mesh'].append(
                {"name": submeshName, "includes": meshName, "data": data, "shader": material_url})

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
            shader.setAttribute("script", material.script)
            if material.compute:
                shader.setAttribute("compute", material.compute)
            xml3d.appendChild(shader)
            for entry in material.data:
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
        stats = self.context.stats
        stats.assets.append({"url": self._path})

        with open(self._path, "w") as assetFile:
            self.saveXML(assetFile, stats)
            assetFile.close()
            os.path.getsize(self._path)
            stats.assets[0]["size"] = os.path.getsize(self._path)

        try:
            path_reference_copy(self.context.copy_set, self.copy_report)
        except PermissionError:
            print('ERROR: While copying textures: %s' % self.context.copy_set)
