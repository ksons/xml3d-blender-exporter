import os
import operator
import mathutils
from xml.dom.minidom import Document
from .export_material import Material, DefaultMaterial, export_image
from bpy_extras.io_utils import create_derived_objects, free_derived_objects
from . import tools


def appendUnique(mlist, value):
    if value in mlist:
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True


class Asset:
    id = ""
    meshes = None
    data = None
    sub_assets = None
    ref_assets = None
    matrix = None
    src = None

    def __init__(self, id_=None, name=None, matrix=None, src=None):
        self.id = id_
        self.name = name
        self.matrix = matrix
        self.src = src
        self.meshes = []
        self.data = {}
        self.sub_assets = {}
        self.ref_assets = []


class AssetExporter:
    context = None
    name = ""

    def __init__(self, name, context, path, scene):
        self.name = name
        self.context = context
        self._path = path
        self._dir = os.path.dirname(path)
        self._scene = scene
        self.asset = Asset(id_="root")
        self._material = {}

    def add_material(self, material):
        url = self.context.materials.add_material(material)
        if url is not None:
            # TODO: Good URL handling
            return "../materials.xml#" + material.id

        if material.id not in self._material:
            self._material[material.id] = material
        return "#" + material.id

    def add_asset(self, obj):
        base_matrix = obj.matrix_basis.inverted()
        free, derived_objects = create_derived_objects(self._scene, obj)
        if derived_objects is None:
            return

        asset_configs = {
            "subconfigs": []
        }
        for derived_object, matrix in derived_objects:
            if derived_object.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                continue
            subasset_configs = self.add_subasset(derived_object, base_matrix * matrix)
            asset_configs["subconfigs"].append(subasset_configs)

        if free:
            free_derived_objects(obj)
        return asset_configs

    def add_subasset(self, derived_object, matrix):
        name = tools.safe_query_selector_id(derived_object.name)

        if name in self.asset.sub_assets:
            ref_asset = Asset(src="#" + name, matrix=matrix)
            self.asset.ref_assets.append(ref_asset)
            return

        sub_asset = Asset(name=name, matrix=matrix.copy())
        subasset_config = {"name": name}

        armature_info = None
        armature_object = tools.get_armature_object(derived_object)
        if armature_object is not None:
            armature, armature_url = self.context.armatures.create_armature(armature_object)
            armature_info = {
                "vertex_groups": derived_object.vertex_groups,
                "bone_map": armature.bone_map,
                "src": "../armatures.xml#" + armature.id,
                "name": armature.id
            }
            armature_config = armature.get_config()
            if armature_config:
                subasset_config["armature"] = armature_config

        try:
            apply_modifiers = armature_object is None
            mesh = derived_object.to_mesh(self._scene, apply_modifiers, 'RENDER', True, False)
        except:
            mesh = None

        if mesh:
            self.add_mesh_data(sub_asset, mesh, armature_info)
            self.asset.sub_assets[name] = sub_asset

        return subasset_config

    def get_bones_and_weights(self, groups, armature_info):
        if not (len(groups) and armature_info):
            return None, None

        weights = []
        group_index = mathutils.Vector.Fill(4, -1)
        group_weights = mathutils.Vector.Fill(4, 0)
        for group in groups:
            index = group.group
            weight = group.weight
            name = armature_info['vertex_groups'][index].name
            weights.append((index, weight, name))

        weights.sort(key=operator.itemgetter(1), reverse=True)

        for j in range(4):
            if j < len(weights):
                w = weights[j]

                # TODO: Mapping by name. However, vertex groups can also be explicitly assigned
                if w[2] in armature_info['bone_map']:
                    group_index[j] = armature_info['bone_map'][w[2]]
                    group_weights[j] = w[1]

        # TODO: Should we normalize? Source is not necessarily normalized.
        return group_index, group_weights

    def export_tessfaces(self, mesh, armature_info):
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
                normal = mesh.vertices[vertexIndex].normal if face.use_smooth else face.normal
                uv_vertex = uv_vertices[i][0] if uv_data else None

                group_index, group_weights = self.get_bones_and_weights(mesh.vertices[vertexIndex].groups, armature_info)

                mv = tools.Vertex(vertexIndex, normal, uv_vertex, group_index, group_weights)

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
            if material and material.use_face_texture:
                try:
                    textures[i] = {"image": mesh.tessface_uv_textures[i].data[
                        0].image, "alpha": material.use_face_texture_alpha}
                except:
                    textures[i] = None
        return textures

    def add_mesh_data(self, asset, mesh, armature_info):
        meshName = tools.safe_query_selector_id(mesh.name)
        materialCount = len(mesh.materials)

        # Export based on tess_faces:
        vertices, indices = self.export_tessfaces(mesh, armature_info)

        if not (vertices and indices):
            return

        content = []
        positions = []
        normals = []
        texcoord = []
        group_weights = []
        group_indices = []
        compute = None
        includes = None

        has_texcoords = vertices[0].texcoord
        has_weights = vertices[0].group_weights
        for v in vertices:
            positions += mesh.vertices[v.index].co[:]
            normals += v.normal[:]
            if has_texcoords:
                texcoord += v.texcoord[:]
            if has_weights:
                group_weights += v.group_weights[:]
                group_indices += v.group_index[:]

        content.append(
            {"type": "float3", "name": "position", "value": positions})
        content.append({"type": "float3", "name": "normal", "value": normals})
        if has_weights:
            content.append({"type": "int4", "name": "bone_index", "value": group_indices})
            content.append({"type": "float4", "name": "bone_weight", "value": group_weights})
            armature_name = armature_info['name']
            # content.append()
            # asset.data[armature_name] = {"src": armature_info["src"], "includes": None, "compute": None}
            asset.data[armature_name] = {"content": [{"type": "data", "src": armature_info["src"]}, {"type": "float", "name": "animKey", "value": 1.0}], "includes": None, "compute": None}
            compute = "dataflow['../common/xflow/data-flows.xml#blenderSkinning']"
            includes = armature_info['name']
        if has_texcoords:
            content.append(
                {"type": "float2", "name": "texcoord", "value": texcoord})

        asset.data[meshName] = {"content": content, "compute": compute, "includes": includes}

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
                image_src = export_image(mesh_textures[materialIndex]["image"], self.context)
                if image_src:
                    # TODO: Image Sampling parameters
                    # FEATURE: Resize / convert / optimize texture
                    data.append(
                        {"type": "texture", "name": "diffuseTexture", "value": "../" + image_src, "wrap": None})
                if mesh_textures[materialIndex]["alpha"]:
                    data.append(
                        {"type": "float", "name": "transparency", "value": "0.002"})

            submeshName = meshName + "_" + materialName

            if material:
                converted = Material.from_blender_material(material, self.context, self._dir)
                material_url = self.add_material(converted)
            else:
                material_url = self.add_material(DefaultMaterial)

            asset.meshes.append(
                {"name": submeshName, "includes": meshName, "data": data, "shader": material_url})

    def saveXML(self, f, stats):
        doc = Document()
        xml3d = doc.createElement("xml3d")
        doc.appendChild(xml3d)
        self.asset_xml(self.asset, xml3d)
        doc.writexml(f, "", "  ", "\n", "UTF-8")

    def asset_xml(self, asset, parent):
        doc = parent.ownerDocument

        asset_element = doc.createElement("asset")
        parent.appendChild(asset_element)

        if asset.id:
            asset_element.setAttribute("id", asset.id)
        if asset.name:
            asset_element.setAttribute("name", asset.name)
        if asset.matrix and not tools.is_identity(asset.matrix):
            asset_element.setAttribute("style", "transform: %s;" % tools.matrix_to_ccs_matrix3d(asset.matrix))
        if asset.src:
            asset_element.setAttribute("src", asset.src)
            return

        for name, value in asset.data.items():
            asset_data = doc.createElement("assetdata")
            asset_data.setAttribute("name", name)

            if 'src' in value:
                asset_data.setAttribute("src", value["src"])

            if 'includes' in value and value["includes"]:
                asset_data.setAttribute("includes", value["includes"])

            if 'compute' in value and value["compute"]:
                asset_data.setAttribute("compute", value["compute"])

            asset_element.appendChild(asset_data)
            if 'content' not in value:
                return

            for entry in value["content"]:
                entryElement = tools.write_generic_entry(doc, entry)
                asset_data.appendChild(entryElement)

        for mesh in asset.meshes:
            asset_mesh = doc.createElement("assetmesh")
            asset_mesh.setAttribute("name", mesh["name"])
            asset_mesh.setAttribute("includes", mesh["includes"])
            asset_mesh.setAttribute("shader", mesh["shader"])
            if "transform" in mesh:
                asset_mesh.setAttribute("style", "transform: %s;" % mesh["transform"])

            asset_element.appendChild(asset_mesh)
            for entry in mesh["data"]:
                entryElement = tools.write_generic_entry(doc, entry)
                asset_mesh.appendChild(entryElement)

        for sub_asset in asset.sub_assets.values():
            self.asset_xml(sub_asset, asset_element)

        for ref_asset in asset.ref_assets:
            self.asset_xml(ref_asset, asset_element)

    def save(self):
        stats = self.context.stats

        with open(self._path, "w") as assetFile:
            self.saveXML(assetFile, stats)
            assetFile.close()
            size = os.path.getsize(self._path)

        stats.assets.append({"url": self._path, "size": size, "name": self.name})
