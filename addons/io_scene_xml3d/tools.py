import mathutils, json

IDENTITY = mathutils.Matrix.Identity(4)

def is_identity(matrix):
    return matrix == IDENTITY

def is_identity_scale(vector):
    return vector[0] == 1.0 and vector[1] == 1.0 and vector[2] == 1.0

def is_identity_translate(vector):
    return vector[0] == 0.0 and vector[1] == 0.0 and vector[2] == 0.0


class Stats(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def join(self, other):
        pass
        for key, val in other.__dict__.items():
            if key in self.__dict__:
                self.__dict__[key] += val # You can custom it here
            else:
                self.__dict__[key] = val

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Vertex :
    index = None
    normal = None
    texcoord = None
    color = None

    def veckey3d(self, v) :
        if v == None :
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8), round(v[2], 8)))

    def veckey2d(self, v):
        if v == None:
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8)))

    def __init__(self, index, normal = None, uvs = None, color = None):
        self.index = index
        self.normal = self.veckey3d(normal)
        self.texcoord = self.veckey2d(uvs)

    def __str__( self ) :
        return "i: " + str(self.index) + ", n: " + str(self.normal) + ", t: " + str(self.texcoord)

    def __cmp__(self, other):
        "Currently not used as __eq__ has higher priority"
        #print("Compare")
        if self.index < other.index:
            return -1;
        if self.index > other.index:
            return 1;

        if self.normal != other.normal:
            if self.normal == None:
                return -1;
            if other.normal == None:
                return 1;
            return cmp(self.normal, other.normal)

        if self.texcoord != other.texcoord:
            if self.texcoord == None:
                return -1;
            if other.texcoord == None:
                return 1;
            return cmp(self.texcoord, other.texcoord)

        return 0;

    def __hash__( self ) :
        return self.index

    def __eq__(self, other):
        return self.index == other.index and self.normal == other.normal and self.texcoord == other.texcoord