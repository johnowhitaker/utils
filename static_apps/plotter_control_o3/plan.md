I want to make a webUI for my hanging plotter to these specs:
* Three tabs - 'Img2SVG', 'SVG2GCODE' and 'Plot Control'
* Img2SVG lets you drag on or choose an image and turns it into an SVG. For now use a dummy function that returns a square made from a single polyline.
* SVG2GCODE that let's you scale and shift the SVG (with preview) to fit in the drawing bounds. The math is a little tricky, I'll get to it
* Plot control has ways of manually controlling the motors using GCODE, and a textarea to paste GCODE (e.g. from tab 2) with a button to send it.

Specifics
* V plotter is defined by distance between motors, and initial string lengths l1 and l2. 
* The motors are controlled by G-CODE, but sending 'G1 X100 Y0' moves the X motor "100mm". I set them to '100 steps per mm' in the printer software, but that equates to half a revolution. These now have 12mm diameter pulleys on, so a move of '100mm' turns into 1000 steps turns into 5 revolutions turns into 5 * pi * 12 mm of string let out. Since the second string length is fixed, this will trace out a bit of an arc. 
* Still, I want the option to send GCODE for +10 and +100 for both X and Y axes, and to assign a new position to the current position (using code G92) with buttons - for the rest I can manually type in GCODE. 
* Use webserial to list serial ports and let me choose which one to connect to
* FOr all GCODE commands, listen in and log stuff in the console. 