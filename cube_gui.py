import tkinter as tk #GUI library
from colour_map import COLOR_PALETTE, FACE_ORDER
import kociemba, tkinter.messagebox #solving algorithm, to show popups

class CubeSolverGUI:
    def __init__(self): #initializes the gui, runs when you create gui = CubeSolverGUI()
        self.root = tk.Tk() #creates the main application window
        self.root.title("Cube Solver Input") #sets the top bar text

        self.current_face = tk.StringVar(value=FACE_ORDER[0]) #sets default face to "U" when GUI starts
        self.face_frames = {} #creates a dictionary that will store a 3x3 grid frame for each face
        self.faces = {face: [""] * 9 for face in FACE_ORDER} #internal cube model, each face with 9 stickers
        self.create_face_selector()
        self.create_face_grid()
        self.create_solve_button()
    
    def create_face_selector(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        for face in FACE_ORDER:
            button = tk.Radiobutton(
                frame, text=face,
                variable=self.current_face,
                value=face,
                indicatoron=False,
                width=4
            )
            button.pack(side=tk.LEFT, padx=2)

    def create_face_grid(self):
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack()

        for face in FACE_ORDER:
            f = tk.Frame(self.grid_frame)
            self.face_frames[face] = f

            for i in range(9):
                btn = tk.Button(
                    f,
                    text="",
                    bg="grey",
                    width=4,
                    height=2,
                    command=lambda f=face, i=i: self.on_square_click(f, i)
                )
                btn.grid(row=i//3, column=i%3, padx=1, pady=1)

    def show_current_face(self):
        for face, frame in self.face_frames.items():
            frame.pack_forget()

        self.face_frames[self.current_face.get()].pack()

    def on_square_click(self, face, index):
        # cycle through colors
        colors = list(COLOR_PALETTE.keys())
        current = self.faces[face][index]
        nxt = colors[(colors.index(current) + 1) % len(colors)] if current in colors else colors[0]

        self.faces[face][index] = nxt

        btn = self.face_frames[face].grid_slaves(row=index//3, column=index%3)[0]
        btn.config(bg=COLOR_PALETTE[nxt], text=nxt)

    def get_cube_string(self):
        order = ["U","R","F","D","L","B"]
        cube_str = ""
        for face in order:
            for color in self.faces[face]:
                if color == "":
                    raise ValueError("Not all squares are filled!")
                cube_str += color
        return cube_str

    def create_solve_button(self):
        btn = tk.Button(self.root, text="Solve", command=self.on_solve)
        btn.pack(pady=10)
    
    def on_solve(self):
        try:
            cube = self.get_cube_string()
            solution = kociemba.solve(cube)
            tkinter.messagebox.showinfo("Solution", solution)
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def run(self):
        self.show_current_face()
        self.root.mainloop()

if __name__ == "__main__":
    gui = CubeSolverGUI()
    gui.run()