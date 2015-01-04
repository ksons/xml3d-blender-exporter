import os
from xml.dom.minidom import Document
from . import tools


class Armature:
    context = None
    id = ""
    data = None

    def __init__(self, name, context):
        self.id = name
        self.context = context
        self.data = []


class ArmatureLibrary:
    armatures = None
    url = None

    def __init__(self, context, url):
        self.armatures = []
        self.context = context
        self.url = url

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
