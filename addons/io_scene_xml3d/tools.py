import mathutils
import re
import itertools
from bpy.path import display_name_from_filepath

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


def matrix_to_list(matrix):
    result = list(itertools.chain(*matrix.transposed()))
    return result


def normalize_vec4(vec):
    # Vector.normalize does not take w into account
    if vec.length == 0.0:
        return vec
    return vec * (1.0 / vec.length)


def get_armature_object(obj, context):
    if not context.options.asset_export_armature:
        return None, None
    if len(obj.modifiers) == 1 and obj.modifiers[0].type == 'ARMATURE':
        return obj.modifiers[0].object, None
    if 'ARMATURE' in [m.type for m in obj.modifiers]:
        # TODO: Add issue
        return None, "There are multiple modifiers on obj '%s'. Armature export with multiple modifiers is not (yet) supported. Armature will not be exported." % obj.name
    return None, None


def escape_html_id(_id):
    # HTML: ID tokens must begin with a letter ([A-Za-z])
    if not _id[:1].isalpha():
        _id = "a" + _id

    # and may be followed by any number of letters, digits ([0-9]),
    # hyphens ("-"), underscores ("_"), colons (":"), and periods (".")
    _id = re.sub('[^a-zA-Z0-9-_:\.]+', '-', _id)
    return _id


def safe_query_selector_id(_id):
    return re.sub('[ \|\.]+', '-', escape_html_id(_id))


def safe_filename_from_image(image):
    # is it actually possible for image.name to be empty?
    # Blender seams to always enumerate "undefined" if no name is specified
    # defaults to file name which is what we would use anyway
    image_name = image.name if image.name != "" else display_name_from_filepath(image.filepath)
    # a name in blender is allowed to contain any utf8 character
    # filesystems are not that permissive
    # to be as compatible as possible we replace the most common invalid characters with an underscore
    # there are many other invalid names like reserved DOS names but handling all edge cases is not feasible
    image_name = re.sub(r"\\|\*|\.|\"|\/|\[|\]|:|;|#|\||=|,|<|>", "_", image_name)
    return image_name


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
