class XMLWriter:
	""" An very simpe XML writer """
	def __init__(self, stream, ident = 0):
		self._stream = stream
		self._isElementOpen = False
		self._ident = ident
		self._hasChildElements = [False]

	def hasChildElements(self):
		self._hasChildElements[len(self._hasChildElements)-1] = True
		self._hasChildElements.append(False)

	def startElement(self, _name, **attr):
		self.hasChildElements()
		if(self._isElementOpen):
			self._stream.write(">\n")
		self._stream.write(self._ident * ' ')
		self._stream.write("<%s" % _name)
		self._isElementOpen = True
		self._ident = self._ident + 1
		content = None
		for key in attr:
			if key == "_content":
				content = attr[key]
			else:
				self.attribute(key, attr[key])

		if content != None:
			self._stream.write(">%s" % content)
			self._isElementOpen = False



	def endElement(self, _name):
		if(self._isElementOpen):
			self._stream.write(">")
			self._isElementOpen = False

		hasChildren = self._hasChildElements.pop()
		self._ident -= 1
		if hasChildren:
			self._stream.write(self._ident * ' ')
		print("</%s>\n" % _name, file=self._stream, end="")

	def attribute(self, name, value):
		self._stream.write(" " + name + "=\"" + value + "\"")

	def element(self, _name, **attr):
		self.startElement(_name, **attr)
		self.endElement(_name)