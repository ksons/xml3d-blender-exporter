from .tools import Vertex
from .data import DataEntry, DataType
import operator
import mathutils


def export_tessfaces(mesh, armature_info, context):
    if not len(mesh.tessfaces):
        context.warning(u"Mesh '{0:s}' has no triangles. Pure line geometry not (yet) supported. Try extruding a little.".format(mesh.name), "geometry")
        return None, None

    material_count = len(mesh.materials)
    store_barycentric_coordinates = True


    # Mesh indices:
    # For each material allocate an array
    # @UnusedVariable
    indices = [[] for m in range(1 if material_count == 0 else material_count)]

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

            group_index, group_weights = get_bones_and_weights(mesh.vertices[vertexIndex].groups, armature_info)

            print(i)
            mv = Vertex(vertexIndex, normal, uv_vertex, group_index, group_weights, i if store_barycentric_coordinates else -1)

            index, added = append_unique(vertex_dict, mv)
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


def get_bones_and_weights(groups, armature_info):
    if not (len(groups) and armature_info):
        return None, None

    weights = []
    group_index = mathutils.Vector.Fill(4, -1)
    group_weights = mathutils.Vector.Fill(4, 0)

    sum_weights = 0.0
    for group in groups:
        index = group.group
        name = armature_info['vertex_groups'][index].name

        if len(name) == 0:
            print("No name")

        if name not in armature_info['bone_map']:
            # print("not in bone_map:", name)
            continue

        sum_weights += group.weight
        weights.append((group.weight, armature_info['bone_map'][name]))

    if sum_weights > 0:
        # Now take the four with the highest influence
        weights.sort(key=operator.itemgetter(0), reverse=True)
        # Recalculate overall weight
        sum_weights = 0.0
        weight_count = len(weights)
        for j in range(min(4, weight_count)):
            weight = weights[j]
            group_index[j] = weight[1]
            group_weights[j] = weight[0]
            sum_weights += weight[0]

        group_weights *= 1.0 / sum_weights

    else:
        print("Found vertex without weights")

    return group_index, group_weights


def append_unique(mlist, value):
    if value in mlist:
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True


def get_vertex_attributes(mesh, vertices):
    content = []
    positions = []
    normals = []
    texcoord = []
    barycentric = []
    group_weights = []
    group_indices = []

    has_texcoords = vertices[0].texcoord
    has_weights = vertices[0].group_weights
    has_barycentric = vertices[0].bc != -1
    for v in vertices:
        positions += mesh.vertices[v.index].co[:]
        normals += v.normal[:]
        if has_texcoords:
            texcoord += v.texcoord[:]
        if has_weights:
            group_weights += v.group_weights[:] if v.group_weights else [0, 0, 0, 0]
            group_indices += v.group_index[:] if v.group_index else [0, 0, 0, 0]

        if has_barycentric:
            if v.bc == 0:
                barycentric += [1, 0, 0]
            elif v.bc == 1 or v.bc == 3:
                barycentric += [0, 1, 0]
            else:
                barycentric += [0, 0, 1]



    content.append(DataEntry("position", DataType.float3, positions))
    content.append(DataEntry("normal", DataType.float3, normals))
    if has_texcoords:
        content.append(DataEntry("texcoord", DataType.float2, texcoord))

    if has_barycentric:
        content.append(DataEntry("barycentric", DataType.float3, barycentric))


    if has_weights:
        content.append(DataEntry("bone_index", DataType.int4, group_indices))
        content.append(DataEntry("bone_weight", DataType.float4, group_weights))

    return content
