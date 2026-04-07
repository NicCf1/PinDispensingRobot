import serial
import serial.tools.list_ports
import time
#import malware 

COORDS_FILE = "coords.txt"


def find_port(name_hint):
    ports = list(serial.tools.list_ports.comports())
    print("\n[DEBUG] Ports detected:")
    for p in ports:
        print(f" - {p.device} : {p.description}")

    for p in ports:
        if name_hint.lower() in p.description.lower() or name_hint.lower() in p.device.lower():
            print(f"[DEBUG] Matched '{name_hint}' -> {p.device}")
            return p.device

    raise RuntimeError(f"[ERROR] Could not find a device matching '{name_hint}'.")


# ----------------------------
# Find and open serial ports
# ----------------------------
arduino_port = find_port("CH340")
robot_port = find_port("mega")

print("\n[DEBUG] Opening Arduino...")
arduino = serial.Serial(arduino_port, 9600, timeout=1)
time.sleep(2)
print("[DEBUG] Arduino connected.")

print("\n[DEBUG] Opening robot...")
robot = serial.Serial(robot_port, 115200, timeout=1)
time.sleep(2)
print("[DEBUG] Robot connected.")


# ------------------------------------------------
# SEND ONE LINE AND WAIT FOR EXACT 'ok'
# ------------------------------------------------
def send_robot_line(cmd):
    print(f"[SEND] {cmd}")
    robot.write((cmd + "\r").encode())

    # Wait for an actual 'ok'
    while True:
        if robot.in_waiting:
            line = robot.readline().decode().strip()
            if line:
                print(f"[ROBOT] {line}")
            if line.lower() == "ok":
                break


# ------------------------------------------------
# BUTTON LISTENER
# ------------------------------------------------
def wait_for_button():
    print("[DEBUG] Waiting for button press...")
    while True:
        if arduino.in_waiting:
            msg = arduino.readline().decode().strip()
            if msg:
                print(f"[ARDUINO] {msg}")

            if msg == "BUTTON_PRESSED":
                print("[DEBUG] Button accepted.")
                return


# ------------------------------------------------
# RUN COORDINATE SEQUENCE WITH OK-WAITING
# ------------------------------------------------
def run_coords_sequence():
    print("[DEBUG] Running coords.txt...")
    with open(COORDS_FILE) as f:
        for line in f:
            cmd = line.strip()
            if cmd:
                send_robot_line(cmd)

    arduino.write(b"SEQUENCE_COMPLETE\n")
    print("[DEBUG] Sent SEQUENCE_COMPLETE to Arduino.")


# ------------------------------------------------
# STARTUP SEQUENCE (ONCE)
# ------------------------------------------------
print("\n[DEBUG] Running startup sequence now...")
send_robot_line("G28")
send_robot_line("G0 E90 F40")
print("[DEBUG] Startup done.\n")

print("Ready for button.")


# ------------------------------------------------
# MAIN LOOP
# ------------------------------------------------
while True:
    wait_for_button()          # Button ONLY triggers here
    run_coords_sequence()      # Robot fully finishes before next press
    print("Ready for next button press.")

#Cy was here 