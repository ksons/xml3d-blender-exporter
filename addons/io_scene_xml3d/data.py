from enum import Enum
from .tools import matrix_to_list


class DataType(Enum):
    float = "float"
    float2 = "float2"
    float3 = "float3"
    float4 = "float4"
    float16 = "float4x4"
    int = "int"
    int4 = "int4"
    bool = "bool"
    texture = "texture"
    data = "data"


class DataEntry:
    name = ""
    type = None,
    key = None
    value = []
    class_name = None

    def __init__(self, name, _type, value, key=None, class_name=None):
        self.name = name
        self.type = _type
        self.value = value
        self.key = key
        self.class_name = class_name

    def __str__(self):
        return self.type.name + ": " + self.name

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @staticmethod
    def create_from_matrix(name, matrix):
        return DataEntry(name, DataType.float16, matrix_to_list(matrix))


class TextureEntry(DataEntry):
    wrap_type = None
    src = ""

    def __init__(self, name, src, wrap_type=None, key=None):
        super().__init__(name, DataType.texture, None, key)
        self.src = src
        self.wrap_type = wrap_type


class DataReference(DataEntry):
    src = ""

    def __init__(self, src):
        super().__init__(None, DataType.data, None)
        self.src = src

    def __str__(self):
        return self.type.name + ": " + self.src


def write_generic_entry(doc, entry):
    entry_type = entry.type
    entry_element = doc.createElement(entry_type.value)

    if entry_type == DataType.data:
        entry_element.setAttribute("src", entry.src)
        return entry_element

    entry_element.setAttribute("name", entry.name)
    if entry.key:
        entry_element.setAttribute("key", entry.key)

    value = entry.value
    value_str = None
    if entry_type in {DataType.int, DataType.int4}:
        value_str = ""
        for t in value:
            length = len(t) if isinstance(t, tuple) else 1
            fs = length * "%.d "
            value_str += fs % t
    elif entry_type == DataType.texture:

        if entry.wrap_type is not None:
            entry_element.setAttribute("wrapS", entry.wrap_type)
            entry_element.setAttribute("wrapT", entry.wrap_type)

        img_element = doc.createElement("img")
        img_element.setAttribute("src", entry.src)
        entry_element.appendChild(img_element)
    else:
        if not isinstance(value, list):
            value_str = str(value)
        else:
            value_str = " ".join(str(v) for v in value)

    if value_str:
        text_node = doc.createTextNode(value_str)
        entry_element.appendChild(text_node)
    return entry_element


def write_generic_entry_html(writer, entry):
    element_name = entry.type.value
    writer.start_element(element_name, name=entry.name)
    if entry.class_name:
        writer.attribute("class", entry.class_name)
    writer.content(str(entry.value))
    writer.end_element(element_name)
