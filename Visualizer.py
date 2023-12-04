# Ryan Clark - rclark32@asu.edu
# Visualizer for laser fff postprocessor

import pygame
import sys
import math


def deg_to_rad(degrees):
    return math.radians(degrees)

def draw_toolpath(path, current_index, colors, screen): # Draws the entire toolpath on the screen
    prev_x, prev_y = None, None
    for i, point in enumerate(path):
        x, y = point["x"], point["y"]
        color = colors[point["color"]]

        if i == current_index:
            # Draw the extruder as a small red circle
            pygame.draw.circle(screen, (255, 0, 0), (x, y), 4)

            # Draw a line indicating extrusion direction
            angle_rad = deg_to_rad(360-point["extruder_angle"])
            extrusion_length = 30
            end_x = int(x + extrusion_length * math.cos(angle_rad))
            end_y = int(y + extrusion_length * math.sin(angle_rad))
            pygame.draw.line(screen, (255, 0, 0), (x, y), (end_x, end_y), 2)

        if prev_x is not None and prev_y is not None and point["extrude"]:
            # Draw a line from the previous point to the current point if both points have extrusion enabled
            pygame.draw.line(screen, color, (prev_x, prev_y), (x, y), 1)

        # Update the previous point variables
        prev_x, prev_y = x, y


# Function to check if a point is inside a rectangle
def is_point_inside_rect(point, rect):
    x, y = point
    rx, ry, rw, rh = rect
    return rx < x < rx + rw and ry < y < ry + rh

# Function to update the slider position based on the current index
def update_slider_position(index, max_index, slider_rect, dims):
    slider_width = slider_rect[2]
    position = (index / max_index) * (dims["width"] - slider_width)
    return position, slider_rect[1], slider_width, slider_rect[3]

def display_current_layer(screen, font, current_layer, num_layers, dims):
    layer_text = font.render(f"Layer: {current_layer + 1}/{num_layers}", True, (0, 0, 0))
    layer_rect = layer_text.get_rect(topright=(dims["width"] - 10, 10))
    screen.blit(layer_text, layer_rect)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def display_color_swatches(screen, font, dims, colors, color_names):
    swatch_size = 20
    swatch_margin = 5
    text_margin = 5
    offset = 35
    width = dims["width"]

    for i, color in enumerate(colors):
        swatch_rect = pygame.Rect(width - swatch_size - swatch_margin, i * (swatch_size + swatch_margin) + offset, swatch_size,
                                  swatch_size)
        pygame.draw.rect(screen, color, swatch_rect)

        text = font.render(color_names[i], True, (0, 0, 0))
        text_rect = text.get_rect(
            midright=(width - swatch_size - swatch_margin - text_margin,
                      i * (swatch_size + swatch_margin) + swatch_size / 2 + offset)
        )
        screen.blit(text, text_rect)


def find_part_bounds(toolpaths):
    # Initialize min and max values for x and y
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    for i, layer in enumerate(toolpaths):
        if i >= len(toolpaths) - 1:
            continue
        for j, toolpath in enumerate(layer):
            for k in range(len(toolpath)):
                try:
                    x = toolpath["x"]
                    y = toolpath["y"]
                except:
                    print(toolpath)
                # Update min and max values for x and y
                """if x < min_x:
                    print(f"Smaller x on i {i}, j {j}, k {k}, x: {x}")
                if y < min_y:
                    print(f"Smaller y on i {i}, j {j}, k {k}, y: {y}")"""

                min_x = min(min_x, x)
                max_x = max(max_x, x)

                min_y = min(min_y, y)
                max_y = max(max_y, y)

    part_bounds = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }
    return part_bounds

def scale_toolpaths(toolpaths,dims):
    scaled_paths = []
    width = dims["width"]  # Screen width
    height = dims["height"]  # Screen height

    part_bounds = find_part_bounds(toolpaths)
    printer_width = part_bounds["max_x"] - part_bounds["min_x"]
    printer_height = part_bounds["max_y"] - part_bounds["min_y"]


    margin = 25

    # Calculate the scale factor for the x and y axes to fit the entire screen
    scale_x = (width - margin * 2) / (part_bounds["max_x"] - part_bounds["min_x"])
    scale_y = (height - margin * 2) / (part_bounds["max_y"] - part_bounds["min_y"])

    # Choose the smallest scale factor
    scale = min(scale_x, scale_y)

    # Calculate the new x and y coordinates



    for layer in toolpaths:
        scaled_layer = []
        for t in layer:
            new_x = (t["x"] - part_bounds["min_x"]) * scale + margin
            new_y = (t["y"] - part_bounds["min_y"]) * scale + margin

            #new_x = (t["x"] - part_bounds["min_x"]) * (width - margin * 2) / printer_width + margin
            #new_y = (t["y"] - part_bounds["min_y"]) * (height - margin * 2) / printer_height + margin

            new_a = t["extruder_angle"]
            new_e = t["extrude"]
            new_c = t["color"]
            new_sf = t["surface_finish"]
            tmp = {"x": new_x, "y": new_y, "extruder_angle": new_a, "extrude": new_e > 0, "color": new_c, "surface_finish": new_sf}

            scaled_layer.append(tmp)
        scaled_paths.append(scaled_layer)
    return(scaled_paths)


def visualize_toolpaths(toolpaths):
    current_layer = 0
    index = 0
    paused = False
    sliding = False
    speed = .5 # Adjust to change framerate, default 1

    running = True
    pygame.init()

    width, height = 800, 600  # Screen size
    dims = {"height": height, "width": width}  # To pass to other functions

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Toolpath Visualizer")

    scaled_toolpaths = scale_toolpaths(toolpaths, dims)  # Center and scale toolpaths to window size

    # Define colors for different toolpaths
    """yellow =  (255,166,48)
    blue = (72, 169, 166)
    dark_blue = (10,36,99)
    red = (137,6,32)
    green = (23,48,28)"""

    yellow = hex_to_rgb("FEA82F")
    blue = hex_to_rgb("4D6CFA")
    green = hex_to_rgb("415D43")
    red = hex_to_rgb("DB3A34")
    black = hex_to_rgb("07090F")

    white = (255, 255, 255)

    colors = [red, blue, black, green, yellow]
    color_names = ["Outer Wall", "Inner Wall", "Fill", "Skin", "Support"]

    clock = pygame.time.Clock()

    # Pause button rectangle (bottom middle)
    pause_button_rect = pygame.Rect(width // 2 - 40, height - 40, 80, 30)

    # Slider rectangle
    slider_rect = (0, height - 20, width, 20)
    slider_handle_rect = (0, height - 20, 20, 20)
    offset_x, offset_y = 0, 0

    font = pygame.font.Font(None, 24) # Font size

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN: # On click
                if event.button == 1:

                    if is_point_inside_rect(event.pos, pause_button_rect): # Check if the pause button is clicked
                        paused = not paused # toggle pause

                    elif is_point_inside_rect(event.pos, slider_handle_rect): # Check if slider is clicked
                        sliding = True
                        offset_x, offset_y = slider_handle_rect[0] - event.pos[0], slider_handle_rect[1] - event.pos[1]
                    else:
                        sliding = False

                elif event.button == 4:  # Scroll up
                    current_layer = (current_layer + 1) % len(toolpaths) # Next layer
                    index = len(scaled_toolpaths[current_layer]) - 1
                    paused = True # Pause on layer change
                    draw_toolpath(scaled_toolpaths[current_layer][:index + 1], index, colors, screen)
                elif event.button == 5:  # Scroll down
                    current_layer = (current_layer - 1) % len(scaled_toolpaths) # Prev layer
                    index = len(scaled_toolpaths[current_layer]) - 1
                    paused = True # Pause on layer change
                    draw_toolpath(scaled_toolpaths[current_layer][:index + 1], index, colors, screen)


            elif event.type == pygame.MOUSEMOTION and sliding:
                # Update the slider position when clicked
                mx, my = event.pos # Get mouse pos

                new_position = max(0, min(width - slider_handle_rect[2], mx + offset_x))
                percent = new_position / (width - slider_handle_rect[2])
                index = int(percent * (len(toolpaths[current_layer]) - 1))


            elif event.type == pygame.KEYDOWN: # Change layer down
                if event.key == pygame.K_DOWN:
                    current_layer = (current_layer - 1) % len(scaled_toolpaths)
                    index = len(scaled_toolpaths[current_layer]) - 1
                    paused = True
                    draw_toolpath(scaled_toolpaths[current_layer][:index + 1], index, colors, screen)

                elif event.key == pygame.K_UP: # Increase layer
                    current_layer = (current_layer + 1) % len(toolpaths)
                    index = len(scaled_toolpaths[current_layer]) - 1
                    paused = True
                    draw_toolpath(scaled_toolpaths[current_layer][:index + 1], index, colors, screen)

                elif event.key == pygame.K_SPACE:
                    paused = not paused

            elif event.type == pygame.MOUSEBUTTONUP:
                sliding = False


        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT]:
            index += 1  # Fast-forward by 1 point
        elif keys[pygame.K_LEFT]:
            index -= 1  # Skip back by 1 point

        # Guarantees that index is within bounds, and stops at the beginning/end of the animation
        index = max(0, min(len(toolpaths[current_layer]) - 1, index))

        screen.fill(white)

        draw_toolpath(scaled_toolpaths[current_layer][:index + 1], index, colors, screen)  # Draw up to the current point
        display_color_swatches(screen, font, dims, colors, color_names) # Show swatches in the top right

        # Draw the pause button
        pause_button_color = red if paused else green # Change background accordingly
        pygame.draw.rect(screen, pause_button_color, pause_button_rect)
        pygame.draw.rect(screen, (0, 0, 0), pause_button_rect, 2) # Black border
        pause_text = font.render("Pause", True, white) # Print white 'pause' text
        screen.blit(pause_text, (width // 2 - 20, height - 35))

        # Display current layer number
        display_current_layer(screen, font, current_layer, len(toolpaths), dims)

        # Update and draw the slider
        slider_rect = update_slider_position(index, len(toolpaths[current_layer]) - 1, slider_rect, dims)
        pygame.draw.rect(screen, (200, 200, 200), slider_rect)
        pygame.draw.rect(screen, (0, 0, 0), slider_rect, 2)

        slider_handle_rect = update_slider_position(index, len(toolpaths[current_layer]) - 1, slider_handle_rect, dims)
        pygame.draw.rect(screen, (0, 0, 255), slider_handle_rect)

        # Display current X, Y, A, E, SF values (UNSCALED)
        current_values = (f"X: {toolpaths[current_layer][index]['x']:.2f} "
                          f" Y: {toolpaths[current_layer][index]['y']:.2f} "
                          f" A: {toolpaths[current_layer][index]['extruder_angle']:.1f} "
                          f" E: {toolpaths[current_layer][index]['extrude']:.0f}"
                          f" SF: {toolpaths[current_layer][index]['surface_finish']:.0f}")

        text = font.render(current_values, True, (0, 0, 0))
        text_rect = text.get_rect(bottomright=(width - 10, height -20))
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(100 * speed)  # Adjust the frame rate based on speed

        if not paused:
            index += 1
            if index >= len(toolpaths[current_layer]):
                index = 0  # Restart the animation

    pygame.quit()
    sys.exit()
