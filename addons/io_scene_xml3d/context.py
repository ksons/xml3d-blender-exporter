import json


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
    stats = Stats(assets=[], lights=0, views=0, groups=0, materials=0, textures=0, meshes=[], warnings=[])
    base_path = None
    copy_set = set()

    def warning(self, message, category=None, issue=None, obj=None):
        self.stats.warnings.append({"message": message, "issue": issue, "object": obj, "category": category})
        print("Warning:", message)

    def set_base_path(self, base_path):
        self.base_path = base_path
