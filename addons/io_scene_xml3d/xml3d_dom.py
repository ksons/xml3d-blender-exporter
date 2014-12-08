# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

try:
	from xml.dom.minidom import Document, Element
except:
	print("Error! Could not find XML modules!")

class XML3DDocument( Document ):
	""" An XML3D Document ( xml3d.org ) """

	def createXml3dElement( self, id_ = None, height_ = None, width_ = None, activeView_ = None ):
		#print 'Creating element  xml3d'
		e = _Xml3dElement( self, id_, height_, width_, activeView_ )
		#e.ownerDocument = self
		return e

	def createDataElement( self, id_ = None, map_ = None, expose_ = None, src_ = None, script_ = None ):
		#print 'Creating element  data'
		e = _DataElement( self, id_, map_, expose_, src_, script_ )
		#e.ownerDocument = self
		return e

	def createDefsElement( self, id_ = None ):
		#print 'Creating element  defs'
		e = _DefsElement( self, id_ )
		#e.ownerDocument = self
		return e

	def createGroupElement( self, id_ = None, visible_ = None, transform_ = None, shader_ = None ):
		#print 'Creating element  group'
		e = _GroupElement( self, id_, visible_, transform_, shader_ )
		#e.ownerDocument = self
		return e

	def createMeshElement( self, id_ = None, visible_ = None, type_ = None, src_ = None ):
		#print 'Creating element  mesh'
		e = _MeshElement( self, id_, visible_, type_, src_ )
		#e.ownerDocument = self
		return e

	def createTransformElement( self, id_ = None, translation_ = None, scale_ = None, rotation_ = None, center_ = None, scaleOrientation_ = None ):
		#print 'Creating element  transform'
		e = _TransformElement( self, id_, translation_, scale_, rotation_, center_, scaleOrientation_ )
		#e.ownerDocument = self
		return e

	def createShaderElement( self, id_ = None, script_ = None, src_ = None ):
		#print 'Creating element  shader'
		e = _ShaderElement( self, id_, script_, src_ )
		#e.ownerDocument = self
		return e

	def createLightElement( self, id_ = None, visible_ = None, shader_ = None, global_ = None, intensity_ = None ):
		#print 'Creating element  light'
		e = _LightElement( self, id_, visible_, shader_, global_, intensity_ )
		#e.ownerDocument = self
		return e

	def createLightshaderElement( self, id_ = None, script_ = None, src_ = None ):
		#print 'Creating element  lightshader'
		e = _LightshaderElement( self, id_, script_, src_ )
		#e.ownerDocument = self
		return e

	def createScriptElement( self, id_ = None, src_ = None, type_ = None ):
		#print 'Creating element  script'
		e = _ScriptElement( self, id_, src_, type_ )
		#e.ownerDocument = self
		return e

	def createFloatElement( self, id_ = None, name_ = None ):
		#print 'Creating element  float'
		e = _FloatElement( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createFloat2Element( self, id_ = None, name_ = None ):
		#print 'Creating element  float2'
		e = _Float2Element( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createFloat3Element( self, id_ = None, name_ = None ):
		#print 'Creating element  float3'
		e = _Float3Element( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createFloat4Element( self, id_ = None, name_ = None ):
		#print 'Creating element  float4'
		e = _Float4Element( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createFloat4x4Element( self, id_ = None, name_ = None ):
		#print 'Creating element  float4x4'
		e = _Float4x4Element( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createIntElement( self, id_ = None, name_ = None ):
		#print 'Creating element  int'
		e = _IntElement( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createBoolElement( self, id_ = None, name_ = None ):
		#print 'Creating element  bool'
		e = _BoolElement( self, id_, name_ )
		#e.ownerDocument = self
		return e

	def createTextureElement( self, id_ = None, name_ = None, type_ = None, filterMin_ = None, filterMag_ = None, filterMip_ = None, wrapS_ = None, wrapT_ = None, wrapU_ = None, borderColor_ = None ):
		#print 'Creating element  texture'
		e = _TextureElement( self, id_, name_, type_, filterMin_, filterMag_, filterMip_, wrapS_, wrapT_, wrapU_, borderColor_ )
		#e.ownerDocument = self
		return e

	def createImgElement( self, id_ = None, src_ = None ):
		#print 'Creating element  img'
		e = _ImgElement( self, id_, src_ )
		#e.ownerDocument = self
		return e

	def createVideoElement( self, id_ = None, src_ = None ):
		#print 'Creating element  video'
		e = _VideoElement( self, id_, src_ )
		#e.ownerDocument = self
		return e

	def createViewElement( self, id_ = None, visible_ = None, position_ = None, orientation_ = None, fieldOfView_ = None ):
		#print 'Creating element  view'
		e = _ViewElement( self, id_, visible_, position_, orientation_, fieldOfView_ )
		#e.ownerDocument = self
		return e

class _XML3DElement( Element ):
	""" A XML3DBaseType Element """

	_id = None

	def __init__( self, doc_, name, id_ = None, class_ = None, style_ = None):
		Element.__init__( self, name )
		self.ownerDocument = doc_
		self._id = id_
		if not (self._id == None):
			self.setAttribute( "id", self._id )


class _Xml3dElement( _XML3DElement ):
	""" A xml3d Element """
	_height = None
	_width = None
	_activeView = None

	def __init__( self, doc_, id_, height_, width_, activeView_ ):
		_XML3DElement.__init__( self, doc_, "xml3d", id_ )
		#print ("Setting height: " + str(height_))
		self._height = height_
		#print ("Setting width: " + str(width_))
		self._width = width_
		#print ("Setting activeView: " + str(activeView_))
		self._activeView = activeView_
		if not (self._height == None):
			self.setAttribute( "height", self._height )
		if not (self._width == None):
			self.setAttribute( "width", self._width )
		if not (self._activeView == None):
			self.setAttribute( "activeView", self._activeView )

	def setHeight( self, value ):
		self._height = value
		self.setAttribute( "height", self._height )
		return

	def setWidth( self, value ):
		self._width = value
		self.setAttribute( "width", self._width )
		return

	def setActiveView( self, value ):
		self._activeView = value
		self.setAttribute( "activeView", self._activeView )
		return

class _DataElement( _XML3DElement ):
	""" A data Element """
	_map = None
	_expose = None
	_src = None
	_script = None

	def __init__( self, doc_, id_, map_, expose_, src_, script_ ):
		_XML3DElement.__init__( self, doc_, "data", id_ )
		#print ("Setting map: " + str(map_))
		self._map = map_
		#print ("Setting expose: " + str(expose_))
		self._expose = expose_
		#print ("Setting src: " + str(src_))
		self._src = src_
		#print ("Setting script: " + str(script_))
		self._script = script_
		if not (self._map == None):
			self.setAttribute( "map", self._map )
		if not (self._expose == None):
			self.setAttribute( "expose", self._expose )
		if not (self._src == None):
			self.setAttribute( "src", self._src )
		if not (self._script == None):
			self.setAttribute( "script", self._script )

	def setMap( self, value ):
		self._map = value
		self.setAttribute( "map", self._map )
		return

	def setExpose( self, value ):
		self._expose = value
		self.setAttribute( "expose", self._expose )
		return

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

	def setScript( self, value ):
		self._script = value
		self.setAttribute( "script", self._script )
		return

class _DefsElement( _XML3DElement ):
	""" A defs Element """

	def __init__( self, doc_, id_ ):
		_XML3DElement.__init__( self, doc_, "defs", id_ )

class _GroupElement( _XML3DElement ):
	""" A group Element """
	_visible = None
	_transform = None
	_shader = None

	def __init__( self, doc_, id_, visible_, transform_, shader_ ):
		_XML3DElement.__init__( self, doc_, "group", id_ )
		#print ("Setting visible: " + str(visible_))
		self._visible = visible_
		#print ("Setting transform: " + str(transform_))
		self._transform = transform_
		#print ("Setting shader: " + str(shader_))
		self._shader = shader_
		if not (self._visible == None):
			self.setAttribute( "visible", self._visible )
		if not (self._transform == None):
			self.setAttribute( "transform", self._transform )
		if not (self._shader == None):
			self.setAttribute( "shader", self._shader )

	def setVisible( self, value ):
		self._visible = value
		self.setAttribute( "visible", self._visible )
		return

	def setTransform( self, value ):
		self._transform = value
		self.setAttribute( "transform", self._transform )
		return

	def setShader( self, value ):
		self._shader = value
		self.setAttribute( "shader", self._shader )
		return

class _MeshElement( _XML3DElement ):
	""" A mesh Element """
	_visible = None
	_type = None
	_src = None

	def __init__( self, doc_, id_, visible_, type_, src_ ):
		_XML3DElement.__init__( self, doc_, "mesh", id_ )
		#print ("Setting visible: " + str(visible_))
		self._visible = visible_
		#print ("Setting type: " + str(type_))
		self._type = type_
		#print ("Setting src: " + str(src_))
		self._src = src_
		if not (self._visible == None):
			self.setAttribute( "visible", self._visible )
		if not (self._type == None):
			self.setAttribute( "type", self._type )
		if not (self._src == None):
			self.setAttribute( "src", self._src )

	def setVisible( self, value ):
		self._visible = value
		self.setAttribute( "visible", self._visible )
		return

	def setType( self, value ):
		self._type = value
		self.setAttribute( "type", self._type )
		return

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

class _TransformElement( _XML3DElement ):
	""" A transform Element """
	_translation = None
	_scale = None
	_rotation = None
	_center = None
	_scaleOrientation = None

	def __init__( self, doc_, id_, translation_, scale_, rotation_, center_, scaleOrientation_ ):
		_XML3DElement.__init__( self, doc_, "transform", id_ )
		#print ("Setting translation: " + str(translation_))
		self._translation = translation_
		#print ("Setting scale: " + str(scale_))
		self._scale = scale_
		#print ("Setting rotation: " + str(rotation_))
		self._rotation = rotation_
		#print ("Setting center: " + str(center_))
		self._center = center_
		#print ("Setting scaleOrientation: " + str(scaleOrientation_))
		self._scaleOrientation = scaleOrientation_
		if not (self._translation == None):
			self.setAttribute( "translation", self._translation )
		if not (self._scale == None):
			self.setAttribute( "scale", self._scale )
		if not (self._rotation == None):
			self.setAttribute( "rotation", self._rotation )
		if not (self._center == None):
			self.setAttribute( "center", self._center )
		if not (self._scaleOrientation == None):
			self.setAttribute( "scaleOrientation", self._scaleOrientation )

	def setTranslation( self, value ):
		self._translation = value
		self.setAttribute( "translation", self._translation )
		return

	def setScale( self, value ):
		self._scale = value
		self.setAttribute( "scale", self._scale )
		return

	def setRotation( self, value ):
		self._rotation = value
		self.setAttribute( "rotation", self._rotation )
		return

	def setCenter( self, value ):
		self._center = value
		self.setAttribute( "center", self._center )
		return

	def setScaleOrientation( self, value ):
		self._scaleOrientation = value
		self.setAttribute( "scaleOrientation", self._scaleOrientation )
		return

class _ShaderElement( _XML3DElement ):
	""" A shader Element """
	_script = None
	_src = None

	def __init__( self, doc_, id_, script_, src_ ):
		_XML3DElement.__init__( self, doc_, "shader", id_ )
		#print ("Setting script: " + str(script_))
		self._script = script_
		#print ("Setting src: " + str(src_))
		self._src = src_
		if not (self._script == None):
			self.setAttribute( "script", self._script )
		if not (self._src == None):
			self.setAttribute( "src", self._src )

	def setScript( self, value ):
		self._script = value
		self.setAttribute( "script", self._script )
		return

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

class _LightElement( _XML3DElement ):
	""" A light Element """
	_visible = None
	_shader = None
	_global = None
	_intensity = None

	def __init__( self, doc_, id_, visible_, shader_, global_, intensity_ ):
		_XML3DElement.__init__( self, doc_, "light", id_ )
		#print ("Setting visible: " + str(visible_))
		self._visible = visible_
		#print ("Setting shader: " + str(shader_))
		self._shader = shader_
		#print ("Setting global: " + str(global_))
		self._global = global_
		#print ("Setting intensity: " + str(intensity_))
		self._intensity = intensity_
		if not (self._visible == None):
			self.setAttribute( "visible", self._visible )
		if not (self._shader == None):
			self.setAttribute( "shader", self._shader )
		if not (self._global == None):
			self.setAttribute( "global", self._global )
		if not (self._intensity == None):
			self.setAttribute( "intensity", self._intensity )

	def setVisible( self, value ):
		self._visible = value
		self.setAttribute( "visible", self._visible )
		return

	def setShader( self, value ):
		self._shader = value
		self.setAttribute( "shader", self._shader )
		return

	def setGlobal( self, value ):
		self._global = value
		self.setAttribute( "global", self._global )
		return

	def setIntensity( self, value ):
		self._intensity = value
		self.setAttribute( "intensity", self._intensity )
		return

class _LightshaderElement( _XML3DElement ):
	""" A lightshader Element """
	_script = None
	_src = None

	def __init__( self, doc_, id_, script_, src_ ):
		_XML3DElement.__init__( self, doc_, "lightshader", id_ )
		#print ("Setting script: " + str(script_))
		self._script = script_
		#print ("Setting src: " + str(src_))
		self._src = src_
		if not (self._script == None):
			self.setAttribute( "script", self._script )
		if not (self._src == None):
			self.setAttribute( "src", self._src )

	def setScript( self, value ):
		self._script = value
		self.setAttribute( "script", self._script )
		return

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

class _ScriptElement( _XML3DElement ):
	""" A script Element """
	_src = None
	_type = None

	def __init__( self, doc_, id_, src_, type_ ):
		_XML3DElement.__init__( self, doc_, "script", id_ )
		#print ("Setting src: " + str(src_))
		self._src = src_
		#print ("Setting type: " + str(type_))
		self._type = type_
		if not (self._src == None):
			self.setAttribute( "src", self._src )
		if not (self._type == None):
			self.setAttribute( "type", self._type )

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

	def setType( self, value ):
		self._type = value
		self.setAttribute( "type", self._type )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _FloatElement( _XML3DElement ):
	""" A float Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "float", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _Float2Element( _XML3DElement ):
	""" A float2 Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "float2", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _Float3Element( _XML3DElement ):
	""" A float3 Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "float3", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _Float4Element( _XML3DElement ):
	""" A float4 Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "float4", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _Float4x4Element( _XML3DElement ):
	""" A float4x4 Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "float4x4", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _IntElement( _XML3DElement ):
	""" A int Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "int", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _BoolElement( _XML3DElement ):
	""" A bool Element """
	_name = None

	def __init__( self, doc_, id_, name_ ):
		_XML3DElement.__init__( self, doc_, "bool", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		if not (self._name == None):
			self.setAttribute( "name", self._name )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setValue( self, value ):
		self.appendChild(self.ownerDocument.createTextNode(value))

class _TextureElement( _XML3DElement ):
	""" A texture Element """
	_name = None
	_type = None
	_filterMin = None
	_filterMag = None
	_filterMip = None
	_wrapS = None
	_wrapT = None
	_wrapU = None
	_borderColor = None

	def __init__( self, doc_, id_, name_, type_, filterMin_, filterMag_, filterMip_, wrapS_, wrapT_, wrapU_, borderColor_ ):
		_XML3DElement.__init__( self, doc_, "texture", id_ )
		#print ("Setting name: " + str(name_))
		self._name = name_
		#print ("Setting type: " + str(type_))
		self._type = type_
		#print ("Setting filterMin: " + str(filterMin_))
		self._filterMin = filterMin_
		#print ("Setting filterMag: " + str(filterMag_))
		self._filterMag = filterMag_
		#print ("Setting filterMip: " + str(filterMip_))
		self._filterMip = filterMip_
		#print ("Setting wrapS: " + str(wrapS_))
		self._wrapS = wrapS_
		#print ("Setting wrapT: " + str(wrapT_))
		self._wrapT = wrapT_
		#print ("Setting wrapU: " + str(wrapU_))
		self._wrapU = wrapU_
		#print ("Setting borderColor: " + str(borderColor_))
		self._borderColor = borderColor_
		if not (self._name == None):
			self.setAttribute( "name", self._name )
		if not (self._type == None):
			self.setAttribute( "type", self._type )
		if not (self._filterMin == None):
			self.setAttribute( "filterMin", self._filterMin )
		if not (self._filterMag == None):
			self.setAttribute( "filterMag", self._filterMag )
		if not (self._filterMip == None):
			self.setAttribute( "filterMip", self._filterMip )
		if not (self._wrapS == None):
			self.setAttribute( "wrapS", self._wrapS )
		if not (self._wrapT == None):
			self.setAttribute( "wrapT", self._wrapT )
		if not (self._wrapU == None):
			self.setAttribute( "wrapU", self._wrapU )
		if not (self._borderColor == None):
			self.setAttribute( "borderColor", self._borderColor )

	def setName( self, value ):
		self._name = value
		self.setAttribute( "name", self._name )
		return

	def setType( self, value ):
		self._type = value
		self.setAttribute( "type", self._type )
		return

	def setFilterMin( self, value ):
		self._filterMin = value
		self.setAttribute( "filterMin", self._filterMin )
		return

	def setFilterMag( self, value ):
		self._filterMag = value
		self.setAttribute( "filterMag", self._filterMag )
		return

	def setFilterMip( self, value ):
		self._filterMip = value
		self.setAttribute( "filterMip", self._filterMip )
		return

	def setWrapS( self, value ):
		self._wrapS = value
		self.setAttribute( "wrapS", self._wrapS )
		return

	def setWrapT( self, value ):
		self._wrapT = value
		self.setAttribute( "wrapT", self._wrapT )
		return

	def setWrapU( self, value ):
		self._wrapU = value
		self.setAttribute( "wrapU", self._wrapU )
		return

	def setBorderColor( self, value ):
		self._borderColor = value
		self.setAttribute( "borderColor", self._borderColor )
		return

class _ImgElement( _XML3DElement ):
	""" A img Element """
	_src = None

	def __init__( self, doc_, id_, src_ ):
		_XML3DElement.__init__( self, doc_, "img", id_ )
		#print ("Setting src: " + str(src_))
		self._src = src_
		if not (self._src == None):
			self.setAttribute( "src", self._src )

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

class _VideoElement( _XML3DElement ):
	""" A video Element """
	_src = None

	def __init__( self, doc_, id_, src_ ):
		_XML3DElement.__init__( self, doc_, "video", id_ )
		#print ("Setting src: " + str(src_))
		self._src = src_
		if not (self._src == None):
			self.setAttribute( "src", self._src )

	def setSrc( self, value ):
		self._src = value
		self.setAttribute( "src", self._src )
		return

class _ViewElement( _XML3DElement ):
	""" A view Element """
	_visible = None
	_position = None
	_orientation = None
	_fieldOfView = None

	def __init__( self, doc_, id_, visible_, position_, orientation_, fieldOfView_ ):
		_XML3DElement.__init__( self, doc_, "view", id_ )
		#print ("Setting visible: " + str(visible_))
		self._visible = visible_
		#print ("Setting position: " + str(position_))
		self._position = position_
		#print ("Setting orientation: " + str(orientation_))
		self._orientation = orientation_
		#print ("Setting fieldOfView: " + str(fieldOfView_))
		self._fieldOfView = fieldOfView_
		if not (self._visible == None):
			self.setAttribute( "visible", self._visible )
		if not (self._position == None):
			self.setAttribute( "position", self._position )
		if not (self._orientation == None):
			self.setAttribute( "orientation", self._orientation )
		if not (self._fieldOfView == None):
			self.setAttribute( "fieldOfView", self._fieldOfView )

	def setVisible( self, value ):
		self._visible = value
		self.setAttribute( "visible", self._visible )
		return

	def setPosition( self, value ):
		self._position = value
		self.setAttribute( "position", self._position )
		return

	def setOrientation( self, value ):
		self._orientation = value
		self.setAttribute( "orientation", self._orientation )
		return

	def setFieldOfView( self, value ):
		self._fieldOfView = value
		self.setAttribute( "fieldOfView", self._fieldOfView )
		return