import sys
import os

# Fix for ModuleNotFoundError when packages are installed in user-specific directory.
# This must be at the top of this file, before other imports are attempted.
if sys.platform == 'win32':
    user_site_packages = os.path.join(os.getenv('APPDATA'), 'Python', f'Python{sys.version_info.major}{sys.version_info.minor}', 'site-packages')
    if os.path.isdir(user_site_packages) and user_site_packages not in sys.path:
        sys.path.append(user_site_packages)

import nxt.locator
import nxt.error
import nxt.brick
from nxt.motor import *
import time

class NXTController:
    def __init__(self):
        self.brick = None
        self.current_status = "Disconnected"

    def connect(self):
        """
        Attempts to find and connect to the NXT brick via Serial Port (COM).
        This bypasses PyBluez by using the virtual COM port created by Windows pairing.
        """
        print("Searching for NXT brick (Serial/COM)...")
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            print("Module 'pyserial' not found. Please run: pip install pyserial")
            self.current_status = "Missing Library"
            return False

        # Get a list of all COM ports
        ports = list(serial.tools.list_ports.comports())
        
        for p in ports:
            print(f"Checking {p.device} - {p.description}")
            # Try to connect to this port
            try:
                sock = SerialSock(p.device)
                # Create a brick object manually
                brick = nxt.brick.Brick(sock)
                
                # Try to send a keep-alive or get battery to verify it's an NXT
                # This will throw an error if it's not an NXT or connection fails
                brick.get_battery_level()
                
                print(f"Success! Connected to NXT on {p.device}")
                self.brick = brick
                self.current_status = f"Connected ({p.device})"
                return True
            except (serial.SerialException, nxt.error.ProtocolError, OSError):
                continue

        print("No NXT found on any COM port. Ensure it is paired in Windows Settings.")
        self.brick = None
        self.current_status = "Connection Failed"
        return False

    def is_connected(self):
        return self.brick is not None

    def send_solution(self, solution_moves):
        """
        Sends the solution moves to the NXT brick.
        Protocol based on Tilted Twister Java code:
        - Mailbox: 5
        - Format: String of moves where:
            - 'U' -> "U"
            - 'U2' -> "UU"
            - "U'" -> "UUU"
        - Terminated with null byte.
        """
        if not self.is_connected():
            print("Cannot send solution: NXT is not connected.")
            return

        print(f"Sending solution to NXT: {solution_moves}")
        
        nxt_message = ""
        for move in solution_moves:
            face = move[0]
            if "2" in move:
                nxt_message += face * 2
            elif "'" in move:
                nxt_message += face * 3
            else:
                nxt_message += face
        
        # The Java code adds a null terminator
        nxt_message += '\x00'
        
        try:
            # Mailbox 5 corresponds to OUTBOX in the Java code
            self.brick.message_write(5, nxt_message.encode('ascii'))
            print(f"Sent message to Mailbox 5: {nxt_message[:-1]}")
            self.current_status = "Executing Moves..."
        except Exception as e:
            print(f"Failed to send message to NXT: {e}")
            self.disconnect()

    def check_mailbox(self):
        """Checks if the NXT has sent a 'Ready' (scan data) message."""
        if not self.is_connected():
            return None
        
        try:
            # Robot sends scan data to Mailbox 1 (OUTBOX=1 in NXC code)
            # The signature is message_read(remote_inbox, local_inbox, remove)
            box, msg = self.brick.message_read(1, 0, True)
            self.current_status = "Ready / Scanned"
            return msg
        except nxt.error.ProtocolError:
            # This is the correct exception for an empty mailbox
            pass
        except Exception:
            pass
        return None

    def disconnect(self):
        if self.is_connected():
            print("Disconnecting from NXT.")
            self.brick = None
            self.current_status = "Disconnected"

class SerialSock:
    """
    A wrapper around pyserial to make it look like an NXT socket.
    Handles the 2-byte length header required for Bluetooth/RFCOMM communication.
    """
    def __init__(self, port):
        import serial
        # Timeout is important so we don't hang forever checking wrong ports
        self.ser = serial.Serial(port, baudrate=9600, timeout=2)

    def send(self, data):
        # NXT Bluetooth protocol requires a 2-byte length header (Little Endian)
        length = len(data)
        header = bytes([length & 0xFF, (length >> 8) & 0xFF])
        self.ser.write(header + data)

    def recv(self):
        # Read the 2-byte length header
        header = self.ser.read(2)
        if len(header) < 2:
            raise nxt.error.ProtocolError("Socket closed or timeout reading header")
        
        length = header[0] + (header[1] << 8)
        data = self.ser.read(length)
        if len(data) < length:
             raise nxt.error.ProtocolError("Incomplete read of packet body")
        return data
    
    def close(self):
        self.ser.close()