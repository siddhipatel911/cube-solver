import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from renderer import Renderer
import kociemba

WIDTH = 800
HEIGHT = 600

def main():
    if not glfw.init():
        raise Exception("GLFW cannot be initialized!")

    window = glfw.create_window(WIDTH, HEIGHT, "3D Cube Solver", None, None)

    if not window:
        glfw.terminate()
        raise Exception("GLFW window cannot be created!")

    glfw.make_context_current(window)

    from OpenGL.GLUT import glutInit
    glutInit()

    renderer = Renderer()

    last_x = 0
    last_y = 0
    dragging = False
    drag_threshold = 3  # pixels
    mouse_moved = False

    def handle_picking(window):
        x, y = glfw.get_cursor_pos(window)
        width, height = glfw.get_framebuffer_size(window)
        y = height - y

        # Check palette first
        for px, py, w, h, color in renderer.palette_positions:
            if px <= x <= px+w and py <= y <= py+h:
                renderer.selected_color = color
                print("Selected color:", color)
                return
            
        # Check Solve button
        if renderer.solve_button:
            bx, by, bw, bh = renderer.solve_button
            if bx <= x <= bx+bw and by <= y <= by+bh:
                cube = renderer.cube

                if not cube.is_fully_colored():
                    print("Cube not fully colored!")
                    return
                
                if not cube.has_valid_color_count():
                    print("Invalid colour counts!")
                    return
                try:
                    cube_string = cube.to_kociemba_string()
                    solution = kociemba.solve(cube_string)
                    print("Solution:", solution)

                    renderer.solution_moves = solution.split()
                    renderer.current_move_index = 0
                    renderer.playback_mode = True
                    renderer.rotation_x = 25
                    renderer.rotation_y = 30

                    renderer.animating = False
                    renderer.current_move = None
                    renderer.animation_angle = 0
                except Exception as e:
                    print("Invalid cube state:", e)

                return
            
        # Check Next button
        if renderer.next_button:
            bx, by, bw, bh = renderer.next_button
            if bx <= x <= bx+bw and by <= y <= by+bh:
                if not renderer.animating and renderer.current_move_index < len(renderer.solution_moves):
                    renderer.current_move = renderer.solution_moves[renderer.current_move_index]
                    renderer.animating = True
                    renderer.animation_angle = 0
                
                return

        # Otherwise do 3D picking
        renderer.pick_mode = True
        renderer.playback_mode = False
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        renderer.draw()
        glFlush()

        pixel = glReadPixels(
            int(x),
            int(y),
            1,
            1,
            GL_RGB,
            GL_UNSIGNED_BYTE
        )

        renderer.pick_mode = False

        if pixel:
            r = pixel[0]
            g = pixel[1]
            b = pixel[2]

            sticker_id = r + (g << 8) + (b << 16)

            if sticker_id in renderer.cube.id_to_sticker:
                face, index = renderer.cube.id_to_sticker[sticker_id]
                renderer.cube.faces[face][index] = renderer.selected_color
                print("Painted:", face, index)

    def mouse_button_callback(window, button, action, mods):
        nonlocal dragging, mouse_moved, last_x, last_y

        if button == glfw.MOUSE_BUTTON_LEFT:

            if action == glfw.PRESS:
                dragging = True
                mouse_moved = False
                last_x, last_y = glfw.get_cursor_pos(window)

            elif action == glfw.RELEASE:
                dragging = False

                # If mouse barely moved → treat as click
                if not mouse_moved:
                    handle_picking(window)


    def cursor_position_callback(window, xpos, ypos):
        nonlocal last_x, last_y, dragging, mouse_moved

        if dragging:
            dx = xpos - last_x
            dy = ypos - last_y

            if abs(dx) > drag_threshold or abs(dy) > drag_threshold:
                mouse_moved = True

            renderer.rotation_y += dx * 0.5
            renderer.rotation_x += dy * 0.5

            last_x = xpos
            last_y = ypos


    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_position_callback)

    while not glfw.window_should_close(window):
        glClearColor(0.85, 0.9, 0.95, 1.0)  # light background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        renderer.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()