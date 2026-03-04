from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from cube_state import CubeState
import glfw

class Renderer:
    def __init__(self):
        self.rotation_x = 25
        self.rotation_y = 30
        self.cube = CubeState()
        self.pick_mode = False
        self.selected_color = "W"
        self.palette_colors = ["W", "R", "G", "B", "O", "Y"]
        self.palette_positions = []  # will store clickable areas
        self.solve_button = None
        self.connect_button = None
        self.is_connected = False
        self.solution_moves = []
        self.scanned_faces = set()
        self.current_move_index = 0
        self.next_button = None
        self.animating = False
        self.current_move = None
        self.animation_angle = 0
        self.animation_speed = 1
        self.nxt_status_text = "Disconnected"
        self.playback_mode = False

    def draw(self):
        width, height = glfw.get_framebuffer_size(glfw.get_current_context())
        glViewport(0, 0, width, height)

        # ----- 3D PROJECTION -----
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width/height, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Move cube to center
        glTranslatef(0.0, 0.0, -10)

        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)

        if self.pick_mode:
            # ----- PICKING MODE -----
            glDisable(GL_LIGHTING)
            glDisable(GL_COLOR_MATERIAL)
            self.draw_stickers()
            return
        
         # ---- Smooth Camera Auto Orientation ----
        if self.playback_mode and self.current_move:
            self.smooth_orient(self.current_move)

        # ---- Animate Layer ----
        if self.animating:
            self.animation_angle += self.animation_speed

            if self.animation_angle >= 90:
                self.cube.apply_move(self.current_move)
                self.current_move_index += 1
                self.animation_angle = 0
                self.animating = False
                self.current_move = None

         # ----- NORMAL RENDERING -----
        self.setup_lighting()
        self.draw_base_cube()
        glDisable(GL_LIGHTING)
        self.draw_stickers()
        self.draw_arrow()

        self.draw_ui(width, height)

    def draw_stickers(self):
        size = 1.0
        gap = 0.01

        face_positions = {
            "F": (0, 0, 1),
            "B": (0, 0, -1),
            "U": (0, 1, 0),
            "D": (0, -1, 0),
            "R": (1, 0, 0),
            "L": (-1, 0, 0),
        }

        for face in self.cube.faces:
            for i in range(9):
                row = i // 3
                col = i % 3

                x = (col - 1) * (size + gap)
                y = (1 - row) * (size + gap)

                glPushMatrix()

                # --- Animate rotating layer ---
                if self.animating and self.should_rotate_cube(face, row, col):

                    direction = -1 if "'" in self.current_move else 1
                    angle = self.animation_angle * direction
                    base = self.current_move.replace("'", "").replace("2", "")

                    # Standard cube rotations (clockwise from face)
                    if base == "U":
                        glRotatef(-angle, 0, 1, 0)
                    elif base == "D":
                        glRotatef(angle, 0, 1, 0)
                    elif base == "R":
                        glRotatef(-angle, 1, 0, 0)
                    elif base == "L":
                        glRotatef(angle, 1, 0, 0)
                    elif base == "F":
                        glRotatef(-angle, 0, 0, 1)
                    elif base == "B":
                        glRotatef(angle, 0, 0, 1)


                # --- Position face ---
                fx, fy, fz = face_positions[face]
                glTranslatef(fx*1.51, fy*1.51, fz*1.51) 

                if face == "F":
                    glTranslatef(x, y, 0)
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

                # Draw black border
                glColor3f(0, 0, 0)
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
        glColor4f(1.0, 1.0, 0.0, 0.7)  # Yellow, semi-transparent

        # Orient to the face
        dist = 2.0 

        if face == "F":
            glTranslatef(0, 0, dist)
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

        # Draw the curved arrow
        radius = 1.2
        width = 0.3
        
        # Arc from 135 to 45 degrees
        num_segments = 20
        start_angle = np.radians(135)
        end_angle = np.radians(45)
        
        glBegin(GL_QUAD_STRIP)
        for i in range(num_segments + 1):
            t = i / num_segments
            theta = start_angle * (1 - t) + end_angle * t
            
            x_inner = (radius - width/2) * np.cos(theta)
            y_inner = (radius - width/2) * np.sin(theta)
            x_outer = (radius + width/2) * np.cos(theta)
            y_outer = (radius + width/2) * np.sin(theta)
            
            glVertex3f(x_inner, y_inner, 0)
            glVertex3f(x_outer, y_outer, 0)
        glEnd()
        
        # Draw Arrow Head
        glBegin(GL_TRIANGLES)
        head_width = width * 2.5
        
        if not is_prime: # CW -> Head at 45 deg
            tip_theta = np.radians(20)
            base_theta = np.radians(45)
        else: # CCW -> Head at 135 deg
            tip_theta = np.radians(160)
            base_theta = np.radians(135)

        # Calculate head vertices
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
        colors = {
            "W": (1,1,1),
            "R": (1,0,0),
            "G": (0,1,0),
            "B": (0,0,1),
            "O": (1,0.5,0),
            "Y": (1,1,0),
            "X": (0.3, 0.3, 0.3),  # gray
            # Map standard face letters to colors for visualization
            "U": (1,1,1),   # Up -> White
            "D": (1,1,0),   # Down -> Yellow
            "F": (0,1,0),   # Front -> Green
            "B": (0,0,1),   # Back -> Blue
            "R": (1,0,0),   # Right -> Red
            "L": (1,0.5,0), # Left -> Orange
        }
        return colors[c]

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
        move = self.current_move
        if not move:
            return False

        base = move.replace("'", "").replace("2", "")

        if base == "U":
            return face_name == "U" or row == 0
        if base == "D":
            return face_name == "D" or row == 2
        if base == "R":
            return face_name == "R" or col == 2
        if base == "L":
            return face_name == "L" or col == 0
        if base == "F":
            return face_name == "F"
        if base == "B":
            return face_name == "B"

        return False
    
    def orient_for_move(self, move):
        if not self.playback_mode:
            return
        
        base = move.replace("'", "")

        if base in ["U", "D"]:
            self.rotation_x = 45
            self.rotation_y = 30

        elif base in ["F"]:
            self.rotation_x = 25
            self.rotation_y = 30

        elif base in ["B"]:
            self.rotation_x = 25
            self.rotation_y = 210

        elif base in ["R"]:
            self.rotation_x = 25
            self.rotation_y = -60

        elif base in ["L"]:
            self.rotation_x = 25
            self.rotation_y = 120

    def smooth_orient(self, move):

        base = move.replace("'", "")

        targets = {
            "U": (45, 30),
            "D": (-45, 30),
            "F": (25, 30),
            "B": (25, 210),
            "R": (25, -60),
            "L": (25, 120),
        }

        target_x, target_y = targets.get(base, (25, 30))

        speed = 3

        self.rotation_x += (target_x - self.rotation_x) * 0.1
        self.rotation_y += (target_y - self.rotation_y) * 0.1
    
    def draw_base_cube(self):
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_QUADS)

        # Front
        glVertex3f(-1.5, -1.5, 1.5)
        glVertex3f(1.5, -1.5, 1.5)
        glVertex3f(1.5, 1.5, 1.5)
        glVertex3f(-1.5, 1.5, 1.5)

        # Back
        glVertex3f(-1.5, -1.5, -1.5)
        glVertex3f(-1.5, 1.5, -1.5)
        glVertex3f(1.5, 1.5, -1.5)
        glVertex3f(1.5, -1.5, -1.5)

        # Top
        glVertex3f(-1.5, 1.5, -1.5)
        glVertex3f(-1.5, 1.5, 1.5)
        glVertex3f(1.5, 1.5, 1.5)
        glVertex3f(1.5, 1.5, -1.5)

        # Bottom
        glVertex3f(-1.5, -1.5, -1.5)
        glVertex3f(1.5, -1.5, -1.5)
        glVertex3f(1.5, -1.5, 1.5)
        glVertex3f(-1.5, -1.5, 1.5)

        # Right
        glVertex3f(1.5, -1.5, -1.5)
        glVertex3f(1.5, 1.5, -1.5)
        glVertex3f(1.5, 1.5, 1.5)
        glVertex3f(1.5, -1.5, 1.5)

        # Left
        glVertex3f(-1.5, -1.5, -1.5)
        glVertex3f(-1.5, -1.5, 1.5)
        glVertex3f(-1.5, 1.5, 1.5)
        glVertex3f(-1.5, 1.5, -1.5)

        glEnd()
    
    def draw_next_button(self, width, height):

        button_width = 160
        button_height = 45

        x = width // 2 - button_width // 2
        y = 100

        self.next_button = (x, y, button_width, button_height)

        glColor3f(0.2, 0.6, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + button_width, y)
        glVertex2f(x + button_width, y + button_height)
        glVertex2f(x, y + button_height)
        glEnd()

        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + button_width, y)
        glVertex2f(x + button_width, y + button_height)
        glVertex2f(x, y + button_height)
        glEnd()

        self.draw_text(x + 40, y + 15, "NEXT MOVE")


    def draw_solution_text(self, width, height):

        if not self.solution_moves:
            return

        start_x = width // 2 - 250
        y = height - 80

        x_offset = 0

        for i, move in enumerate(self.solution_moves):

            if i == self.current_move_index:
                glColor3f(1.0, 0.2, 0.2)
            else:
                glColor3f(1.0, 1.0, 1.0)

            self.draw_text(start_x + x_offset, y, move)
            x_offset += 35
    
    def draw_ui(self, width, height):

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)

        # -------- TITLE --------
        self.draw_text(width//2 - 120, height - 40, "3D RUBIK'S CUBE SOLVER")

        # -------- SOLVE BUTTON --------
        button_w = 140
        button_h = 45
        bx = width - button_w - 30
        by = 30

        self.solve_button = (bx, by, button_w, button_h)

        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(bx, by)
        glVertex2f(bx+button_w, by)
        glVertex2f(bx+button_w, by+button_h)
        glVertex2f(bx, by+button_h)
        glEnd()

        self.draw_text(bx+40, by+15, "SOLVE")

        # -------- CONNECT BUTTON --------
        self.draw_connect_button(width, height)

        # -------- SCAN STATUS --------
        if self.is_connected:
            self.draw_scan_status(width, height)

        # -------- PALETTE --------
        self.draw_palette(width, height)

        # -------- SOLUTION UI --------
        if self.solution_moves:
            self.draw_next_button(width, height)
            self.draw_solution_text(width, height)

        glEnable(GL_DEPTH_TEST)

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    def draw_connect_button(self, width, height):
        button_w = 180
        button_h = 45
        # Position to the left of the Solve button
        # Solve button is at roughly width - 170
        x = width - 170 - button_w - 20
        y = 30

        self.connect_button = (x, y, button_w, button_h)

        if self.is_connected:
            glColor3f(0.2, 0.8, 0.2)  # Green
            text = "NXT CONNECTED"
        else:
            glColor3f(0.4, 0.4, 0.4)  # Grey
            text = "CONNECT NXT"

        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + button_w, y)
        glVertex2f(x + button_w, y + button_h)
        glVertex2f(x, y + button_h)
        glEnd()

        glColor3f(1, 1, 1)
        self.draw_text(x + 20, y + 15, text)
        
        # Draw Status Text below button
        glColor3f(0.7, 0.7, 0.7)
        self.draw_text(x, y - 20, f"Status: {self.nxt_status_text}")

    def draw_scan_status(self, width, height):
        y = height - 120
        start_x = width // 2 - 100
        # This order matches the ScanCube() function in the NXC code
        face_order = ["B", "L", "F", "D", "R", "U"]
        
        glColor3f(1, 1, 1)
        self.draw_text(start_x - 130, y, "Scan Progress:")

        for i, face in enumerate(face_order):
            x = start_x + i * 35
            color = (0.2, 1.0, 0.2) if face in self.scanned_faces else (0.7, 0.7, 0.7)
            glColor3f(*color)
            self.draw_text(x, y, face)

    def draw_text(self, x, y, text):
        from OpenGL.GLUT import glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18
        glDisable(GL_LIGHTING)
        glRasterPos2f(x, y)
        for ch in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    def draw_palette(self, width, height):
        # Save current matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)

        size = 50
        spacing = 20
        start_x = 20
        y = 20

        self.palette_positions.clear()

        for i, color in enumerate(self.palette_colors):
            x = start_x + i * (size + spacing)

            rgb = self.get_color(color)

            # Highlight selected
            if color == self.selected_color:
                glColor3f(1, 1, 1)
                glBegin(GL_QUADS)
                glVertex2f(x-5, y-5)
                glVertex2f(x+size+5, y-5)
                glVertex2f(x+size+5, y+size+5)
                glVertex2f(x-5, y+size+5)
                glEnd()

            glColor3f(*rgb)
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x+size, y)
            glVertex2f(x+size, y+size)
            glVertex2f(x, y+size)
            glEnd()

            self.palette_positions.append((x, y, size, size, color))

        glEnable(GL_DEPTH_TEST)

        # Restore matrices
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()