////////////
///Readme///
////////////

extension to the xml3D web client
creates handle (slider + play button) to scrub through animations
& adds trackball and first person navigation
developed in the scope of the seminar "Character Animation"
Author: Jonas Trottnow
Supervisor: Alexis Heloir

-------------------------------------------------------------------------------------

An example export is provided in the folder example_export in the git repository.
Host this folder on a web server to be able to play around with the implementations.

-------------------------------------------------------------------------------------

USAGE:

How to: Use the animation handles:
A slider and a play button will be displayed at the lower right corner of the window.
The slider can be grabbed at any time (while playing or pausing) to jump to a specific 
time in the animation.
By clicking on the play button the animation can be paused and restarted.
Orange button means: is playing
Gray button means: is paused

How to: Use the trackball and fist person navigation:
After the setup the navigation modes can be choosen with the numbers on the keyboard.
1: first person navigation
	- use 'W', 'A', 'S' & 'D' keys to navigate left, right, forward and backward
	- use 'R' & 'F' to navigate up and down
	- use the mouse to rotate the view (hold left mouse button to activate)
2: trackball
	- press and hold the 'alt' key and click on a scene object with the left mouse button 
	  to set the rotate-around point to the hitpoint on the object
	- use the mouse to rotate around the rotate-around point with the trackball interface 
	  (hold left mouse button to activate)

-------------------------------------------------------------------------------------

EXPORT:

How to: Export scene from blender:
1. Zip the folder io_scene_xml3d (find it in the 'addons' folder of this git repository)
2. Import the blender extension (the generated zip file) to blender as described in the 
   main readme.md file

How to: Setup the main html file for using the animation handles:
1. register the animated objects within the existing docAnims javascript variable:
	e.g.:
	|	<script>
	|		var docAnims = {
	|			"anim armature" : {max: 250, off: 0, factor: 50.0},
	|		}
	|	</script>
	
	The specified name (in the example: "anim armature") should be the name of the class 
	of the animKey float:
	|	animKey is normally defined in the html body:
	|	<assetdata name="Armature">
	|		<float name="animKey" class="anim armature">0.0</float>
	|	</assetdata>
	max: defines the last keyframe to be played of this animation, before starting from 
	     the beginning again
	off: defines a keyframe offset (usefull if multiple animated objects are present in 
		 the scene, that should not start at the same time)
	factor: specifies the speed of the animation in fps (frames per second)
2. done! The animation handle should now move according to the specified parameters.

How to: Setup the main html file for using the trackball and first person modes:
1. nothing has to be done to use the interaction modes
2. to visualize the rotate-around point of the trackball implementation an xml3D object 
   with id="x" can be added, which will then automatically be used as point visualizer
   (have a look at the index.html file of the example_export to see how to add a cube as 
   rotate-around point visualizer to the scene)
   

-------------------------------------------------------------------------------------

BUG AVOIDING:

The exporter code provided by ksons has 2 minor bugs that can be easily avoided while 
using blender:

1. The web client will break if a bone (armature) animation is exported in which contains 
   a bone to which no vertices are assigned.
   -> assign at least one vertex to each bone
	
2. If the camera is translated & rotated within blender, the transformations will not be 
   applied to the xml3D camera, but on a group around that camera.
   This will break the rotation and trackball interface in the web client (rotations will 
   be wrong and setting the rotate-around point will seem to be wrong)
   -> export the camera at the origin (camera global position = (0,0,0) ) and apply the 
      camera translations in the web client