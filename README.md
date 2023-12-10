# LaserFFF-Gcode-Postprocessor
A gcode postprocessor for a Laser-FFF 3D printer, with built in visualizer. Compatible with Cura or standalone

## Program Background
This program is a gcode Postprocessor for a custom 3D printer. This printer is Dr. Pu Han's, from Dr. Keng Hsu's lab on the ASU Polytechnic campus. This Laser FFF printer is like a normal 3D printer, but uses an orbiting laser to melt or soften the plastic below the deposition site. An example is shown in the video below. This program provides extra control over the laser, and also adds a custom visualizer that shows a preview of the laser orientation relative to the toolpath

[Video Link](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Videos/Laser-FFF-Demonstration.mp4)



## Program Usage
Currently, this program is made to standalone, but is designed for future integration with Cura (version 4.12). This program provides 4 new settings:

**Rotation Speed (deg/s)** - max speed to rotate the laser head
**Outer wall print speed (mm/s)** - max speed to print the outer wall
**Layers between surface finish** - Every X layers, perform a surface finish layer (rotates the laser 90 degrees to improve surface finish)
**Visualize** - Runs custom visualizer to show laser orientation


The program consists of 3 files: 

[PostProcessor.py](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/PostProcessor.py)

[Visualizer.py](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Visualizer.py)

[UI_Wrapper.py](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/UI_Wrapper.py)


PostProcessor and Visualizer are designed to be incorporated into Cura. UI_Wrapper provides functionality as a standalone program.



## Demonstration & Examples

Some example gcode files are shown below. These were sliced for a Creality Ender 3, but the postprocessor still functions the same.

[Input Gcode](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Gcode-Examples/LFFF-Benchy.gcode) - Benchy (.stl from [Creative Tools on Thingiverse](https://www.thingiverse.com/thing:763622/files))

[Processed Gcode](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Gcode-Examples/LFFF-Benchy-LaserFFF.gcode)


[Input Gcode](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Gcode-Examples/LFFF-Elephant.gcode) - Elephant (.stl from [LeFabShop on Thingiverse](https://www.thingiverse.com/thing:257911/files))

[Output Gcode](https://github.com/rclark32/LaserFFF-Gcode-Postprocessor/blob/main/Gcode-Examples/LFFF-Elephant-LaserFFF.gcode)

## Video demonstration:
https://youtu.be/7vI6lZpDN5w

### Libraries Used: 
Numpy, argparse, tkinter, pygame, re, os, sys

