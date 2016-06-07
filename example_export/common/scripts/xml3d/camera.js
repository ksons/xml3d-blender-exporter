/*************************************************************************/
/*                                                                       */
/*  xml3d_scene_controller.js                                            */
/*  Navigation method for XML3D                                             */
/*                                                                       */
/*  Copyright (C) 2010                                                   */
/*  DFKI - German Research Center for Artificial Intelligence            */
/*                                                                       */
/*  xml3d.js is free software; you can redistribute it and/or modify     */
/*  under the terms of the GNU General Public License as                 */
/*  published by the Free Software Foundation; either version 2 of       */
/*  the License, or (at your option) any later version.                  */
/*                                                                       */
/*  xml3d.js is distributed in the hope that it will be useful, but      */
/*  WITHOUT ANY WARRANTY; without even the implied warranty of           */
/*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                 */
/*  See the GNU General Public License                                   */
/*  (http://www.fsf.org/licensing/licenses/gpl.html) for more details.   */
/*                                                                       */
/*************************************************************************/

/* extension/modified version of camera.js
 * implements real trackball & ego perspective navigation
 * developed in the scope of the seminar "Character Animation"
 * Author: Jonas Trottnow
 * Supervisor: Alexis Heloir
 */

//Check, if basics have already been defined
if(!XML3D)
    XML3D = {};
if(!XML3D.util)
    XML3D.util = {};

XML3D.util.Timer = function() {
    this.start();
};

XML3D.util.Timer.prototype.restart = function() {
    var prevTime = this.time;
    this.start();
    return this.time - prevTime;
};

XML3D.util.Timer.prototype.start = function() {
    this.time = new Date().getTime();
};


XML3D.Camera = function(view) {
    this.view = view;
};

XML3D.Camera.prototype.__defineGetter__("orientation", function() {
    return this.view.orientation;
});
XML3D.Camera.prototype.__defineGetter__("position", function() {
    return this.view.position;
});
XML3D.Camera.prototype.__defineSetter__("orientation", function(orientation) {
    /*xml3d.debug.logError("Orientation: " + orientation);*/
    //xml3d.copyRotation(this.view.orientation, orientation);
    var ax = orientation.axis;
    var str = ax.x + " " + ax.y + " " + ax.z + " " + orientation.angle;
    this.view.setAttribute("orientation", str);
});
XML3D.Camera.prototype.__defineSetter__("position", function(position) {
    //xml3d.copyVector(this.view.position, position);
    var str = position.x + " " + position.y + " " + position.z;
    this.view.setAttribute("position", str);
});
XML3D.Camera.prototype.__defineGetter__("direction", function() {
    return this.view.getDirection();
});
XML3D.Camera.prototype.__defineGetter__("upVector", function() {
    return this.view.getUpVector();
});
XML3D.Camera.prototype.__defineGetter__("fieldOfView", function() {
    return this.view.fieldOfView;
});

XML3D.Camera.prototype.rotateAroundPoint = function(q0, p0) {
    //xml3d.debug.logError("Orientation: " + this.orientation.multiply(q0).normalize());
    var tmp = this.orientation.multiply(q0);
    tmp.normalize();
    this.orientation = tmp;
    var trans = new window.XML3DRotation(this.inverseTransformOf(q0.axis), q0.angle).rotateVec3(this.position.subtract(p0));
    this.position = p0.add(trans);
};

XML3D.Camera.prototype.lookAround = function(rotSide, rotUp, upVector) {
    //xml3d.debug.logError("Orientation: " + this.orientation.multiply(q0).normalize());
    var check = rotUp.multiply(this.orientation);
    var tmp;
    if( Math.abs(upVector.dot(check.rotateVec3(new window.XML3DVec3(0,0,-1)))) > 0.95 )
        tmp = rotSide;
    else
        tmp = rotSide.multiply(rotUp);
    tmp.normalize();
    tmp = tmp.multiply(this.orientation);
    tmp.normalize();
    this.orientation = tmp;
};

XML3D.Camera.prototype.rotate = function(q0) {
    this.orientation = this.orientation.multiply(q0).normalize();
};

XML3D.Camera.prototype.translate = function(t0) {
    this.position = this.position.add(t0);
};

XML3D.Camera.prototype.translateAbsolute = function(t0) {
    this.position = t0;
};

XML3D.Camera.prototype.inverseTransformOf = function(vec) {
    return this.orientation.rotateVec3(vec);
};

XML3D.Xml3dSceneController = function(xml3dElement) {
    this.webgl = typeof(xml3dElement.style) !== 'object';

    this.xml3d = xml3dElement;
    this.canvas = this.webgl ?  xml3dElement.canvas : xml3dElement;

    var view = this.getView();
    if (!view)
    {
        XML3D.debug.logWarning("No view found, rendering disabled!");
        if (xml3dElement.update)
            xml3dElement.update(); // TODO: Test
    }
    if (!this.xml3d || !view)
    {
        XML3D.debug.logError("Could not initialize Camera Controller.");
        return;
    }

    this.camera = new XML3D.Camera(view);
    this.timer = new XML3D.util.Timer();
    this.prevPos = {x: -1, y: -1};
    this.prevZoomVectorLength;
				
    this.mode = "ego";
    this.altDown = false;
    this.revolveAroundPoint = new window.XML3DVec3(0.0, 0.0, -1.0);
    this.rotateSpeed = 1;
    this.zoomSpeed = 1;
    this.spinningSensitivity = 0.3;
    this.isSpinning = false;

    this.upVector = this.camera.upVector;

    this.moveSpeedElement = document.getElementById("moveSpeed");
    this.useKeys = true;//document.getElementById("useKeys");

    var navigations = xml3dElement.getElementsByTagName("navigation");

    if(navigations.length > 0)
    {
        var config = navigations[0];
        this.mode = config.getAttribute("mode");

        if(this.mode == "none")
            return;

        if(this.mode != "walk" && this.mode != "examine" )
            this.mode = "examine";

        if(config.getAttribute("resolveAround")){
            XML3D.debug.logWarning("resolveAround is obsolete. Use 'revolveAround' instead!");
            this.revolveAroundPoint.setVec3Value(config.getAttribute("resolveAround"));
        }
        if(config.getAttribute("revolveAround")){
            this.revolveAroundPoint.setVec3Value(config.getAttribute("revolveAround"));
        }
        if(config.getAttribute("speed"))
        {
            this.zoomSpeed *= config.getAttribute("speed");
        }
    }

    this.attach();
};

///////////////////////////////////////////////////////////////////////////////////
///////////////////////// Look At Rotation ////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////
XML3D.Xml3dSceneController.prototype.lookAt = function(point) {
	
	//get veector pointing to given target point
	var targetDir = point.subtract(this.camera.position).normalize();
	
	//get camera right (->) vector
	var cross = this.camera.upVector.cross(this.camera.direction).normalize();
	
	//project vectors by only using rotations on cameras local x & y axis
	var projX = (targetDir.subtract(this.camera.upVector.scale(targetDir.dot(this.camera.upVector)))).normalize();
	var projY = (targetDir.subtract(cross.scale(targetDir.dot(cross)))).normalize();
	
	//calculate angles on x & y axis
	var xDeltaAngle = this.camera.direction.multiply(projX);
	xDeltaAngle = Math.acos(xDeltaAngle.x + xDeltaAngle.y + xDeltaAngle.z);
	var yDeltaAngle = this.camera.direction.multiply(projY);
	yDeltaAngle = Math.acos(yDeltaAngle.x + yDeltaAngle.y + yDeltaAngle.z);
	
	//acos failure error handling
	if(!isNaN(xDeltaAngle) && !isNaN(yDeltaAngle))
	{
		//correct quarters
		if(this.camera.upVector.y < 0.0)
		{
			xDeltaAngle = -xDeltaAngle;
			yDeltaAngle = -yDeltaAngle;
		}
		if(this.camera.position.z >=  point.z)
		{
			if(this.camera.direction.x < projX.normalize().x) xDeltaAngle = -xDeltaAngle;
			if(this.camera.direction.y < projY.normalize().y) yDeltaAngle = -yDeltaAngle;
		}
		else
		{
			if(this.camera.direction.x > projX.normalize().x) xDeltaAngle = -xDeltaAngle;
			if(this.camera.direction.y < projY.normalize().y) yDeltaAngle = -yDeltaAngle;
		}
	
		//apply rotation
		var mx = new window.XML3DRotation( this.camera.upVector , xDeltaAngle);
		var my = new window.XML3DRotation( cross , yDeltaAngle);

		this.camera.lookAround(mx, my, this.upVector);
	}
	
};

XML3D.Xml3dSceneController.prototype.setCamera = function(newCamera) {
    this.camera = new XML3D.Camera(newCamera);
    this.upVector = this.camera.upVector;
};

XML3D.Xml3dSceneController.prototype.setRevolvePoint = function(vec) {
    this.revolveAroundPoint = vec;
};

XML3D.Xml3dSceneController.prototype.attach = function() {
    var self = this;
    this._evt_mousedown = function(e) {self.mousePressEvent(e);};
    this._evt_mouseup = function(e) {self.mouseReleaseEvent(e);};
    this._evt_mousemove = function(e) {self.mouseMoveEvent(e);};
    this._evt_contextmenu = function(e) {self.stopEvent(e);};
    this._evt_keydown = function(e) {self.keyHandling(e);};
    this._evt_keyup = function(e) {self.keyUpHandling(e);};


    this.canvas.addEventListener("mousedown", this._evt_mousedown, false);
    document.addEventListener("mouseup", this._evt_mouseup, false);
    document.addEventListener("mousemove",this._evt_mousemove, false);

    this.canvas.addEventListener("contextmenu", this._evt_contextmenu, false);
    if (this.useKeys)
    {
        document.addEventListener("keydown", this._evt_keydown, false);
        document.addEventListener("keyup", this._evt_keyup, false);
    }
    
};

XML3D.Xml3dSceneController.prototype.detach = function() {
    this.canvas.removeEventListener("mousedown", this._evt_mousedown, false);
    document.removeEventListener("mouseup", this._evt_mouseup, false);
    document.removeEventListener("mousemove",this._evt_mousemove, false);

    this.canvas.removeEventListener("contextmenu", this._evt_contextmenu, false);
    if (this.useKeys)
    {
        document.removeEventListener("keydown", this._evt_keydown, false);
        document.removeEventListener("keyup", this._evt_keyup, false);
    }
};

XML3D.Xml3dSceneController.prototype.__defineGetter__("width", function() { return this.canvas.width;});
XML3D.Xml3dSceneController.prototype.__defineGetter__("height", function() { return this.canvas.height;});

XML3D.Xml3dSceneController.prototype.getView = function() {
    var activeView = this.xml3d.activeView;
    XML3D.debug.logInfo("Active View: " + activeView);
	console.log("Active View: " + activeView);

    if (activeView)
    {
        if (activeView.substring(0, 1) == '#') {
            activeView = activeView.substring(1);
        }
        XML3D.debug.logInfo("Trying to resolve view '" + activeView +"'");
        activeView = document.getElementById(activeView);
    }

    // if activeView is not defined or the reference is not valid
    // use the first view element
    if (!activeView)
    {
        XML3D.debug.logWarning("No view referenced. Trying to use first view.");
        activeView = this.xml3d.querySelector('view');
    }

    if(false)
    {
        // no view present at all
        // create new one and append it to defs element
        XML3D.debug.logWarning("No view defined. Trying to create view.");

        // create it
        activeView = document.createElementNS(XML3D.xml3dNS, "view");

        var id = "created_xml3d.Xml3dSceneController.view_";
        id += "" + Math.random();
        activeView.setAttribute("id", id);

        // append it to defs
        var defsEl =  document.evaluate('xml3d:defs[1]', this.xml3d, function() {
            return XML3D.xml3dNS;
        }, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

        if(!defsEl)
        {
            defsEl = document.createElementNS(XML3D.xml3dNS, "defs");
            this.xml3d.appendChild(defsEl);
        }

        defsEl.appendChild(activeView);
    }

    return activeView;
};

XML3D.Xml3dSceneController.prototype.stopEvent = function(ev) {
    if (ev.preventDefault)
        ev.preventDefault();
    if (ev.stopPropagation)
        ev.stopPropagation();
    ev.returnValue = false;
};

XML3D.Xml3dSceneController.prototype.update = function() {
    if (this.animation || this.needUpdate) {
        this.needUpdate = false;
        if (this.xml3d.update)
            this.xml3d.update();
    }
};

XML3D.Xml3dSceneController.prototype.NO_MOUSE_ACTION = 0;
XML3D.Xml3dSceneController.prototype.TRANSLATE = 1;
XML3D.Xml3dSceneController.prototype.DOLLY = 2;
XML3D.Xml3dSceneController.prototype.ROTATE = 3;
XML3D.Xml3dSceneController.prototype.LOOKAROUND = 4;
XML3D.Xml3dSceneController.prototype.TRACKBALL = 5;

XML3D.Xml3dSceneController.prototype.mousePressEvent = function(event) {

    var ev = event || window.event;

    var button = (ev.which || ev.button);
    switch (button) {
        case 1:
        	if(!this.altDown)
        	{
            	if(this.mode == "examine")
				{
					this.action = this.ROTATE;
				}
				else if (this.mode == "trackball") 
				{
					this.action = this.TRACKBALL;
				}
            	else
				{
                	this.action = this.LOOKAROUND;
				}
            }
            else
            {
            	var xml3d = this.xml3d;
            	var ray = xml3d.generateRay(event.pageX, event.pageY);
            	var hitPoint = new XML3DVec3();
				var hitNormal = new XML3DVec3();
				var hitObject = xml3d.getElementByRay(ray, hitPoint, hitNormal);
				if(!isNaN(hitPoint.x))
				{
					this.revolveAroundPoint = hitPoint;
					var cube = document.getElementById("x");
					if(cube)
					{
						cube.setAttribute('style' , 'transform:translate3d('+hitPoint.x+","+hitPoint.y+","+hitPoint.z+");");
					}
					this.lookAt(hitPoint);
					this.revolveAroundPoint = hitPoint;
				}
            }
            break;
        case 2:
            this.action = this.TRANSLATE;
            break;
        case 3:
            this.action = this.DOLLY;
            break;
        default:
            this.action = this.NO_MOUSE_ACTION;
    }

    this.prevPos.x = ev.pageX;
    this.prevPos.y = ev.pageY;

    this.stopEvent(event);
    return false;
};

XML3D.Xml3dSceneController.prototype.mouseReleaseEvent = function(event) {
    this.stopEvent(event);

    //if (this.action == this.ROTATE && this.mouseSpeed > this.spinningSensitivity)
    //    this.startSpinning();

    this.action = this.NO_MOUSE_ACTION;
    return false;
};

XML3D.Xml3dSceneController.prototype.startSpinning = new function() {
    this.isSpinning = true;
    // TODO
};

XML3D.Xml3dSceneController.prototype.computeMouseSpeed = function(event) {
    var dx = (event.pageX - this.prevPos.x);
    var dy = (event.pageY - this.prevPos.y);
    var dist = Math.sqrt(+dx*dx + dy*+dy);
    this.delay = this.timer.restart();
    if (this.delay == 0)
        this.mouseSpeed = dist;
      else
        this.mouseSpeed = dist/this.delay;
    XML3D.debug.logWarning("Mouse speed: " + this.mouseSpeed);
};

XML3D.Xml3dSceneController.prototype.mouseMoveEvent = function(event, camera) {

    var ev = event || window.event;
    if (!this.action)
        return;
    switch(this.action) {
        case(this.TRANSLATE):
            var f = 2.0* Math.tan(this.camera.fieldOfView/2.0) / this.height;
            var dx = f*(ev.pageX - this.prevPos.x);
            var dy = f*(ev.pageY - this.prevPos.y);
            var trans = new window.XML3DVec3(-dx, dy, 0.0);
            this.camera.translate(this.camera.inverseTransformOf(trans));
			this.revolveAroundPoint.add(this.camera.inverseTransformOf(trans));
            break;
        case(this.DOLLY):
            var dy = this.zoomSpeed * (ev.pageY - this.prevPos.y) / this.height;
            this.camera.translate(this.camera.inverseTransformOf(new window.XML3DVec3(0, 0, dy)));
			this.revolveAroundPoint.add(this.camera.inverseTransformOf(new window.XML3DVec3(0, 0, dy)));
            break;
        case(this.ROTATE):
            var dx = -this.rotateSpeed * (ev.pageX - this.prevPos.x) * 2.0 * Math.PI / this.width;
            var dy = -this.rotateSpeed * (ev.pageY - this.prevPos.y) * 2.0 * Math.PI / this.height;

            var mx = new window.XML3DRotation(new window.XML3DVec3(0,1,0), dx);
            var my = new window.XML3DRotation(new window.XML3DVec3(1,0,0), dy);
            //this.computeMouseSpeed(ev);
            this.camera.rotateAroundPoint(mx.multiply(my), this.revolveAroundPoint);
            break;
        case(this.TRACKBALL):
///////////////////////////////////////////////////////////////////////////////////
///////////////////// Trackball implementation ////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////
			var h = window.innerHeight;
			var w = window.innerWidth;
			var mid = new window.XML3DVec3(w/2.0,h/2.0,0);
			var radius = h;
			
			//Calculate previous 3D point on trackball sphere
			var x1 = Math.max(Math.min(this.prevPos.x, w),0);
			var y1 = Math.max(Math.min(this.prevPos.y, h),0);
			var z1 = Math.sqrt(Math.max((radius/2.0)*(radius/2.0) - (x1-w/2.0)*(x1-w/2.0) - (y1-h/2.0)*(y1-h/2.0),0));
			var p1 = new window.XML3DVec3(x1,y1,z1);
			p1 = p1.subtract(mid).normalize();
			
			//Calculate current 3D point on trackball sphere
			var x2 = Math.max(Math.min(ev.pageX, w),0);
			var y2 = Math.max(Math.min(ev.pageY, h),0);
			var z2 = Math.sqrt(Math.max((radius/2.0)*(radius/2.0) - (x2-w/2.0)*(x2-w/2.0) - (y2-h/2.0)*(y2-h/2.0),0));
			var p2 = new window.XML3DVec3(x2,y2,z2);
			p2 = p2.subtract(mid).normalize();
			
			//Calculate angle-axis representation of rotation from P1 to P2
			var angle = Math.acos(p1.dot(p2));
			var axis = p1.cross(p2);
			axis.y = -axis.y;
			if (isNaN(angle)) angle = 0;
			
			//Transform angle-axis representation to quaternion
			var quaternion = new window.XML3DRotation();
			quaternion.setAxisAngle(axis,angle);
			
			//apply it to the camera
			this.camera.rotateAroundPoint(quaternion, this.revolveAroundPoint);     			
			break;
///////////////////////////////////////////////////////////////////////////////////
        case(this.LOOKAROUND):
            var dx = -this.rotateSpeed * 0.1 * (ev.pageX - this.prevPos.x) * 2.0 * Math.PI / this.width;
            var dy = -this.rotateSpeed * 0.1 * (ev.pageY - this.prevPos.y) * 2.0 * Math.PI / this.height;
            var cross = this.upVector.cross(this.camera.direction);

            //var mx = new window.XML3DRotation( this.upVector , dx);
            //var my = new window.XML3DRotation( cross , dy);

			var mx = new window.XML3DRotation(new window.XML3DVec3(0,1,0), dx);
			var my = new window.XML3DRotation(new window.XML3DVec3(1,0,0), dy);

			this.camera.rotateAroundPoint(mx.multiply(my), this.camera.position);
            //this.camera.lookAround(mx, my, this.camera.upVector);
            break;
    }

    if (this.action != this.NO_MOUSE_ACTION)
    {
        this.needUpdate = true;
        this.prevPos.x = ev.pageX;
        this.prevPos.y = ev.pageY;
        event.returnValue = false;

        this.update();
    }
    this.stopEvent(event);
    return false;
};

// -----------------------------------------------------
// key movement
// -----------------------------------------------------

XML3D.Xml3dSceneController.prototype.keyHandling = function(e) {
    var KeyID = e.keyCode;
    if (KeyID == 0) {
        switch (e.which) {
		case 49: //1
			KeyID = 49;
			break; 
		case 50: //2
			KeyID = 50;
			break;
        case 119:
            KeyID = 87;
            break; // w
        case 100:
            KeyID = 68;
            break; // d
        case 97:
            KeyID = 65;
            break; // a
        case 115:
            KeyID = 83;
            break; // s
        }
    }

    var xml3d = this.xml3d;
    // alert(xml3d);
    var camera = this.camera;
    var dir = camera.direction;
    if (xml3d) {
        switch (KeyID) {
        case 18:
        	this.altDown = true;
        	break;
		case 49: //1
			this.mode = "ego";
			console.log("Mode: " + this.mode);
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:scale3d(0,0,0););');
			}
			break;
		case 50: //2
			this.mode = "trackball";
			this.lookAt(this.revolveAroundPoint);
			console.log("Mode: " + this.mode);
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:scale3d(1,1,1););');
				cube.setAttribute('style' , 'transform:transform:translate3d('+this.revolveAroundPoint.x+','+this.revolveAroundPoint.y+','+this.revolveAroundPoint.z+');');
			}
			break;
        case 38: // up
        case 87: // w
            camera.position = camera.position.add(dir.scale(this.zoomSpeed));

            break;
        case 39: // right
        case 68: // d
			camera.position = camera.position.subtract(this.camera.upVector.cross(this.camera.direction).normalize());
			this.revolveAroundPoint = this.revolveAroundPoint.subtract(this.camera.upVector.cross(this.camera.direction).normalize());
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:translate3d('+this.revolveAroundPoint.x+","+this.revolveAroundPoint.y+","+this.revolveAroundPoint.z+");");
				if(this.mode == "ego") cube.setAttribute('style' , 'transform:scale3d(0,0,0););');
			}
            break;
        case 37: // left
        case 65: // a
			camera.position = camera.position.add(this.camera.upVector.cross(this.camera.direction).normalize());
			this.revolveAroundPoint = this.revolveAroundPoint.add(this.camera.upVector.cross(this.camera.direction).normalize());
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:translate3d('+this.revolveAroundPoint.x+","+this.revolveAroundPoint.y+","+this.revolveAroundPoint.z+");");
				if(this.mode == "ego") cube.setAttribute('style' , 'transform:scale3d(0,0,0););');
			}

            break;
        case 40: // down
        case 83: // s
            camera.position = camera.position.subtract(dir.scale(this.zoomSpeed));
            break;

        case 82: //r
            camera.position = camera.position.add(this.camera.upVector.normalize());
            this.revolveAroundPoint = this.revolveAroundPoint.add(this.camera.upVector.normalize());
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:translate3d('+this.revolveAroundPoint.x+","+this.revolveAroundPoint.y+","+this.revolveAroundPoint.z+");");
				if(this.mode == "ego") cube.setAttribute('style' , 'transform:scale3d(0,0,0););');

			}

        	break;
        case 70: //f
        	camera.position = camera.position.subtract(this.camera.upVector.normalize());
        	this.revolveAroundPoint = this.revolveAroundPoint.subtract(this.camera.upVector.normalize());
			var cube = document.getElementById("x");
			if(cube)
			{
				cube.setAttribute('style' , 'transform:translate3d('+this.revolveAroundPoint.x+","+this.revolveAroundPoint.y+","+this.revolveAroundPoint.z+");");
				if(this.mode == "ego") cube.setAttribute('style' , 'transform:scale3d(0,0,0););');
			}
        	break;

        default:
            return;
        }
        this.needUpdate = true;
    }
    this.stopEvent(e);
};

XML3D.Xml3dSceneController.prototype.keyUpHandling = function(e) {
	var KeyID = e.keyCode;
	switch (KeyID) 
	{
        case 18:
        	this.altDown = false;
        	break;
        default:
            return;
    }       
};

//-----------------------------------------------------
//attach/detach of all controllers
//-----------------------------------------------------
XML3D.Xml3dSceneController.attachAllControllers = function() {

    XML3D.debug.logInfo("Attaching all active controllers to xml3d elements.");

    var xml3dList = Array.prototype.slice.call( document.getElementsByTagNameNS(XML3D.xml3dNS, 'xml3d') );
    for(var node in xml3dList) {
        XML3D.Xml3dSceneController.controllers[node].attach();
    }
};

XML3D.Xml3dSceneController.detachAllControllers = function() {

    XML3D.debug.logInfo("Detaching all active controllers from xml3d elements.");

    var xml3dList = Array.prototype.slice.call( document.getElementsByTagNameNS(XML3D.xml3dNS, 'xml3d') );
    for(var node in xml3dList) {
        XML3D.Xml3dSceneController.controllers[node].detach();
    }
};

XML3D.Xml3dSceneController.getController = function(xml3d) {

    var xml3dList = Array.prototype.slice.call( document.getElementsByTagNameNS(XML3D.xml3dNS, 'xml3d') );
    for(var node in xml3dList) {

        var ctrl = XML3D.Xml3dSceneController.controllers[node];
        if(xml3d == ctrl.xml3d)
            return ctrl;
    }

    return null;
};

//-----------------------------------------------------
//loading/unloading
//-----------------------------------------------------

(function() {

    var onload = function() {

        var xml3dList = Array.prototype.slice.call( document.querySelectorAll('xml3d') );

        XML3D.Xml3dSceneController.controllers = new Array();
        for(var i in xml3dList) {
            XML3D.debug.logInfo("Attaching Controller to xml3d element.");
            XML3D.Xml3dSceneController.controllers[i] = new XML3D.Xml3dSceneController(xml3dList[i]);
        };
    };
    var onunload = function() {
        for(var i in XML3D.Xml3dSceneController.controllers)
        {
            XML3D.Xml3dSceneController.controllers[i].detach();
        }
    };

    window.addEventListener('load', onload, false);
    window.addEventListener('unload', onunload, false);
    window.addEventListener('reload', onunload, false);

})();

/***********************************************************************/
