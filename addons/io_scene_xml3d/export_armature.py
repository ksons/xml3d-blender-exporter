import os
from xml.dom.minidom import Document
from . import tools


class ArmatureAnimation:
    id = ""
    context = None

    def __init__(self, name, context):
        self.id = name
        self.context = context
        self.data = []


class Armature:
    context = None
    id = ""
    data = None
    bone_map = None
    animations = None

    def __init__(self, name, context):
        self.id = name
        self.context = context
        self.data = []
        self.animations = []

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
        Armature.create_animation(armature_object, armature, context)
        return armature

    @staticmethod
    def create_animation(armature_object, armature, context):
        if not (armature_object.animation_data and armature_object.animation_data.action):
            return

        action = armature_object.animation_data.action
        animation = ArmatureAnimation(action.name, context)
        frame_min = action.frame_range[0]
        frame_max = action.frame_range[1]

        animation.data.append({"type": "float", "name": "minFrame", "value": frame_min})
        animation.data.append({"type": "float", "name": "maxFrame", "value": frame_max})

        keys = set()
        channels_rotation = []
        # Collect samples from keyframes
        for i, pose_bone in enumerate(armature_object.pose.bones):
            channels = find_channels(action, pose_bone.bone, "rotation_quaternion")
            print(len(channels))
            channels_rotation.append(channels)
            for channel in channels:
                for keyframe in channel.keyframe_points:
                    keys.add(keyframe.co[0])

        samples = sorted(keys)
        print("samples", len(samples), samples)

        for sample in samples:
            sampled_rotations = []
            for i, pose_bone in enumerate(armature_object.pose.bones):
                channels = channels_rotation[i]
                for channel in channels:
                    sampled_rotations.append(channel.evaluate(sample))

            animation.data.append({"type": "float4", "name": "rotation_quaternion", "key": str(sample), "value": sampled_rotations})

        armature.animations.append(animation)
        print(action)


# Stolen from three.js blender exporter (GNU GPL, https://github.com/mrdoob/three.js)
def find_channels(action, bone, channel_type):
    bone_name = bone.name
    ngroups = len(action.groups)
    result = []

    # Variant 1: channels grouped by bone names
    if ngroups > 0:

        # Find the channel group for the given bone
        group_index = -1
        for i in range(ngroups):
            if action.groups[i].name == bone_name:
                group_index = i

        # Get all desired channels in that group
        if group_index > -1:
            for channel in action.groups[group_index].channels:
                if channel_type in channel.data_path:
                    result.append(channel)

    # Variant 2: no channel groups, bone names included in channel names
    else:

        bone_label = '"%s"' % bone_name

        for channel in action.fcurves:
            data_path = channel.data_path
            if bone_label in data_path and channel_type in data_path:
                result.append(channel)

    return result


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
            data = doc.createElement("data")
            data.setAttribute("id", armature.id)
            for entry in armature.data:
                entry_element = tools.write_generic_entry(doc, entry)
                data.appendChild(entry_element)
            xml3d.appendChild(data)

            for animation in armature.animations:
                data = doc.createElement("data")
                data.setAttribute("id", animation.id)
                for entry in animation.data:
                    entry_element = tools.write_generic_entry(doc, entry)
                    data.appendChild(entry_element)
                xml3d.appendChild(data)

        doc.writexml(file, "", "  ", "\n", "UTF-8")

    def save(self):
        if not len(self.armatures):
            return

        with open(self.url, "w") as armatureFile:
            self.__save_xml(armatureFile)
            armatureFile.close()
            size = os.path.getsize(self.url)

        self.context.stats.armatures.append({"name": "armature.xml", "size": size})
