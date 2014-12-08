import mathutils, os
from xml.dom.minidom import Document, Element
from .tools import Vertex, Stats


def appendUnique(mlist, value):
    if value in mlist :
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True

class AssetExporter:
	def __init__(self,path, scene):
		self._path = path
		self._scene = scene
		self._asset = { u"mesh": [], u"data": {}}
		self._material = {}

	def add_default_material(self):
		if "defaultMaterial" in self._material:
			return

		data = []
		data.append({ "type": "float3", "name": "diffuseColor", "value": "0.8 0.8 0.8"})
		data.append({ "type": "float3", "name": "specularColor", "value": "1.0 1.0 0.1"})
		data.append({ "type": "float", "name": "ambientIntensity", "value": "0.5" })

		self._material["defaultMaterial"] = { "content": { "data": data }, "script": "urn:xml3d:shader:phong" }


	def add_material(self, material):
		materialName = material.name
		if materialName in self._material:
			return
		data = []
		data.append({ "type": "float3", "name": "diffuseColor", "value": [e * material.diffuse_intensity for e in material.diffuse_color]})
		data.append({ "type": "float3", "name": "specularColor", "value": [tuple(material.specular_color)] })
		data.append({ "type": "float", "name": "ambientIntensity", "value": material.ambient })

		self._material[materialName] = { "content": { "data": data }, "script": "urn:xml3d:shader:phong" }

	def addMesh(self, meshObject, derivedObject):
		if derivedObject:
			for obj, mat in derivedObject:
				print(obj, mat)
				if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
					continue

				try:
					data = obj.to_mesh(self._scene, True, 'RENDER')
				except:
					data = None

				if data:
					self.addMeshData(data)

		else:
			self.addMeshData(meshObject.data)

	def addMeshData(self, mesh):
		if len(mesh.polygons) == 0 :
			return

		meshName = mesh.name
		materialCount = len(mesh.materials)

		#print("Writing mesh %s" % meshName)

		# Mesh indices

		# Speichert für jedes Material die entsprechenden Vertexindices
		indices = [[] for m in range(1 if materialCount == 0 else materialCount)] #@UnusedVariable
		# Speichert alle Vertices des Meshes in einer aufbereiteten Form
		vertices = []
		# Stellt sicher, dass keine Vertices doppelt aufgenommen werden
		vertex_dict = {}

		# print("Faces: %i" % len(mesh.polygons))

		uvTexture = mesh.uv_textures.active
		if uvTexture :
			pass
			#print("Active UV Texture: " + uvTexture.name)

        #meshTextureFaceLayerData = None
       #if mesh.tessface_uv_textures.active :
       #    meshTextureFaceLayerData = mesh.tessface_uv_textures.active.data

		for faceIndex, face in enumerate(mesh.polygons) :
			mv = None
			uvFace = None
			#if uvTexture and uvTexture.data[faceIndex] :
		 	#	uvFaceData = uvTexture.data[faceIndex]
		 	#	uvFace = uvFaceData.uv1, uvFaceData.uv2, uvFaceData.uv3, uvFaceData.uv4

			newFaceVertices = []

			for i, vertexIndex in enumerate(face.vertices):
				if face.use_smooth:
					#if uvFace:
					#	mv = Vertex(vertexIndex, mesh.vertices[vertexIndex].normal, uvFace[i])
					#else:
					mv = Vertex(vertexIndex, mesh.vertices[vertexIndex].normal, None)
				else :
					#if uvFace :
					#	meshTexturePolyLayer = mesh.uv_textures.active
					#	mv = Vertex(vertexIndex, face.normal, uvFace[i])
					#else:
					mv = Vertex(vertexIndex, face.normal)

				index, added = appendUnique(vertex_dict, mv)
				newFaceVertices.append(index)
				#print("enumerate: %d -> %d (%d)" % (i, vertexIndex, index))
				if added :
					vertices.append(mv)

			if len(newFaceVertices) == 3 :
				#print("3 vertices found")
				for vertexIndex in newFaceVertices :
					indices[face.material_index].append(vertexIndex)
			elif len(newFaceVertices) == 4 :
				#print("4 vertices found")
				indices[face.material_index].append(newFaceVertices[0])
				indices[face.material_index].append(newFaceVertices[1])
				indices[face.material_index].append(newFaceVertices[2])
				indices[face.material_index].append(newFaceVertices[2])
				indices[face.material_index].append(newFaceVertices[3])
				indices[face.material_index].append(newFaceVertices[0])


		content = []
		# Vertex positions and normals
		positions = []
		normals = []
		for v in vertices :
			positions.append(tuple(mesh.vertices[v.index].co))
			normals.append(tuple(v.normal))

		content.append({ "type": "float3", "name": "position", "value": positions})
		content.append({ "type": "float3", "name": "normal", "value": normals})

		self._asset['data'][meshName] = { "content": content }
#		print("materialIndex", len(indices[0]))

 #        # Vertex texCoord
 #        if uvTexture :
 #            value_list = []
 #            for v in vertices :
 #                if v.texcoord :
 #                    value_list.append("%.6f %.6f" % tuple(v.texcoord))
 #                else :
 #                    value_list.append("0.0 0.0")

 #            valueElement = self. doc.createFloat2Element(None, "texcoord")
 #            valueElement.setValue(' '.join(value_list))
 #            data.appendChild(valueElement);



		for materialIndex, material in enumerate(mesh.materials if materialCount else [None]) :
			print(materialIndex)
			if len(indices[materialIndex]) == 0:
				continue

			materialName = material.name if material else "defaultMaterial"

			data = []
			data.append({ "type": "int", "name": "index", "value": indices[materialIndex]})

			submeshName = meshName + "_" + materialName
			self._asset['mesh'].append( {"name": submeshName, "includes": meshName, "data": data, "shader": "#"+materialName })

			if material:
				self.add_material(material)
			else:
				self.add_default_material()

	def saveXML(self, f, stats):
		doc = Document()
		xml3d = doc.createElement("xml3d")
		doc.appendChild(xml3d)

		asset = doc.createElement("asset")
		asset.setAttribute("id", "root")
		xml3d.appendChild(asset)

		for name, material in self._material.items():
			shader = doc.createElement("shader")
			shader.setAttribute("id", name)
			shader.setAttribute("script", material["script"])
			xml3d.appendChild(shader)
			content = material["content"]
			for entry in content["data"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry)
				shader.appendChild(entryElement)
			stats.materials += 1

		for name, value in self._asset["data"].items():
			assetData = doc.createElement("assetdata")
			assetData.setAttribute("name", name)
			asset.appendChild(assetData)
			for entry in value["content"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry)
				assetData.appendChild(entryElement)

		for mesh in self._asset["mesh"]:
			assetMesh = doc.createElement("assetmesh")
			assetMesh.setAttribute("name", mesh["name"])
			assetMesh.setAttribute("includes", mesh["includes"])
			assetMesh.setAttribute("shader", mesh["shader"])
			asset.appendChild(assetMesh)
			for entry in mesh["data"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry)
				assetMesh.appendChild(entryElement)
			stats.meshes.append(mesh["name"])

		doc.writexml(f, "", "  ", "\n", "UTF-8")

	def writeGenericContent(doc, entry):
		entryElement = doc.createElement(entry["type"])
		entryElement.setAttribute("name", entry["name"])
		value = entry["value"]
		valueStr = ""
		if (entry["type"] == "int"):
			valueStr = " ".join(str(e) for e in value)
		else:
			if not isinstance(value, list):
				valueStr = str(value)
			else:
				for t in value:
					length = len(t) if isinstance(t,tuple) else 1
					fs = length* "%.6f "
					valueStr += fs % t

		textNode = doc.createTextNode(valueStr)
		entryElement.appendChild(textNode)
		return entryElement

	def save(self):
		stats = Stats(materials = 0, meshes = [], assets=[])
		stats.assets.append({ "url": self._path })

		with open (self._path, "w") as assetFile:
			self.saveXML(assetFile, stats)
			assetFile.close()
			os.path.getsize(self._path)
			stats.assets[0]["size"] = os.path.getsize(self._path)
			return stats
