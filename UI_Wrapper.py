# Ryan Clark - rclark32@asu.edu
# GUI Interface for laser-fff postprocessor

import tkinter as tk
from tkinter import filedialog
from PostProcessor import PostProcessor

class GCodePostprocessorUI:
    def __init__(self, master):
        self.master = master
        master.title("Laser FFF Postprocessor")

        self.file_path = None
        self.rotation_speed = tk.StringVar(value="3333.33333") #Set default values
        self.outer_wall_speed = tk.StringVar(value="10")
        self.layers_between_finish = tk.StringVar(value="2")
        self.visualize_toolpath = tk.BooleanVar(value=True)

        self.button_margin_size = 15

        # Title label
        self.title_label = tk.Label(master, text="Laser FFF Postprocessor", font=("Arial", 16))
        self.title_label.pack(pady=self.button_margin_size)

        # Create select file button
        self.select_file_button = tk.Button(master, text="Select GCode File", command=self.select_file)
        self.select_file_button.pack(pady=self.button_margin_size)

        # Textbox for Rotation Speed
        self.rotation_speed_label = tk.Label(master, text="Rotation Speed (deg/s):")
        self.rotation_speed_label.pack(pady=self.button_margin_size)
        self.rotation_speed_entry = tk.Entry(master, textvariable=self.rotation_speed)
        self.rotation_speed_entry.pack(pady=self.button_margin_size)

        # Textbox for Outer Wall Print Speed
        self.outer_wall_speed_label = tk.Label(master, text="Outer Wall Print Speed (mm/s):")
        self.outer_wall_speed_label.pack(pady=self.button_margin_size)
        self.outer_wall_speed_entry = tk.Entry(master, textvariable=self.outer_wall_speed)
        self.outer_wall_speed_entry.pack(pady=self.button_margin_size)

        # Textbox for Layers Between Surface Finish
        self.layers_between_finish_label = tk.Label(master, text="Layers Between Surface Finish:")
        self.layers_between_finish_label.pack(pady=self.button_margin_size)
        self.layers_between_finish_entry = tk.Entry(master, textvariable=self.layers_between_finish)
        self.layers_between_finish_entry.pack(pady=self.button_margin_size)

        # Checkbox for Visualize Toolpath
        self.visualize_toolpath_checkbox = tk.Checkbutton(master, text="Visualize Toolpath", variable=self.visualize_toolpath)
        self.visualize_toolpath_checkbox.pack(pady=self.button_margin_size)

        # Submit button
        self.submit_button = tk.Button(master, text="Submit", command=self.submit_form)
        self.submit_button.pack(pady=self.button_margin_size)

    def select_file(self):
        # Open a file dialog to select a GCode file
        self.file_path = filedialog.askopenfilename(filetypes=[("GCode files", "*.gcode")])

        if self.file_path:
            print(f"Selected file: {self.file_path}")

    def generate_output_filepath(self, input_filepath):
        if input_filepath.lower().endswith(".gcode"):
            # Remove the ".gcode" extension and append "-LaserFFF.gcode"
            output_filepath = input_filepath[:-(len(".gcode"))] + "-LaserFFF.gcode"
            return output_filepath
        else:
            TypeError("Error: input filepath must be of type '.gcode'")

    def submit_form(self):
        # Get values from UI
        rotation_speed = float(self.rotation_speed_entry.get())
        outer_wall_speed = float(self.outer_wall_speed_entry.get())
        layers_between_finish = int(self.layers_between_finish_entry.get())
        visualize_layers = self.visualize_toolpath.get()

        # Create dictionary with settings
        cura_settings = {
            "lf_rotation_speed": rotation_speed,
            "lf_outer_wall_print_speed": outer_wall_speed,
            "lf_layers_between_surface_finish": layers_between_finish,
            "lf_visualize_layers": visualize_layers,
        }


        output_filepath = self.generate_output_filepath(self.file_path) # Add "-laserFFF to the end of the filename"

        postprocessor = PostProcessor()
        postprocessor.input_gcode_path = self.file_path
        postprocessor.output_gcode_path = output_filepath  #

        # Add user settings to postprocessor
        postprocessor.get_cura_settings(cura_settings)

        # Postprocess gcode
        postprocessor.process_gcode()


# Run & create application
root = tk.Tk()
app = GCodePostprocessorUI(root)

root.mainloop()
