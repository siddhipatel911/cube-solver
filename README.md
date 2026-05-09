# 🧊 Rubik's Cube Solver

A high-performance Rubik's Cube solver featuring a 3D interactive interface and integration with LEGO Mindstorms NXT robots. This project allows users to input cube states manually via a 3D UI or scan them using a physical robot, solve them using the Kociemba algorithm, and visualize the solution with animated move-by-move playback.

## ✨ Features

*   **🖥️ 3D Visualization:** A fully interactive 3D cube rendered using OpenGL, supporting rotation and manual sticker "painting."
*   **🤖 Robotic Integration:** Seamless connection to LEGO Mindstorms NXT via Serial/Bluetooth, supporting the "Tilted Twister" protocol.
*   **🧠 Optimal Solving:** Utilizes the Kociemba two-phase algorithm for near-optimal solution lengths.
*   **🎞️ Animated Playback:** Watch moves being performed in real-time with smooth animations and camera auto-orientation.
*   **⌨️ Hybrid Input:** Supports manual color entry via 2D GUI (`cube_gui.py`) or 3D picking (`main.py`).

## 📂 Project Structure

*   `main.py`: The entry point for the 3D application. Handles the main loop and input events.
*   `renderer.py`: Core OpenGL rendering logic, including 3D geometry, UI overlays, and animations.
*   `nxt_controller.py`: Manages communication with the NXT brick, handling the Bluetooth serial protocol and mailbox messaging.
*   `cube_gui.py`: A lightweight Tkinter-based fallback GUI for manual color configuration.

## 🛠️ Prerequisites

### 🔌 Hardware
*   LEGO Mindstorms NXT Brick (optional, for robotic solving).
*   A PC with Bluetooth support (for NXT connection).

### 💻 Software Dependencies
Ensure you have Python 3.x installed along with the following libraries:

```bash
pip install PyOpenGL PyOpenGL_accelerate glfw pyserial nxt-python kociemba numpy
```

*Note: On Windows, `freeglut.dll` may be required for GLUT text rendering.*

## Usage

1.  **Launch the 3D Solver:**
    ```bash
    python "3D_cube_solver/main.py"
    ```
2.  **Input the Cube State:**
    *   Use the mouse to rotate the cube.
    *   Select a color from the bottom palette and click on cube stickers to paint them.
    *   Alternatively, connect an NXT robot to scan the cube automatically.
3.  **Solve:**
    *   Click the **SOLVE** button.
    *   If connected to an NXT, the moves will be sent to the robot.
    *   Use the **NEXT MOVE** button to step through the solution animation on screen.

## NXT Connection Details

The project uses a virtual COM port created by Windows Bluetooth pairing to bypass legacy driver issues. 
*   The robot listens on **Mailbox 5** for move sequences.
*   The robot sends scan data/status to **Mailbox 1**.
*   Move format: `U`, `UU` (U2), or `UUU` (U') terminated by a null byte.

## Demo Video

### Manual Solver Demo
[Watch the manual solver demo](https://drive.google.com/file/d/1nxkUumcUpE2jXsIE8EYrzjFKdxBS1YqX/view?usp=drive_link)

### Robot Solver Demo
[Watch the robot solver demo](https://drive.google.com/file/d/1D8yiZerIOPliAmflefi2sBBzLnEeLCHs/view?usp=sharing)

## Acknowledgments

*   **Herbert Kociemba:** For the Two-Phase-Algorithm.
*   **Hans Andersson:** For the original Tilted Twister robot design and protocol logic.
*   **nxt-python contributors:** For the LEGO NXT interface library.
