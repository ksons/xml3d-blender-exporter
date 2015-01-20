import os
import mathutils
from xml.dom.minidom import Document
from . import tools


class ArmatureAnimation:
    id = ""
    context = None
    start_frame = 0.0

    def __init__(self, name, context):
        self.id = name
        self.context = context
        self.data = []
        self.start_frame = 0.0


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

    def get_config(self):
        if not len(self.animations):
            return None

        config = []
        for animation in self.animations:
            config.append({
                "name": self.id,
                "data": [
                    {"type": "float", "name": "animKey", "value": animation.start_frame, "class": "anim armature"}
                ]
            })
        return config

    @staticmethod
    def create_from_blender(armature_object, armature_id, context):
        armature = Armature(armature_id, context)
        pose = armature_object.pose

        # print(armature_object.name, armature_object.matrix_local)
        armature_matrix = armature_object.matrix_local
        # print(armature_matrix, tools.is_identity(armature_matrix))
        bone_map = {}
        armature.bone_map = {}
        bind_matrices = []

        for i, pose_bone in enumerate(pose.bones):
            bone_map[pose_bone] = i
            armature.bone_map[pose_bone.name] = i
            armature_bone = pose_bone.bone

            matrix = armature_matrix * armature_bone.matrix_local
            bind_matrices += tools.matrix_to_list(matrix.inverted())

        bone_parent = [(bone_map[bone.parent] if bone.parent in bone_map else -1) for bone in pose.bones]
        armature.data.append({"type": "int", "name": "bone_parent", "value": bone_parent})
        armature.data.append({"type": "float4x4", "name": "inverse_bind_matrix", "value": bind_matrices})
        Armature.create_animation(armature_object, armature, context)
        return armature

    @staticmethod
    def create_animation(armature_object, armature, context):
        if not (armature_object.animation_data and armature_object.animation_data.action):
            return

        action = armature_object.animation_data.action
        animation = ArmatureAnimation(tools.safe_query_selector_id(action.name), context)
        frame_min = animation.start_frame = action.frame_range[0]
        frame_max = action.frame_range[1]

        animation.data.append({"type": "float", "name": "minFrame", "value": frame_min})
        animation.data.append({"type": "float", "name": "maxFrame", "value": frame_max})
        animation.data.append({"type": "float", "name": "animKey", "value": "15"})

        keys = set()
        channels_rotation = []
        channels_location = []
        # Collect samples from keyframes
        for i, pose_bone in enumerate(armature_object.pose.bones):
            rotation_channels = find_channels(action, pose_bone.bone, "rotation_quaternion")
            # print(rotation_channels)
            channels_rotation.append(rotation_channels)
            for channel in rotation_channels:
                for keyframe in channel.keyframe_points:
                    keys.add(keyframe.co[0])

            location_channels = find_channels(action, pose_bone.bone, "location")
            channels_location.append(location_channels)
            for channel in location_channels:
                for keyframe in channel.keyframe_points:
                    keys.add(keyframe.co[0])

        samples = sorted(keys)
        # print("samples", len(samples), samples)

        for sample in samples:
            sampled_rotations = []
            sampled_locations = []
            for i, pose_bone in enumerate(armature_object.data.bones):
                local_matrix = get_local_bone_matrix(pose_bone)
                loc, rot, scl = local_matrix.decompose()

                bone_channels_location = channels_location[i]
                bone_channels_rotation = channels_rotation[i]
                vec = mathutils.Vector.Fill(3)
                quaternion = mathutils.Quaternion()
                for i, channel in enumerate(bone_channels_rotation):
                    quaternion[i] = channel.evaluate(sample)
                for j, channel in enumerate(bone_channels_location):
                    vec[j] = channel.evaluate(sample)
                sampled_rotations += mathutils.Vector((rot * quaternion)).yzwx[:]
                sampled_locations += (vec + loc)[:]

            animation.data.append({"type": "float4", "name": "rotation_quaternion", "key": str(sample), "value": sampled_rotations})
            animation.data.append({"type": "float3", "name": "location", "key": str(sample), "value": sampled_locations})

        armature.data.append({"type": "data", "src": "#" + animation.id})
        armature.animations.append(animation)
        context.stats.animations.append({"name": tools.safe_query_selector_id(action.name), "minFrame": frame_min, "maxFrame": frame_max})


def get_local_bone_matrix(bone):
    if not bone.parent:
        return bone.matrix_local
    else:
        parent_matrix = bone.parent.matrix_local
        return parent_matrix.inverted() * bone.matrix_local


# Stolen from three.js blender exporter (GNU GPL, https://github.com/mrdoob/three.js)
def find_channels(action, bone, channel_type):
    bone_name = bone.name
    ngroups = len(action.groups)
    result = []

    # TODO Catch assertion
    assert ngroups > 0, "This scene does not use action groups. Not considered yet."

    # Variant 1: channels grouped by bone names
    # only using variant 1. Have no case for variant 2 yet

    # Find the channel group for the given bone
    group_index = -1
    for i in range(ngroups):
        # print(action.groups[i].name, bone_name)
        if action.groups[i].name == bone_name:
            group_index = i

    # Get all desired channels in that group
    if group_index > -1:
        for channel in action.groups[group_index].channels:
            if channel_type in channel.data_path:
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
            armature_data = doc.createElement("data")
            armature_data.setAttribute("id", armature.id)
            for entry in armature.data:
                entry_element = tools.write_generic_entry(doc, entry)
                armature_data.appendChild(entry_element)
            xml3d.appendChild(armature_data)

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
