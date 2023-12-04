# Laser FFF Post Processor
# Ryan Clark - rclark32@asu.edu

import re
import os

import math
import argparse  # Used to simulate args during testing
from collections import OrderedDict

# Default gcode filepath for testing:
inputFilePath = "C:/Users/recla/Downloads/Gcode_ref/Venchy.gcode"
outputFilePath = "C:/Users/recla/Downloads/Gcode_ref/Outputfiles/testOutputVenchy.gcode"


class PostProcessor:
    def __init__(self) -> None:

        # Regular expressions:
        self._layer_num_regexp = re.compile(r"^;LAYER:(\d*)")
        # Get section type after ;TYPE:WALL-OUTER
        self._section_type_regexp = re.compile(r";TYPE:([^;\n]+)")
        # Capture a block of gcode after a TYPE comment (even if the next line is a MESH comment)
        self._type_block_regexp = re.compile(
            r";TYPE:[^;\n]+([\s\S]*?)(?=(?:;TYPE:|;MESH:|;TIME_ELAPSED:|$)(?<!;TYPE:))")

        # Printer specific Gcode commands:
        self._laser_enable = 'M60; Laser enable'
        self._laser_disable = 'M61; Laser disable'

        self._rotate_command = 'A'

        self._rotation_offset = -90  # Rotation offset for outer wall Could be -90? maybe radians?
        self._base_rotation = 90  # Assumes positive Y is 0 degrees - Change if 0 degrees is in a different location

        # Initialization
        self._extruder_state = False
        self.added_commands = 0
        self.toolpaths = []

    def process_gcode(self):  # Used by UI Wrapper
        gcode_list = self.make_gcode_list(self.input_gcode_path)
        modified_gcode_list = self.process_gcode_list(gcode_list)
        self.write_gcode_to_file(self.output_gcode_path, modified_gcode_list)
        self.visualize_gcode(self.toolpaths)

    def visualize_gcode(self, gcode):
        if self.lf_visualize_layers:
            from Visualizer import visualize_toolpaths
            visualize_toolpaths(gcode)


    def get_gcode_file_path(self, args) -> None:
        for key, value in vars(args).items():
            if key in ["input_gcode_path", "output_gcode_path"]:  # Do not modify these two
                continue
            setattr(self, key, value)

    def make_gcode_list(self, filepath) -> list[str]:
        gcode = ""
        with open(filepath, "r") as file:
            gcode = file.read()
        gcode_list = gcode.split(";LAYER:")
        gcode_list = [l if i == 0 else ";LAYER:" + l for i, l in enumerate(gcode_list)]
        return gcode_list

    def get_cura_settings(self, cura_settings) -> None:
        if type(cura_settings) is dict: # For GUI:
            self.lf_rotation_speed = cura_settings.get("lf_rotation_speed", 360)
            self.lf_outer_wall_print_speed = cura_settings.get("lf_outer_wall_print_speed", 100)
            self.lf_layers_between_surface_finish = cura_settings.get("lf_layers_between_surface_finish", 2)
            self.lf_visualize_layers = cura_settings.get("lf_visualize_layers", True)
        else: # For Cura:
            self.lf_rotation_speed = cura_settings.getProperty("lf_rotation_speed", "value")
            self.lf_outer_wall_print_speed = cura_settings.getProperty("lf_outer_wall_print_speed", "value")
            self.lf_layers_between_surface_finish = cura_settings.getProperty("lf_layers_between_surface_finish",
                                                                              "value")
            self.lf_visualize_layers = cura_settings.getProperty("lf_visualize_layers", "value")

    def parse_line(self, line) -> (str, OrderedDict, str):
        original = line.split(";")[0]
        try:
            comment = "; " + line.split(";")[1]
        except:
            comment = "" # If there isn't already a comment on the line, don't append anything

        split_commands = original.strip().split(" ")

        try:
            args = OrderedDict((a[0], float(a[1:])) for a in split_commands)
        except:
            args = OrderedDict()

        return (original, args, comment)

    def write_gcode_to_file(self, filepath, gcode_list) -> None:
        gcode_joined = ""
        for g in gcode_list: # For layer in list
            tmp = ""
            for l in g: # For line in layer, add \n
                tmp += '\n' + l
            gcode_joined += tmp

        with open(filepath, "w") as f:
            f.write(gcode_joined)

    def _calculate_rotation(self, old_x, old_y, new_x, new_y) -> float:
        direction = math.degrees(math.atan2((new_x - old_x), (new_y - old_y)))
        if (old_y < new_y):
            direction += 180
        return round(direction % 360, 3)

    def _get_laser_gcode(self, command, E) -> str:
        if E <= 0:
            return (self._laser_disable)  # If retraction or no extrusion, return 0
        elif command:
            return (self._laser_enable)  # If G1, enable laser
        else:
            return (self._laser_disable)  # G0 - disable laser

    def process_gcode_list(self, gcode_list):
        sum_size = 0
        biggest = 0
        for s in gcode_list:
            sum_size += len(s)
            if len(s) > biggest:
                biggest = len(s)

        linebuffer = []

        old_x = 0
        old_y = 0
        old_A = 0
        old_G = 0
        old_E = 0

        new_x = 0
        new_y = 0
        new_A = 0
        new_G = 0
        new_E = 0

        delta_E = 0

        Z = 0
        new_F = 0
        old_F = 0

        surface_finish = False
        outer_wall = False
        current_layer_num = 0

        modified_gcode_list = []
        rotation_offset = self._base_rotation

        visualize = self.lf_visualize_layers

        toolpath = []
        vs_color = 1

        for current_layer, layer_gcode in enumerate(gcode_list):  # Iterate through LAYERS in gcode
            lines = layer_gcode.split("\n")

            for line_nr, line in enumerate(lines):  # iterate through LINES in each LAYER
                changed = False

                layer_line = self._layer_num_regexp.match(line)  # Check if this line is a ;LAYER: comment
                type_line = self._section_type_regexp.match(line)  # Get current section type

                if layer_line:  # If it's a layer line
                    try:
                        current_layer_num = int(layer_line.groups()[0])
                    except:
                        current_layer_num = 0

                    if current_layer_num == 0:  # If first layer
                        linebuffer = [";LAYER:0"]

                    elif current_layer_num < 0: # If it's a raft or similar (negative layer)
                        linebuffer.append(line) # Put the line back

                    else:  # if not the first layer, but is still a new layer
                        linebuffer.append(";LAYER:" + str(current_layer_num))

                        # If this layer is a surface finish layer (every X layers)
                        if current_layer_num % (self.lf_layers_between_surface_finish + 1) == 0:  # Layers are 0 indexed
                            rotation_offset = self._rotation_offset + self._base_rotation  # Add 90 degree offset to standard offset
                            linebuffer.append("; Surface finish layer")
                            self.added_commands += 1
                            surface_finish = True
                        else:  # Otherwise, return to orientation in line with motion
                            rotation_offset = self._base_rotation
                            surface_finish = False

                elif type_line:
                    current_type = type_line.groups()[0].strip()
                    linebuffer.append(
                        ";TYPE:" + current_type)  # Equivalent to linebuffer.append(line), used as a sanity check

                    # print("TYPE is ", current_type)
                    if current_type == "WALL-OUTER":
                        outer_wall = True
                        vs_color = 0
                    elif current_type == "WALL-INNER":
                        outer_wall = False
                        vs_color = 1
                    elif current_type == "SKIN":
                        outer_wall = False
                        vs_color = 2
                    elif current_type == "FILL":
                        outer_wall = False
                        vs_color = 3
                    elif "SUPPORT" in current_type:
                        vs_color = 4
                        outer_wall = False
                    else:
                        vs_color = 4 # Everything else (like bed adhesion types, are colored with support material)
                        outer_wall = False


                elif (line.split(" ")[0] in ['G0', 'G1']):  # If it's a G line
                    splitline = line.split(" ")

                    old_A = new_A

                    original_line, command, comment = self.parse_line(line)  # Split gcode line into commands

                    extrude_state_changed_flag = False
                    calculate_rotation_flag = False
                    line_updated_flag = False
                    no_feedrate_in_line = False

                    if 'G' in command:
                        old_G = new_G
                        new_G = int(command['G'])
                        if new_G != old_G:
                            extrude_state_changed_flag = True

                    if 'X' in command:
                        old_x = new_x
                        new_x = command['X']
                        calculate_rotation_flag = True

                    if 'Y' in command:
                        old_y = new_y
                        new_y = command['Y']
                        calculate_rotation_flag = True  # recalculate angle - TODO? disable on G0

                    if 'Z' in command:
                        Z = command['Z']  # Currently unused

                    if 'E' in command:
                        old_E = new_E
                        new_E = command['E']
                        delta_E = new_E - old_E
                    else:
                        delta_E = 0  # TODO is this true? Assumes absolute extruder positioning

                    if 'F' in command:
                        old_F = new_F
                        new_F = command['F']
                        no_feedrate_in_line = False
                    else:
                        no_feedrate_in_line = True

                    if calculate_rotation_flag:
                        new_A = self._calculate_rotation(old_x, old_y, new_x, new_y)

                        if outer_wall is True:
                            new_A += rotation_offset
                            new_A = new_A % 360
                        else:
                            new_A += self._base_rotation
                            new_A = new_A % 360

                        rotation_speed = self.lf_outer_wall_print_speed * 60  # Convert to deg/min from deg/s

                        linebuffer.append(f'G0 A{new_A} F{rotation_speed}')
                        self.added_commands += 1

                        # linebuffer.append(line) # Add original line w/ comment back in

                    if extrude_state_changed_flag:
                        # Toggle laser depending on deposition state
                        linebuffer.append(self._get_laser_gcode(new_G, delta_E))
                        self.added_commands += 1

                    if no_feedrate_in_line == True:
                        linebuffer.append(f"{original_line} F{new_F}") # Add original feedrate after a rotate command
                    else:
                        linebuffer.append(line) # Or just add the original line

                    if visualize:
                        path = {"x": new_x, "y": new_y, "extruder_angle": new_A, "extrude": delta_E > 0,
                                "color": vs_color, "surface_finish": surface_finish}
                        toolpath.append(path)


                else:  # If it's another command (M, comment, etc.)
                    linebuffer.append(line)

            modified_gcode_list.append(linebuffer)
            linebuffer = []

            if visualize: # If visualizing is on, then add to toolpath list
                self.toolpaths.append(toolpath)
                toolpath = []


        self.toolpaths.pop(0) # remove the first, empty value
        return modified_gcode_list


if __name__ == "__main__":

    # The following is only used for debugging or running the file independently
    parser = argparse.ArgumentParser(description="Postprocess Laser FFF Gcode - Run as main")

    parser.add_argument("--input_gcode_path", action="store",
                        default=inputFilePath, type=str)
    parser.add_argument("--output_gcode_path", action="store",
                        default=outputFilePath, type=str)

    parser.add_argument("--lf_rotation_speed", action="store", default=360, type=float)
    parser.add_argument("--lf_outer_wall_print_speed", action="store", default=10, type=float)
    parser.add_argument("--lf_layers_between_surface_finish", action="store", default=2, type=int)
    parser.add_argument("--lf_visualize_layers", action="store", default=True, type=bool)



    args = parser.parse_args()
    post_processor = PostProcessor()
    post_processor.get_gcode_file_path(args)

    gcode_list = post_processor.make_gcode_list(args.input_gcode_path)
    modified_gcode_list = post_processor.process_gcode_list(gcode_list)

    post_processor.write_gcode_to_file(args.output_gcode_path, modified_gcode_list)

    if post_processor.lf_visualize_layers:
        from Visualizer import visualize_toolpaths
        visualize_toolpaths(post_processor.toolpaths)
