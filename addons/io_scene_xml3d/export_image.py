import os
import bpy
from . import png
from . import tools
from bpy_extras.io_utils import path_reference

IMG_FORMAT_2_EXTENSION = dict(JPEG=".jpg", PNG=".png")

def export_image(image, context):
    if image in context.images:
        return context.images[image]

    if image.source not in {'FILE', 'VIDEO'}:
        context.warning(u"Image '{0:s}' is of source '{1:s}' which is not (yet) supported. Using default ...".format(image.name, image.source), "texture")
        return None

    # Create texture directory if it does not exist
    texture_path = os.path.join(context.base_url, "textures")
    os.makedirs(texture_path, exist_ok=True)

    if image.file_format in {'PNG', 'JPEG'}:
        if image.packed_file:
            image_src = save_packed_image(image, context)
        else:
            image_src = copy_image(image, context)
    else:
        image_src = convert_and_export(image, texture_path, context)

    # Save the image to not export it again
    context.images[image] = image_src
    return image_src


def save_packed_image(image, context):
    image_data = image.packed_file.data
    image_name = tools.safe_filename_from_image(image) + IMG_FORMAT_2_EXTENSION[image.file_format]

    image_src = os.path.join("textures", image_name)
    file_path = os.path.join(context.base_url, image_src)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as image_file:
            image_file.write(image_data)
            image_file.close()

    # Save file and file size in stats
    context.stats.textures.append({"name": image_name, "size": os.path.getsize(file_path)})

    image_src = image_src.replace('\\', '/')
    return image_src


def copy_image(image, context):
    base_src = os.path.dirname(bpy.data.filepath)
    filepath_full = bpy.path.abspath(image.filepath, library=image.library)
    image_src = path_reference(filepath_full, base_src, context.base_url, 'COPY', "textures", context.copy_set, image.library)
    # Stats are written when files have been copied (see Context.finalize)
    return image_src


def convert_and_export(image, texture_path, context):
    image_name = tools.safe_filename_from_image(image)
    # todo: we should copy the texture if it is already a png image
    file_name = image_name + ".png"
    image_src = os.path.join("textures", file_name)
    file_path = os.path.join(texture_path, file_name)
    width = image.size[0]
    height = image.size[1]
    pixels = [x * 255 for x in list(image.pixels)]
    pixels = [pixels[r * width * 4:(r + 1) * width * 4] for r in range(0, height)][::-1]
    w = png.Writer(width, height, alpha=True)
    with open(file_path, "wb") as image_file:
        w.write_packed(image_file, pixels)
        image_file.close()

    # Save file and file size in stats
    context.stats.textures.append({"name": file_name, "size": os.path.getsize(file_path)})

    image_src = image_src.replace('\\', '/')
    return image_src
