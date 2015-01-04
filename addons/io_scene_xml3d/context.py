import json
import os
from .export_material import MaterialLibrary
from .export_armature import ArmatureLibrary
from bpy_extras.io_utils import path_reference_copy


class Stats(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def join(self, other):
        pass
        for key, val in other.__dict__.items():
            if key in self.__dict__:
                self.__dict__[key] += val  # You can custom it here
            else:
                self.__dict__[key] = val

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Context():
    stats = Stats(assets=[], lights=0, views=0, groups=0, materials=[], textures=[], meshes=[], armatures=[], warnings=[], scene=None)
    base_url = None
    copy_set = set()
    materials = None
    scene = None

    def __init__(self, base_url, scene):
        self.base_url = base_url
        self.scene = scene
        self.materials = MaterialLibrary(self, base_url + "/materials.xml")
        self.armatures = ArmatureLibrary(self, base_url + "/armatures.xml")

    def warning(self, message, category=None, issue=None, obj=None):
        self.stats.warnings.append({"message": message, "issue": issue, "object": obj, "category": category})
        print("Warning:", message)

    def __copy_report(self, msg):
        self.warning(msg.capitalize(), "texture")

    def finalize(self):
        self.armatures.save()
        self.materials.save()
        try:
            path_reference_copy(self.copy_set, self.__copy_report)
        except PermissionError:
            self.warning('ERROR: While copying textures: %s' % self.copy_set, "textures")

        for key, value in self.copy_set:
            try:
                size = os.path.getsize(value)
            except FileNotFoundError:
                size = 0
            self.stats.textures.append({
                "name": os.path.basename(value),
                "size": size

            })
