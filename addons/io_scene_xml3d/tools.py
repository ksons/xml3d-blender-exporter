import mathutils
import re

IDENTITY = mathutils.Matrix.Identity(4)
EMPTY = mathutils.Matrix()
EMPTY.zero()


def is_identity(matrix):
    return matrix == IDENTITY


def is_empty(matrix):
    return matrix == EMPTY


def is_identity_scale(vector):
    return vector[0] == 1.0 and vector[1] == 1.0 and vector[2] == 1.0


def is_identity_translate(vector):
    return vector[0] == 0.0 and vector[1] == 0.0 and vector[2] == 0.0


def matrix_to_ccs_matrix3d(matrix):
    return "matrix3d(%s)" % ",".join(["%.6f,%.6f,%.6f,%.6f" % (col[0], col[1], col[2], col[3])
                                      for col in matrix.col])


def normalize_vec4(vec):
    # Vector.normalize does not take w into account
    if vec.length == 0.0:
        return vec
    return vec * (1.0 / vec.length)


def get_armature_object(obj):
    if len(obj.modifiers) == 1 and obj.modifiers[0].type == 'ARMATURE':
        return obj.modifiers[0].object
    return None


def safe_query_selector_id(id):
    return re.sub('[ \.]+', '-', id)


def write_generic_entry(doc, entry):
    entry_type = entry["type"]
    entry_element = doc.createElement(entry_type)

    if entry_type == "data":
        entry_element.setAttribute("src", entry["src"])
        return entry_element

    entry_element.setAttribute("name", entry["name"])

    value = entry["value"]
    value_str = None
    if entry_type == "int" or entry_type == "int4":
        value_str = ""
        for t in value:
            length = len(t) if isinstance(t, tuple) else 1
            fs = length * "%.d "
            value_str += fs % t
    elif entry_type == "texture":

        if entry["wrap"] is not None:
            entry_element.setAttribute("wrapS", entry["wrap"])
            entry_element.setAttribute("wrapT", entry["wrap"])

        img_element = doc.createElement("img")
        img_element.setAttribute("src", value)
        entry_element.appendChild(img_element)
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
        text_node = doc.createTextNode(value_str)
        entry_element.appendChild(text_node)
    return entry_element


class Vertex:
    index = None
    normal = None
    texcoord = None
    group_index = None
    group_weights = None

    def veckey4d(self, v):
        if v is None:
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8), round(v[2], 8), round(v[3], 8)))

    def veckey3d(self, v):
        if v is None:
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8), round(v[2], 8)))

    def veckey2d(self, v):
        if v is None:
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8)))

    def __init__(self, index, normal=None, uvs=None, group_index=None, group_weights=None):
        self.index = index
        self.normal = self.veckey3d(normal)
        self.texcoord = self.veckey2d(uvs)
        self.group_index = self.veckey4d(group_index)
        self.group_weights = self.veckey4d(group_weights)

    def __str__(self):
        return "i: " + str(self.index) + ", n: " + str(self.normal) + ", t: " + str(self.texcoord)

    # def __cmp__(self, other):
    #     "Currently not used as __eq__ has higher priority"
    #     # print("Compare")
    #     if self.index < other.index:
    #         return -1
    #     if self.index > other.index:
    #         return 1
    #
    #     if self.normal != other.normal:
    #         if self.normal is None:
    #             return -1
    #         if other.normal is None:
    #             return 1
    #         return cmp(self.normal, other.normal)
    #
    #     if self.texcoord != other.texcoord:
    #         if self.texcoord == None:
    #             return -1
    #         if other.texcoord == None:
    #             return 1
    #         return cmp(self.texcoord, other.texcoord)
    #
    #     return 0

    def __hash__(self):
        return self.index

    def __eq__(self, other):
        return self.index == other.index and self.normal == other.normal and self.texcoord == other.texcoord and self.group_index == other.group_index and self.group_weights == other.group_weights
