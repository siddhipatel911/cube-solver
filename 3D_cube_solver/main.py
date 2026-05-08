import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from renderer import Renderer
import kociemba
from nxt_controller import NXTController

WIDTH = 800
HEIGHT = 600

def main():
    if not glfw.init():
        raise Exception("GLFW cannot be initialized!")

    glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
    glfw.window_hint(glfw.MAXIMIZED, glfw.TRUE)
    window = glfw.create_window(WIDTH, HEIGHT, "3D Cube Solver", None, None)

    if not window:
        glfw.terminate()
        raise Exception("GLFW window cannot be created!")

    glfw.make_context_current(window)
    glfw.maximize_window(window)

    from OpenGL.GLUT import glutInit
    glutInit()

    renderer = Renderer()
    nxt_robot = NXTController()

    last_x = 0
    last_y = 0
    dragging = False
    drag_threshold = 3
    mouse_moved = False

    def get_scaled_x(x):
        width, _ = glfw.get_framebuffer_size(window)
        return x * (width / 800.0)

    def get_scaled_y(y):
        _, height = glfw.get_framebuffer_size(window)
        return y * (height / 600.0)

    def perform_solve():
        cube = renderer.cube
        try:
            cube_string = cube.to_kociemba_string()
            solution = kociemba.solve(cube_string)
            print("Solution found:", solution)

            renderer.solution_moves = solution.split()
            renderer.current_move_index = 0
            renderer.playback_mode = True
            renderer.rotation_x = 25
            renderer.rotation_y = 30
            renderer.animating = False
            renderer.current_move = None
            renderer.animation_angle = 0

            if nxt_robot.is_connected():
                nxt_robot.send_solution(renderer.solution_moves)
        except Exception as e:
            print("Solver Error:", e)

    def go_home():
        renderer.current_mode = "home"
        renderer.reset_state()
        nxt_robot.disconnect()
        renderer.is_connected = False

    def handle_home_screen(window):
        x, y = glfw.get_cursor_pos(window)
        width, height = glfw.get_window_size(window)
        y = height - y

        for mode, bx, by, bw, bh in renderer.home_mode_buttons:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                renderer.current_mode = mode
                renderer.reset_state()
                if mode == "robot":
                    renderer.is_connected = nxt_robot.is_connected()
                return

    def handle_manual_mode(window):
        x, y = glfw.get_cursor_pos(window)
        width, height = glfw.get_window_size(window)
        y = height - y

        for px, py, w, h, color in renderer.palette_positions:
            if px <= x <= px + w and py <= y <= py + h:
                renderer.selected_color = color
                print("Selected color:", color)
                return

        if renderer.solve_button:
            bx, by, bw, bh = renderer.solve_button
            if bx <= x <= bx + bw and by <= y <= by + bh:
                cube = renderer.cube
                if not cube.is_fully_colored():
                    print("Cube not fully colored!")
                    return
                if not cube.has_valid_color_count():
                    print("Invalid colour counts!")
                    return
                perform_solve()
                return

        if renderer.home_button:
            hx, hy, hw, hh = renderer.home_button
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                go_home()
                return

        if renderer.reset_button:
            rx, ry, rw, rh = renderer.reset_button
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                renderer.reset_state()
                return

        if renderer.next_button:
            bx, by, bw, bh = renderer.next_button
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if not renderer.animating and renderer.current_move_index < len(renderer.solution_moves):
                    renderer.current_move = renderer.solution_moves[renderer.current_move_index]
                    renderer.animating = True
                    renderer.animation_angle = 0
                return

        renderer.pick_mode = True
        renderer.playback_mode = False
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        renderer.draw()
        glFlush()

        fb_w, fb_h = glfw.get_framebuffer_size(window)
        win_w, win_h = glfw.get_window_size(window)

        pick_x = int(x * fb_w / win_w)
        pick_y = int(y * fb_h / win_h)
        pixel = glReadPixels(pick_x, pick_y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
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

    def handle_robot_mode(window):
        x, y = glfw.get_cursor_pos(window)
        width, height = glfw.get_window_size(window)
        y = height - y

        if renderer.home_button:
            hx, hy, hw, hh = renderer.home_button
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                go_home()
                return

        if renderer.connect_button:
            cx, cy, cw, ch = renderer.connect_button
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                if not nxt_robot.is_connected():
                    renderer.is_connected = nxt_robot.connect()
                    if renderer.is_connected:
                        renderer.scanned_faces.clear()
                return

        if renderer.auto_play_button:
            ax, ay, aw, ah = renderer.auto_play_button
            if ax <= x <= ax + aw and ay <= y <= ay + ah:
                renderer.auto_play_mode = not renderer.auto_play_mode
                return

        if renderer.next_button:
            bx, by, bw, bh = renderer.next_button
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if not renderer.animating and renderer.current_move_index < len(renderer.solution_moves):
                    renderer.current_move = renderer.solution_moves[renderer.current_move_index]
                    renderer.animating = True
                    renderer.animation_angle = 0
                return

    def handle_picking(window):
        if renderer.current_mode == "home":
            handle_home_screen(window)
        elif renderer.current_mode == "manual":
            handle_manual_mode(window)
        elif renderer.current_mode == "robot":
            handle_robot_mode(window)

    def mouse_button_callback(window, button, action, mods):
        nonlocal dragging, mouse_moved, last_x, last_y

        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                dragging = True
                mouse_moved = False
                last_x, last_y = glfw.get_cursor_pos(window)
            elif action == glfw.RELEASE:
                dragging = False
                if not mouse_moved:
                    handle_picking(window)

    def cursor_position_callback(window, xpos, ypos):
        nonlocal last_x, last_y, dragging, mouse_moved

        if dragging:
            dx = xpos - last_x
            dy = ypos - last_y

            if abs(dx) > drag_threshold or abs(dy) > drag_threshold:
                mouse_moved = True

            if renderer.current_mode != "home":
                renderer.rotation_y += dx * 0.5
                renderer.rotation_x += dy * 0.5

            last_x = xpos
            last_y = ypos

    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_position_callback)

    frame_count = 0

    while not glfw.window_should_close(window):
        glClearColor(0.12, 0.13, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        frame_count += 1

        if renderer.current_mode == "robot" and nxt_robot.is_connected():
            if frame_count % 10 == 0:
                msg = nxt_robot.check_mailbox()
                if msg:
                    try:
                        msg_str = msg.decode('ascii').replace('\x00', '')
                        print("NXT Message:", msg_str)

                        if msg_str.startswith("SCANNED"):
                            parts = msg_str.split()
                            if len(parts) >= 2:
                                renderer.scanned_faces.add(parts[1])
                                nxt_robot.current_status = f"Scanned Face {parts[1]}"
                        elif len(msg_str) >= 54:
                            renderer.cube.set_state_from_nxt_string(msg_str)
                            nxt_robot.current_status = "Solving..."
                            perform_solve()
                    except Exception as e:
                        print("Error parsing NXT message:", e)

        if renderer.current_mode == "robot" and renderer.auto_play_mode and renderer.solution_moves:
            if not renderer.animating and renderer.current_move_index < len(renderer.solution_moves):
                renderer.auto_play_timer += 1
                if renderer.auto_play_timer >= renderer.auto_play_frame_interval:
                    renderer.auto_play_timer = 0
                    renderer.current_move = renderer.solution_moves[renderer.current_move_index]
                    renderer.animating = True
                    renderer.animation_angle = 0
            elif not renderer.animating and renderer.current_move_index >= len(renderer.solution_moves):
                renderer.auto_play_mode = False
                renderer.auto_play_timer = 0

        renderer.nxt_status_text = nxt_robot.current_status
        renderer.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
