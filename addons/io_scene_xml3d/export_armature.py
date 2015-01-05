import os
from xml.dom.minidom import Document
from . import tools


class Armature:
    context = None
    id = ""
    data = None
    bone_map = None

    def __init__(self, name, context):
        self.id = name
        self.context = context
        self.data = []

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @staticmethod
    def create_from_blender(armature_object, armature_id, context):
        armature = Armature(armature_id, context)
        pose = armature_object.pose

        bone_map = {}
        armature.bone_map = {}
        locations = []
        rotations = []

        for i, pose_bone in enumerate(pose.bones):
            bone_map[pose_bone] = i
            armature.bone_map[pose_bone.name] = i
            armature_bone = pose_bone.bone
            # TODO: What information needs to be exported from the pose? Also: relative vs absolute...
            locations.append(armature_bone.head_local[:])
            rotations.append(pose_bone.rotation_quaternion[:])

        bone_parent = [(bone_map[bone.parent] if bone.parent in bone_map else -1) for bone in pose.bones]
        armature.data.append({"type": "int", "name": "bone_parent", "value": bone_parent})
        armature.data.append({"type": "float3", "name": "bind_location", "value": locations})
        armature.data.append({"type": "float4", "name": "bind_rotation", "value": rotations})
        return armature


class ArmatureLibrary:
    armatures = None
    url = None

    def __init__(self, context, url):
        self.armatures = []
        self.context = context
        self.url = url

    def get_armature(self, id):
        for armature in self.armatures:
            if armature.id == id:
                return armature
        return None

    def create_armature(self, armature_object):
        armature_id = tools.safe_query_selector_id(armature_object.data.name)
        armature = self.get_armature(armature_id)
        if not armature:
            armature = Armature.create_from_blender(armature_object, armature_id, self.context)
            self.armatures.append(armature)
        return armature, "./" + self.url + "#" + armature_id

    def add_armature(self, armature):
        if armature not in self.armatures:
            self.armatures.append(armature)
        return "./" + self.url + "#" + armature.id

    def __save_xml(self, file):
        doc = Document()
        xml3d = doc.createElement("xml3d")
        doc.appendChild(xml3d)

        for armature in self.armatures:
            shader = doc.createElement("data")
            shader.setAttribute("id", armature.id)
            for entry in armature.data:
                entry_element = tools.write_generic_entry(doc, entry)
                shader.appendChild(entry_element)
            xml3d.appendChild(shader)

        doc.writexml(file, "", "  ", "\n", "UTF-8")

    def save(self):
        if not len(self.armatures):
            return

        with open(self.url, "w") as armatureFile:
            self.__save_xml(armatureFile)
            armatureFile.close()
            size = os.path.getsize(self.url)

        self.context.stats.armatures.append({"name": "armature.xml", "size": size})
