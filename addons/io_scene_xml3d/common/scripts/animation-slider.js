/* extension to xml3D web client
 * creates handle (slider) to scrub through animation
 * developed in the scope of the seminar "Character Animation"
 * Author: Jonas Trottnow
 * Supervisor: Alexis Heloir
 */
 
var mytime = 0.0;
var lastTime = Date.now();

var divid;
var playPauseButton;
var manualMove = false;
var xFactor = 0.0;
var maxX;
var pause = false;

var reqAniFrame = (window.requestAnimationFrame || window.mozRequestAnimationFrame || window.webkitRequestAnimationFrame).bind(window);


//set multiple attributes of an html element
Element.prototype.setAttributes = function (attrs) {
    for (var idx in attrs) {
        if ((idx === 'styles' || idx === 'style') && typeof attrs[idx] === 'object') {
            for (var prop in attrs[idx]){this.style[prop] = attrs[idx][prop];}
        } else if (idx === 'html') {
            this.innerHTML = attrs[idx];
        } else {
            this.setAttribute(idx, attrs[idx]);
        }
    }
};

//add slider html to webpage
window.addEventListener("load", function()
{
	// add the GUI elements to the body of the html document
	var caption = document.createElement('div');
	caption.innerHTML = '<p style="color:white;">Drag to scrub through animation:</p>';
	caption.setAttribute('style' , 'height:30px; width:280px; z-index:2; position:fixed; right:100px; bottom:130px;');
	document.body.appendChild(caption);
	
	var container = document.createElement('div');
	container.setAttribute('style' , 'height:30px; width:280px; z-index:2; position:fixed; right:70px; bottom:100px; -webkit-user-select: none; -moz-user-select: none; -o-user-select: none; -ms-user-select: none; -khtml-user-select: none; user-select: none;');
	container.setAttribute('id', 'dragContainer');
	document.body.appendChild(container);
	
	var line = document.createElement('div');
	line.innerHTML = "<p> </p>";
	line.setAttribute('style' , 'height:2px; width:100%; top:49%; position:absolute; background-color:black; -webkit-user-select: none; -moz-user-select: none; -o-user-select: none; -ms-user-select: none; -khtml-user-select: none; user-select: none;');
	document.getElementById("dragContainer").appendChild(line);
	
	divid = document.createElement('div');
	divid.innerHTML = "<p> </p>";
	divid.setAttribute('style' , 'height:30px; left:0px; width:10px; top:0px; position:absolute; background-color:gray; -webkit-user-select: none; -moz-user-select: none; -o-user-select: none; -ms-user-select: none; -khtml-user-select: none; user-select: none;');
	divid.setAttribute('id', 'animDrag');
	divid.setAttribute('onmousedown', 'startMoving(this,"dragContainer",event)');
	divid.setAttribute('onmouseup', 'stopMoving("dragContainer")');
	document.getElementById("dragContainer").appendChild(divid);
	
	playPauseButton = document.createElement('div');
	playPauseButton.innerHTML = "<p></p>";
	playPauseButton.setAttributes({
		'style':{
			'height':'0px',
			'left':'-30px',
			'width':'0px',
			'top':'5px',
			'position':'absolute',
			'-webkit-user-select': 'none',
			'-moz-user-select': 'none',
			'-o-user-select': 'none',
			'-ms-user-select': 'none',
			'-khtml-user-select': 'none',
			'user-select': 'none',
			'border-top': '10px solid transparent',
			'border-left': '20px solid orange',
			'border-bottom': '10px solid transparent'
		},
		'onclick': 'playPause()',
		'id': 'playPause'
	});
	document.getElementById("dragContainer").appendChild(playPauseButton);
	
	//initialize variables
	maxX = parseInt(document.getElementById("dragContainer").style.width);

});

//change the color of the playbutton
function playPause()
{
	pause = !pause;
	if(pause)
	playPauseButton.setAttributes({
		'style':{
			'border-left': '20px solid gray'
		}
	});
	else
	playPauseButton.setAttributes({
		'style':{
			'border-left': '20px solid orange'
		}
	});
}

//update the animation of all registered objects
function updateAnim() {
	diff = 0;
  if(!pause)
  {
	  diff = Date.now() - lastTime;
  }
  lastTime = Date.now();

  var value;
  var newPos;
  var stop = 0;
  for(var id in docAnims){
	var entry = docAnims[id];
	if(!manualMove)
	{
		mytime += diff / 1200.0;
	}
	else
	{
		mytime = ((xFactor)*entry.max)/entry.factor;
	}
	value = (mytime * entry.factor + entry.off) % entry.max;
	if(stop == 0) {newPos = Math.floor(((value + 0.0) / (entry.max + 0.0))*(maxX + 0.0)); stop = 1;}
	document.getElementsByClassName(id)[0].innerHTML = value;
  }
  if(divid)
  {
	divid.style.left = newPos + 'px';
  }
  reqAniFrame(updateAnim);
}


reqAniFrame(updateAnim);


// initialize slider movement (start scrubbing)
function startMoving(divid,container,evt){
	
	evt = evt || window.event;
	var posX = evt.clientX,
		posY = evt.clientY,
	divTop = divid.style.top,
	divLeft = divid.style.left,
	eWi = parseInt(divid.style.width),
	eHe = parseInt(divid.style.height),
	cWi = parseInt(document.getElementById(container).style.width),
	cHe = parseInt(document.getElementById(container).style.height);
	document.getElementById(container).style.cursor='move';
	divTop = divTop.replace('px','');
	divLeft = divLeft.replace('px','');
	var diffX = posX - divLeft,
		diffY = posY - divTop;
	document.onmousemove = function(evt){
		evt = evt || window.event;
		var posX = evt.clientX,
			posY = evt.clientY,
			aX = posX - diffX,
			aY = posY - diffY;
			if (aX < 0) aX = 0;
			if (aY < 0) aY = 0;
			if (aX + eWi > cWi) aX = cWi - eWi;
			if (aY + eHe > cHe) aY = cHe -eHe;
		xFactor = (aX  + 0.0)/(maxX + 0.0);
		manualMove = true;
	}
}

// go back to normal playback after scrubbing
function stopMoving(container){
	manualMove = false;
	var a = document.createElement('script');
	document.getElementById(container).style.cursor='default';
	document.onmousemove = function(){}
}