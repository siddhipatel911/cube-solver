class CubeState:
    def __init__(self):
        self.faces = {
            "U": ["X"]*9,
            "R": ["X"]*9,
            "F": ["X"]*9,
            "D": ["X"]*9,
            "L": ["X"]*9,
            "B": ["X"]*9,
        }

        # Create sticker ID mapping
        self.sticker_ids = {}
        self.id_to_sticker = {}

        current_id = 1
        for face in self.faces:
            for i in range(9):
                self.sticker_ids[(face, i)] = current_id
                self.id_to_sticker[current_id] = (face, i)
                current_id += 1

    def is_fully_colored(self):
        for face in self.faces:
            for sticker in self.faces[face]:
                if sticker == "X":
                    return False
        return True


    def has_valid_color_count(self):
        counts = {"W":0, "R":0, "G":0, "B":0, "O":0, "Y":0}

        for face in self.faces:
            for sticker in self.faces[face]:
                if sticker not in counts:
                    return False
                counts[sticker] += 1

        for color in counts:
            if counts[color] != 9:
                return False

        return True
    
    def to_kociemba_string(self):
        center_map = {
            self.faces["U"][4]: "U",
            self.faces["R"][4]: "R",
            self.faces["F"][4]: "F",
            self.faces["D"][4]: "D",
            self.faces["L"][4]: "L",
            self.faces["B"][4]: "B",
        }
        
        order = ["U", "R", "F", "D", "L", "B"]
        result = ""

        for face in order:
            for sticker in self.faces[face]:
                result += center_map[sticker]

        return result
    
    def set_state_from_nxt_string(self, s):
        # NXC code sends faces in order: L, F, R, B, U, D
        # Each face has 9 characters.
        if len(s) < 54:
            print("Error: NXT string too short")
            return

        self.faces["L"] = list(s[0:9])
        self.faces["F"] = list(s[9:18])
        self.faces["R"] = list(s[18:27])
        self.faces["B"] = list(s[27:36])
        self.faces["U"] = list(s[36:45])
        self.faces["D"] = list(s[45:54])

    def set_face(self, face, stickers):
        """
        Updates a single face with a string of 9 characters.
        """
        if face in self.faces and len(stickers) == 9:
            self.faces[face] = list(stickers)

    def rotate_face_clockwise(self, face):
        f = self.faces[face]
        self.faces[face] = [
            f[6], f[3], f[0],
            f[7], f[4], f[1],
            f[8], f[5], f[2],
        ]

    """def rotate_face_ccw(self, face):
        self.rotate_face_clockwise(face)
        self.rotate_face_clockwise(face)
        self.rotate_face_clockwise(face)"""

    def move_U(self):
        self.rotate_face_clockwise("U")

        F = self.faces["F"]
        R = self.faces["R"]
        B = self.faces["B"]
        L = self.faces["L"]

        temp = F[0:3]

        F[0:3] = R[0:3]
        R[0:3] = B[0:3]
        B[0:3] = L[0:3]
        L[0:3] = temp

    def move_R(self):
        self.rotate_face_clockwise("R")

        U = self.faces["U"]
        F = self.faces["F"]
        D = self.faces["D"]
        B = self.faces["B"]

        temp = [U[2], U[5], U[8]]

        U[2], U[5], U[8] = F[2], F[5], F[8]
        F[2], F[5], F[8] = D[2], D[5], D[8]
        D[2], D[5], D[8] = B[6], B[3], B[0]
        B[6], B[3], B[0] = temp

    def move_L(self):
        self.rotate_face_clockwise("L")

        U = self.faces["U"]
        F = self.faces["F"]
        D = self.faces["D"]
        B = self.faces["B"]

        temp = [U[0], U[3], U[6]]

        U[0], U[3], U[6] = B[8], B[5], B[2]
        B[8], B[5], B[2] = D[0], D[3], D[6]
        D[0], D[3], D[6] = F[0], F[3], F[6]
        F[0], F[3], F[6] = temp

    def move_D(self):
        self.rotate_face_clockwise("D")

        F = self.faces["F"]
        R = self.faces["R"]
        B = self.faces["B"]
        L = self.faces["L"]

        temp = F[6:9]

        F[6:9] = L[6:9]
        L[6:9] = B[6:9]
        B[6:9] = R[6:9]
        R[6:9] = temp

    def move_F(self):
        self.rotate_face_clockwise("F")

        U = self.faces["U"]
        R = self.faces["R"]
        D = self.faces["D"]
        L = self.faces["L"]

        temp = [U[6], U[7], U[8]]

        U[6], U[7], U[8] = L[8], L[5], L[2]
        L[8], L[5], L[2] = D[2], D[1], D[0]
        D[2], D[1], D[0] = R[0], R[3], R[6]
        R[0], R[3], R[6] = temp

    def move_B(self):
        self.rotate_face_clockwise("B")

        U = self.faces["U"]
        R = self.faces["R"]
        D = self.faces["D"]
        L = self.faces["L"]

        temp = [U[0], U[1], U[2]]

        U[0], U[1], U[2] = R[2], R[5], R[8]
        R[2], R[5], R[8] = D[8], D[7], D[6]
        D[8], D[7], D[6] = L[6], L[3], L[0]
        L[6], L[3], L[0] = temp
    
    def apply_move(self, move):
        times = 1
        if move.endswith("2"):
            times = 2
            move = move[0]
        elif move.endswith("'"):
            times = 3
            move = move[0]

        for _ in range(times):
            if move == "U":
                self.move_U()
            elif move == "R":
                self.move_R()
            elif move == "F":
                self.move_F()
            elif move == "D":
                self.move_D()
            elif move == "L":
                self.move_L()
            elif move == "B":
                self.move_B()
            else:
                print(f"Unknown move: {move}")