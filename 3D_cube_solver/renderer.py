from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from cube_state import CubeState
import glfw

MOVE_ANIMATION_DURATION = 2.5
AUTO_PLAY_FRAME_INTERVAL = 150

class Renderer:
    def __init__(self):
        self.rotation_x = 25
        self.rotation_y = 30
        self.cube = CubeState()
        self.pick_mode = False
        self.selected_color = "W"
        self.palette_colors = ["W", "R", "G", "B", "O", "Y"]
        self.palette_positions = []
        self.solve_button = None
        self.connect_button = None
        self.reset_button = None
        self.home_button = None
        self.is_connected = False
        self.solution_moves = []
        self.scanned_faces = set()
        self.current_move_index = 0
        self.next_button = None
        self.auto_play_button = None
        self.animating = False
        self.current_move = None
        self.animation_angle = 0
        self.animation_speed = 1
        self.nxt_status_text = "Disconnected"
        self.playback_mode = False

        self.current_mode = "home"
        self.home_mode_buttons = []
        self.auto_play_mode = False
        self.auto_play_timer = 0
        self.auto_play_frame_interval = AUTO_PLAY_FRAME_INTERVAL

    def get_scale(self):
        width, height = glfw.get_framebuffer_size(glfw.get_current_context())
        return min(width / 800.0, height / 600.0)

    def get_ui_scale(self):
        window = glfw.get_current_context()
        width, height = glfw.get_window_size(window)
        base_scale = min(width / 1400.0, height / 900.0)
        try:
            scale_x, scale_y = glfw.get_window_content_scale(window)
            content_scale = max(scale_x, scale_y)
        except Exception:
            content_scale = 1.0
        return max(1.0, base_scale * content_scale)

    def get_layout(self):
        window = glfw.get_current_context()
        w, h = glfw.get_window_size(window)

        ui = min(w / 1400.0, h / 900.0)
        ui = max(0.9, min(ui, 1.15))

        content_w = min(w, int(1400 * ui))
        start_x = (w - content_w) // 2

        return {
            "w": w,
            "h": h,
            "ui": ui,
            "margin": int(24 * ui),
            "gap": int(250 * ui),
            "content_w": content_w,
            "start_x": start_x,
        }

    def clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def reset_state(self):
        self.cube = CubeState()
        self.scanned_faces.clear()
        self.solution_moves = []
        self.current_move_index = 0
        self.animating = False
        self.current_move = None
        self.pick_mode = False
        self.selected_color = "W"
        self.playback_mode = False
        self.rotation_x = 25
        self.rotation_y = 30
        self.auto_play_mode = False
        self.auto_play_timer = 0

    def draw(self):
        framebuffer_width, framebuffer_height = glfw.get_framebuffer_size(glfw.get_current_context())
        window_width, window_height = glfw.get_window_size(glfw.get_current_context())
        glViewport(0, 0, framebuffer_width, framebuffer_height)

        if self.current_mode == "home":
            self.draw_home_screen(window_width, window_height)
            return

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, framebuffer_width / framebuffer_height, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(0.0, 0.0, -10)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)

        if self.pick_mode:
            glDisable(GL_LIGHTING)
            glDisable(GL_COLOR_MATERIAL)
            self.draw_stickers()
            return

        if self.playback_mode and self.current_move:
            self.smooth_orient(self.current_move)

        if self.animating:
            self.animation_angle += self.animation_speed
            if self.animation_angle >= 90:
                self.cube.apply_move(self.current_move)
                self.current_move_index += 1
                self.animation_angle = 0
                self.animating = False
                self.current_move = None

        self.setup_lighting()
        self.draw_base_cube()
        glDisable(GL_LIGHTING)
        self.draw_stickers()
        self.draw_arrow()

        if self.current_mode == "manual":
            self.draw_manual_ui(window_width, window_height)
        elif self.current_mode == "robot":
            self.draw_robot_ui(window_width, window_height)

    def draw_stickers(self):
        size = 1.0
        gap = 0.01
        face_positions = {
            "F": (0, 0, 1), "B": (0, 0, -1),
            "U": (0, 1, 0), "D": (0, -1, 0),
            "R": (1, 0, 0), "L": (-1, 0, 0),
        }

        for face in self.cube.faces:
            for i in range(9):
                row = i // 3
                col = i % 3
                x = (col - 1) * (size + gap)
                y = (1 - row) * (size + gap)
                glPushMatrix()

                if self.animating and self.should_rotate_cube(face, row, col):
                    direction = -1 if "'" in self.current_move else 1
                    angle = self.animation_angle * direction
                    base = self.current_move.replace("'", "").replace("2", "")
                    if base == "U": glRotatef(-angle, 0, 1, 0)
                    elif base == "D": glRotatef(angle, 0, 1, 0)
                    elif base == "R": glRotatef(-angle, 1, 0, 0)
                    elif base == "L": glRotatef(angle, 1, 0, 0)
                    elif base == "F": glRotatef(-angle, 0, 0, 1)
                    elif base == "B": glRotatef(angle, 0, 0, 1)

                fx, fy, fz = face_positions[face]
                glTranslatef(fx*1.51, fy*1.51, fz*1.51)

                if face == "F": glTranslatef(x, y, 0)
                elif face == "B":
                    glRotatef(180, 0, 1, 0)
                    glTranslatef(x, y, 0)
                elif face == "U":
                    glRotatef(-90, 1, 0, 0)
                    glTranslatef(x, y, 0)
                elif face == "D":
                    glRotatef(90, 1, 0, 0)
                    glTranslatef(x, y, 0)
                elif face == "R":
                    glRotatef(90, 0, 1, 0)
                    glTranslatef(x, y, 0)
                elif face == "L":
                    glRotatef(-90, 0, 1, 0)
                    glTranslatef(x, y, 0)

                if self.pick_mode:
                    sticker_id = self.cube.sticker_ids[(face, i)]
                    r = (sticker_id & 0xFF) / 255.0
                    g = ((sticker_id >> 8) & 0xFF) / 255.0
                    b = ((sticker_id >> 16) & 0xFF) / 255.0
                    glColor3f(r, g, b)
                else:
                    glColor3f(*self.get_color(self.cube.faces[face][i]))

                glBegin(GL_QUADS)
                glVertex3f(-size/2, -size/2, 0)
                glVertex3f(size/2, -size/2, 0)
                glVertex3f(size/2, size/2, 0)
                glVertex3f(-size/2, size/2, 0)
                glEnd()

                glColor3f(0.05, 0.05, 0.05)
                glLineWidth(2)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-size/2, -size/2, 0.001)
                glVertex3f(size/2, -size/2, 0.001)
                glVertex3f(size/2, size/2, 0.001)
                glVertex3f(-size/2, size/2, 0.001)
                glEnd()
                glPopMatrix()

    def draw_arrow(self):
        if not self.animating or not self.current_move:
            return
        move = self.current_move
        face = move[0]
        is_prime = "'" in move
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 0.0, 0.7)
        dist = 2.0
        if face == "F": glTranslatef(0, 0, dist)
        elif face == "B":
            glRotatef(180, 0, 1, 0)
            glTranslatef(0, 0, dist)
        elif face == "U":
            glRotatef(-90, 1, 0, 0)
            glTranslatef(0, 0, dist)
        elif face == "D":
            glRotatef(90, 1, 0, 0)
            glTranslatef(0, 0, dist)
        elif face == "R":
            glRotatef(90, 0, 1, 0)
            glTranslatef(0, 0, dist)
        elif face == "L":
            glRotatef(-90, 0, 1, 0)
            glTranslatef(0, 0, dist)

        radius = 1.2
        width = 0.3
        num_segments = 20
        start_angle = np.radians(135)
        end_angle = np.radians(45)
        glBegin(GL_QUAD_STRIP)
        for i in range(num_segments + 1):
            t = i / num_segments
            theta = start_angle * (1 - t) + end_angle * t
            glVertex3f((radius - width/2) * np.cos(theta), (radius - width/2) * np.sin(theta), 0)
            glVertex3f((radius + width/2) * np.cos(theta), (radius + width/2) * np.sin(theta), 0)
        glEnd()
        glBegin(GL_TRIANGLES)
        head_width = width * 2.5
        if not is_prime:
            tip_theta = np.radians(20)
            base_theta = np.radians(45)
        else:
            tip_theta = np.radians(160)
            base_theta = np.radians(135)
        tip_x = radius * np.cos(tip_theta)
        tip_y = radius * np.sin(tip_theta)
        b1_x = (radius - head_width/2) * np.cos(base_theta)
        b1_y = (radius - head_width/2) * np.sin(base_theta)
        b2_x = (radius + head_width/2) * np.cos(base_theta)
        b2_y = (radius + head_width/2) * np.sin(base_theta)
        if not is_prime:
            glVertex3f(tip_x, tip_y, 0)
            glVertex3f(b1_x, b1_y, 0)
            glVertex3f(b2_x, b2_y, 0)
        else:
            glVertex3f(tip_x, tip_y, 0)
            glVertex3f(b2_x, b2_y, 0)
            glVertex3f(b1_x, b1_y, 0)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def get_color(self, c):
        return {
            "W": (1,1,1), "R": (1,0,0), "G": (0,1,0),
            "B": (0,0,1), "O": (1,0.5,0), "Y": (1,1,0),
            "X": (0.3, 0.3, 0.3),
            "U": (1,1,1), "D": (1,1,0), "F": (0,1,0),
            "B": (0,0,1), "R": (1,0,0), "L": (1,0.5,0),
        }.get(c, (1,1,1))

    def setup_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT, GL_SPECULAR, (0.3,0.3,0.3,1))
        glMateriali(GL_FRONT, GL_SHININESS, 50)
        glEnable(GL_DEPTH_TEST)

    def should_rotate_cube(self, face_name, row, col):
        if not self.current_move:
            return False
        base = self.current_move.replace("'", "").replace("2", "")
        if base == "U": return face_name == "U" or row == 0
        if base == "D": return face_name == "D" or row == 2
        if base == "R": return face_name == "R" or col == 2
        if base == "L": return face_name == "L" or col == 0
        if base == "F":
            return (face_name == "F" or (face_name == "U" and row == 2) or
                    (face_name == "D" and row == 0) or
                    (face_name == "L" and col == 2) or (face_name == "R" and col == 0))
        if base == "B":
            return (face_name == "B" or (face_name == "U" and row == 0) or
                    (face_name == "D" and row == 2) or
                    (face_name == "L" and col == 0) or (face_name == "R" and col == 2))
        return False

    def smooth_orient(self, move):
        base = move.replace("'", "")
        targets = {"U": (45, 30), "D": (-45, 30), "F": (25, 30),
                  "B": (25, 210), "R": (25, -60), "L": (25, 120)}
        target_x, target_y = targets.get(base, (25, 30))
        self.rotation_x += (target_x - self.rotation_x) * 0.1
        self.rotation_y += (target_y - self.rotation_y) * 0.1

    def draw_base_cube(self):
        glColor3f(0.15, 0.15, 0.2)
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-1.5, -1.5, 1.5); glVertex3f(1.5, -1.5, 1.5)
        glVertex3f(1.5, 1.5, 1.5); glVertex3f(-1.5, 1.5, 1.5)
        # Back
        glVertex3f(-1.5, -1.5, -1.5); glVertex3f(-1.5, 1.5, -1.5)
        glVertex3f(1.5, 1.5, -1.5); glVertex3f(1.5, -1.5, -1.5)
        # Top
        glVertex3f(-1.5, 1.5, -1.5); glVertex3f(-1.5, 1.5, 1.5)
        glVertex3f(1.5, 1.5, 1.5); glVertex3f(1.5, 1.5, -1.5)
        # Bottom
        glVertex3f(-1.5, -1.5, -1.5); glVertex3f(1.5, -1.5, -1.5)
        glVertex3f(1.5, -1.5, 1.5); glVertex3f(-1.5, -1.5, 1.5)
        # Right
        glVertex3f(1.5, -1.5, -1.5); glVertex3f(1.5, 1.5, -1.5)
        glVertex3f(1.5, 1.5, 1.5); glVertex3f(1.5, -1.5, 1.5)
        # Left
        glVertex3f(-1.5, -1.5, -1.5); glVertex3f(-1.5, -1.5, 1.5)
        glVertex3f(-1.5, 1.5, 1.5); glVertex3f(-1.5, 1.5, -1.5)
        glEnd()

    def begin_2d(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

    def end_2d(self):
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    def draw_rect(self, x, y, w, h, color):
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def draw_rect_outline(self, x, y, w, h, color, line_width=2):
        glColor3f(*color)
        glLineWidth(line_width)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def draw_panel(self, x, y, w, h, fill, border, line_width=2):
        self.draw_rect(x, y, w, h, fill)
        self.draw_rect_outline(x, y, w, h, border, line_width)

    def draw_text_pixel(self, x, y, text, color=(1, 1, 1), size=18, align="left", valign="baseline"):
        from OpenGL.GLUT import glutStrokeCharacter, glutStrokeWidth, GLUT_STROKE_ROMAN
        if not text:
            return
        glDisable(GL_LIGHTING)
        glColor3f(*color)
        scale = size / 120.0
        tracking = 3.5
        space_width = 30.0
        total = 0
        for ch in text:
            if ch == ' ':
                total += space_width + tracking
            else:
                total += glutStrokeWidth(GLUT_STROKE_ROMAN, ord(ch)) + tracking
        text_width = total * scale
        text_height = size

        if align == "center":
            x -= text_width / 2
        elif align == "right":
            x -= text_width

        if valign == "center":
            y -= text_height / 2
        elif valign == "top":
            y -= text_height

        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(scale, scale, 1.0)
        glLineWidth(max(1.0, size / 24.0))
        for ch in text:
            if ch == ' ':
                glTranslatef(space_width, 0, 0)
            else:
                glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
                glTranslatef(tracking, 0, 0)
        glPopMatrix()

    def draw_text_block(self, x, y, lines, color=(1, 1, 1), size=18, line_gap=1.35, align="left"):
        line_height = size * line_gap
        for i, line in enumerate(lines):
            self.draw_text_pixel(x, y - i * line_height, line, color=color, size=size, align=align)

    def draw_manual_icon(self, cx, cy, scale):
        handle_w = 10 * scale
        handle_h = 36 * scale
        tip_h = 18 * scale
        glColor3f(0.93, 0.95, 0.99)
        glBegin(GL_QUADS)
        glVertex2f(cx - handle_w, cy - handle_h)
        glVertex2f(cx + handle_w, cy - handle_h)
        glVertex2f(cx + handle_w, cy + handle_h * 0.2)
        glVertex2f(cx - handle_w, cy + handle_h * 0.2)
        glEnd()
        glBegin(GL_TRIANGLES)
        glVertex2f(cx - handle_w * 1.3, cy + handle_h * 0.2)
        glVertex2f(cx + handle_w * 1.3, cy + handle_h * 0.2)
        glVertex2f(cx, cy + handle_h * 0.2 + tip_h)
        glEnd()
        glColor3f(0.2, 0.35, 0.65)
        glBegin(GL_QUADS)
        glVertex2f(cx - handle_w * 1.2, cy - handle_h * 0.05)
        glVertex2f(cx + handle_w * 1.2, cy - handle_h * 0.05)
        glVertex2f(cx + handle_w * 1.2, cy + handle_h * 0.2)
        glVertex2f(cx - handle_w * 1.2, cy + handle_h * 0.2)
        glEnd()

    def draw_robot_icon(self, cx, cy, scale):
        head_w = 34 * scale
        head_h = 26 * scale
        body_w = 48 * scale
        body_h = 30 * scale
        glColor3f(0.93, 0.95, 0.99)
        glBegin(GL_QUADS)
        glVertex2f(cx - head_w, cy + 6 * scale)
        glVertex2f(cx + head_w, cy + 6 * scale)
        glVertex2f(cx + head_w, cy + head_h)
        glVertex2f(cx - head_w, cy + head_h)
        glEnd()
        glBegin(GL_QUADS)
        glVertex2f(cx - body_w, cy - body_h)
        glVertex2f(cx + body_w, cy - body_h)
        glVertex2f(cx + body_w, cy + 2 * scale)
        glVertex2f(cx - body_w, cy + 2 * scale)
        glEnd()
        glColor3f(0.12, 0.13, 0.15)
        eye_offset = 15 * scale
        eye_r = 4 * scale
        for eye_x in (cx - eye_offset, cx + eye_offset):
            glBegin(GL_QUADS)
            glVertex2f(eye_x - eye_r, cy + 16 * scale - eye_r)
            glVertex2f(eye_x + eye_r, cy + 16 * scale - eye_r)
            glVertex2f(eye_x + eye_r, cy + 16 * scale + eye_r)
            glVertex2f(eye_x - eye_r, cy + 16 * scale + eye_r)
            glEnd()
        glColor3f(0.93, 0.95, 0.99)
        glBegin(GL_LINES)
        glVertex2f(cx, cy + head_h)
        glVertex2f(cx, cy + head_h + 14 * scale)
        glVertex2f(cx - body_w * 0.7, cy - body_h)
        glVertex2f(cx - body_w, cy - body_h - 18 * scale)
        glVertex2f(cx + body_w * 0.7, cy - body_h)
        glVertex2f(cx + body_w, cy - body_h - 18 * scale)
        glVertex2f(cx - body_w, cy - 6 * scale)
        glVertex2f(cx - body_w - 18 * scale, cy + 8 * scale)
        glVertex2f(cx + body_w, cy - 6 * scale)
        glVertex2f(cx + body_w + 18 * scale, cy + 8 * scale)
        glEnd()

    def draw_home_card(self, x, y, w, h, accent, border, title, description, mode, icon_name):
        self.draw_panel(x, y, w, h, (0.14, 0.16, 0.2), border, 3)
        self.draw_rect(x, y + h - 8, w, 8, accent)
        icon_center_x = x + w / 2
        icon_center_y = y + h - 62

        if icon_name == "manual":
            self.draw_manual_icon(icon_center_x, icon_center_y, max(0.85, min(1.35, w / 250.0)))
        else:
            self.draw_robot_icon(icon_center_x, icon_center_y - 8, max(0.85, min(1.35, w / 250.0)))

        title_size = 20 if w < 420 else 24
        body_size = 12
        title_y = y + h - 138
        body_y = title_y - 44

        self.draw_text_pixel(x + w / 2, title_y, title, (0.95, 0.97, 1.0), size=title_size, align="center")
        self.draw_text_block(
            x + w / 2,
            body_y,
            description,
            color=(0.68, 0.72, 0.8),
            size=body_size,
            line_gap=1.45,
            align="center",
        )
        self.draw_text_pixel(x + w / 2, y + 24, f"Click to open {mode}", accent, size=12, align="center")

    def draw_home_screen(self, width, height):
        L = self.get_layout()
        self.begin_2d(width, height)
        glClearColor(0.12, 0.13, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.home_mode_buttons.clear()

        self.draw_text_pixel(
            width // 2,
            height - 250 * L["ui"],
            "Rubik's Cube Solver",
            size=118,
            align="center"
        )

        self.draw_text_pixel(
            width // 2,
            height - 500 * L["ui"],
            "Choose your mode",
            (0.7, 0.75, 0.85),
            size=50,
            align="center"
        )

        card_w = L["content_w"] - L["gap"]
        card_h = int(700 * L["ui"])

        y = height // 2 - card_h // 2 

        total_w = card_w * 2 + L["gap"]
        group_start = width // 2 - total_w // 2
        manual_x = group_start
        robot_x = group_start + card_w + L["gap"]

        self.draw_panel(manual_x, y, card_w, card_h, (0.14, 0.16, 0.2), (0.3, 0.5, 0.8))
        self.draw_text_pixel(manual_x + card_w / 2, y + card_h - 350, "Manual", align="center", size=70)
        self.draw_text_pixel(manual_x + card_w / 2, y + card_h - 500, "Paint cube and solve", align="center", size=45)

        self.draw_panel(robot_x, y, card_w, card_h, (0.14, 0.16, 0.2), (0.8, 0.5, 0.2))
        self.draw_text_pixel(robot_x + card_w / 2, y + card_h - 350, "Robot", align="center", size=70)
        self.draw_text_pixel(robot_x + card_w / 2, y + card_h - 500, "Scan with NXT", align="center", size=45)

        self.home_mode_buttons.append(("manual", manual_x, y, card_w, card_h))
        self.home_mode_buttons.append(("robot", robot_x, y, card_w, card_h))

        self.end_2d()

    def draw_button_2d(self, x, y, w, h, text, color, text_color=(1,1,1), scale=1.0, font_size=None):
        self.draw_rect(x, y, w, h, color)
        darker = (color[0]*0.8, color[1]*0.8, color[2]*0.8)
        self.draw_rect_outline(x, y, w, h, darker, 2)
        resolved_size = font_size if font_size is not None else self.clamp(h * 0.38, 12, 20)
        self.draw_text_pixel(x + w / 2, y + h / 2 - resolved_size * 0.22, text, text_color, size=resolved_size, align="center")

    def draw_top_bar(self, width, height, title, accent):
        ui = self.get_ui_scale()
        margin = 18 * ui
        bar_h = 84 * ui
        self.draw_panel(margin, height - bar_h - margin, width - margin * 2, bar_h, (0.1, 0.11, 0.14), (0.2, 0.22, 0.28), 2)
        self.draw_rect(margin, height - margin - 6 * ui, width - margin * 2, 6 * ui, accent)
        self.draw_text_pixel(margin + 20 * ui, height - margin - 36 * ui, title, (0.95, 0.97, 1.0), size=24, valign="center")
        return bar_h

    def draw_status_chip(self, x, y, w, h, text, fill, text_color=(1, 1, 1)):
        self.draw_panel(x, y, w, h, fill, fill, 1)
        self.draw_text_pixel(x + w / 2, y + h / 2 - 5, text, text_color, size=13, align="center")

    def draw_cube_stage_guidance(self, width, height, title, subtitle):
        ui = self.get_ui_scale()
        left = 26
        box_w = min(520 * ui, width - 52)
        box_h = 82 * ui
        y = height - 192 * ui
        self.draw_panel(left, y, box_w, box_h, (0.11, 0.12, 0.16), (0.19, 0.21, 0.27), 1)
        self.draw_text_pixel(left + 18 * ui, y + 50 * ui, title, (0.95, 0.97, 1.0), size=12)
        self.draw_text_pixel(left + 18 * ui, y + 24 * ui, subtitle, (0.62, 0.67, 0.76), size=12)

    def draw_bottom_panel(self, width, height, panel_h):
        ui = self.get_ui_scale()
        x = 18
        y = 18
        w = width - 36
        self.draw_panel(x, y, w, panel_h, (0.1, 0.11, 0.14), (0.2, 0.22, 0.28), 2)
        return x, y, w, panel_h

    def draw_control_buttons_row(self, width, top_y):
        ui = self.get_ui_scale()
        btn_w = 120 * ui
        btn_h = 40 * ui
        x1 = 34 * ui
        y = top_y + 18 * ui
        gap = 16 * ui
        self.draw_button_2d(x1, y, btn_w, btn_h, "HOME", (0.24, 0.26, 0.32))
        self.home_button = (x1, y, btn_w, btn_h)
        x2 = x1 + btn_w + gap
        self.draw_button_2d(x2, y, btn_w, btn_h, "RESET", (0.72, 0.26, 0.26))
        self.reset_button = (x2, y, btn_w, btn_h)

    def draw_solution_summary(self, x, y, w):
        if not self.solution_moves:
            self.draw_text_pixel(x + w / 2, y + 14, "Complete the cube to generate a solution.", (0.62, 0.67, 0.76), size=12, align="center")
            return
        current = min(self.current_move_index + 1, len(self.solution_moves))
        self.draw_text_pixel(x, y + 28, f"Solution ready: {len(self.solution_moves)} moves", (0.95, 0.97, 1.0), size=12)
        self.draw_text_pixel(x, y + 10, f"Current step: {current}", (0.62, 0.67, 0.76), size=10)

    def draw_manual_ui(self, width, height):
        L = self.get_layout()
        self.solve_button = None
        self.reset_button = None
        self.next_button = None
        self.auto_play_button = None
        self.begin_2d(width, height)

        bar_h = int(90 * L["ui"])
        x = L["start_x"]
        y = height - bar_h - L["margin"]

        self.draw_panel(x, y, L["content_w"], bar_h, (0.1, 0.11, 0.14), (0.2, 0.2, 0.25))
        self.draw_text_pixel(x + 20, y + bar_h / 2, "Manual Solver", size=32, valign="center")

        btn_w = int(140 * L["ui"])
        btn_h = int(50 * L["ui"])

        self.draw_button_2d(x + 20, y - btn_h - 40, btn_w, btn_h, "HOME", (0.3, 0.3, 0.35))
        self.home_button = (x + 20, y - btn_h - 40, btn_w, btn_h)

        self.draw_button_2d(x + 270, y - btn_h - 40, btn_w, btn_h, "RESET", (0.7, 0.3, 0.3))
        self.reset_button = (x + 270, y - btn_h - 40, btn_w, btn_h)

        panel_h = int(145 * L["ui"])
        py = L["margin"]

        self.draw_panel(x, py, L["content_w"], panel_h, (0.1, 0.11, 0.14), (0.2, 0.2, 0.25))
        self.draw_palette(x + 70, py + 30)

        solve_w = int(150 * L["ui"])
        solve_h = int(75 * L["ui"])

        solve_x = x + L["content_w"] - solve_w - 90
        solve_y = py + 35
        self.draw_button_2d(solve_x, solve_y, solve_w, solve_h, "SOLVE", (0.12, 0.62, 0.42))
        self.solve_button = (solve_x, solve_y, solve_w, solve_h)

        if self.solution_moves:
            self.draw_next_button(solve_x, solve_y + solve_h + 12, solve_w)
            solution_w = min(int(760 * L["ui"]), L["content_w"] - 160)
            solution_x = x + (L["content_w"] - solution_w) // 2
            solution_y = y - btn_h - 140
            self.draw_solution_text(solution_x, solution_y, solution_w)

        self.end_2d()

    def draw_robot_ui(self, width, height):
        L = self.get_layout()
        self.connect_button = None
        self.next_button = None
        self.auto_play_button = None
        self.reset_button = None
        self.begin_2d(width, height)

        self.draw_text_pixel(width // 2, height - 170, "Robot Solver", align="center", size=68)

        self.draw_button_2d(1300, height - 400, 200, 65, "HOME", (0.3, 0.3, 0.35))
        self.home_button = (1300, height - 400, 200, 65)

        if not self.is_connected:
            box_w = int(440 * L["ui"])
            box_h = int(260 * L["ui"])

            x = width // 2 - box_w // 2
            y = height // 2 - box_h // 2

            self.draw_panel(x, y, box_w, box_h, (0.1, 0.11, 0.14), (0.2, 0.2, 0.25))
            self.draw_text_pixel(width // 2, y + box_h - 95, "Connect NXT", align="center", size=35)

            btn_w = int(250 * L["ui"])
            btn_h = int(70 * L["ui"])

            bx = width // 2 - btn_w // 2
            by = y + 40

            self.draw_button_2d(bx, by, btn_w, btn_h, "CONNECT", (0.3, 0.4, 0.6))
            self.connect_button = (bx, by, btn_w, btn_h)
        else:
            self.draw_text_pixel(width // 2, height // 2, "Connected", align="center", size=20)

            if self.solution_moves:
                self.draw_next_button(width // 2 - 75, 100, 150)
                self.draw_auto_play_button(width // 2 - 75, 160, 150)

        self.end_2d()

    def draw_next_button(self, x, y, button_w=150):
        button_h = 46
        self.next_button = (x, y+100, button_w, button_h)
        self.draw_button_2d(x, y+100, button_w, button_h, "NEXT MOVE", (0.2, 0.7, 0.3))

    def draw_auto_play_button(self, x, y, button_w=150):
        button_h = 46
        self.auto_play_button = (x, y, button_w, button_h)
        if self.auto_play_mode:
            self.draw_button_2d(x, y, button_w, button_h, "PAUSE", (0.7, 0.2, 0.7))
        else:
            self.draw_button_2d(x, y, button_w, button_h, "AUTO PLAY", (0.25, 0.44, 0.82))

    def draw_solution_text(self, x, y, max_width):
        L = self.get_layout()
        if not self.solution_moves:
            return
        max_line_width = max(max_width, 120)
        line_y = y
        line_height = 24 * L["ui"]
        current_x = 0
        for i, move in enumerate(self.solution_moves):
            from OpenGL.GLUT import glutStrokeWidth, GLUT_STROKE_ROMAN
            tracking = 3.5
            move_width = (sum(glutStrokeWidth(GLUT_STROKE_ROMAN, ord(ch)) for ch in move) + len(move) * tracking) * 16 / 120.0 + 18 * L["ui"]
            if current_x + move_width > max_line_width:
                current_x = 0
                line_y -= line_height
            if i == self.current_move_index:
                color = (1.0, 0.36, 0.36)
            else:
                color = (0.93, 0.95, 1.0)
            self.draw_text_pixel(x + current_x, line_y, move, color=color, size=16)
            current_x += move_width

    def draw_palette(self, start_x, start_y):
        L = self.get_layout()
        size = 78 * L["ui"]
        spacing = 42 * L["ui"]
        self.palette_positions.clear()
        for i, color in enumerate(self.palette_colors):
            x = start_x + i * (size + spacing)
            y = start_y
            rgb = self.get_color(color)
            if color == self.selected_color:
                glColor3f(1, 1, 1)
                glBegin(GL_QUADS)
                glVertex2f(x - 4 * L["ui"], y - 4 * L["ui"])
                glVertex2f(x + size + 4 * L["ui"], y - 4 * L["ui"])
                glVertex2f(x + size + 4 * L["ui"], y + size + 4 * L["ui"])
                glVertex2f(x - 4 * L["ui"], y + size + 4 * L["ui"])
                glEnd()
            glColor3f(*rgb)
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + size, y)
            glVertex2f(x + size, y + size)
            glVertex2f(x, y + size)
            glEnd()
            glColor3f(0.05, 0.05, 0.05)
            glLineWidth(2)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x, y)
            glVertex2f(x + size, y)
            glVertex2f(x + size, y + size)
            glVertex2f(x, y + size)
            glEnd()
            self.draw_text_pixel(x + size / 2, y - 16, color, (0.86, 0.9, 0.98), size=14, align="center")
            self.palette_positions.append((x, y, size, size, color))

    def draw_scan_status(self, start_x, start_y):
        face_order = ["B", "L", "F", "D", "R", "U"]
        self.draw_text_pixel(start_x, start_y + 34, "Scan Progress", (0.95, 0.97, 1.0), size=12)
        for i, face in enumerate(face_order):
            x = start_x + i * 44
            if face in self.scanned_faces:
                self.draw_status_chip(x, start_y, 30, 28, face, (0.18, 0.6, 0.28))
            else:
                self.draw_status_chip(x, start_y, 30, 28, face, (0.25, 0.27, 0.31), (0.72, 0.75, 0.82))
