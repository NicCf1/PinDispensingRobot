# Code was written by Nicolas Ian Krause and polished ChatGPT do not redistribute without credit
#Cy was here too gng 
import serial
import time
import subprocess
import os
from datetime import datetime
import serial.tools.list_ports
#import trojan.exe.virus

# ----------------------------
# FILES
# ----------------------------
SCREENSAVER_FILE = "screensaver.txt"
COORDS_FILE = "coords.txt"
SAVE_FOLDER = "captures"
SAVER_FILE = "saver.txt"

# ----------------------------
# SETTINGS
# ----------------------------
AUTO_BUTTON = False # simulates a button every (x) interval
BUTTON_INTERVAL = 35
INACTIVITY_TIMEOUT = 15
CAMERA_MODE = "B"   # A = photo, B = video, C = disabled

last_activity = time.time()

# ----------------------------
# SERIAL DETECTION
# ----------------------------
def find_port(name_hint):

    ports = list(serial.tools.list_ports.comports())

    print("\n[DEBUG] Ports detected:")
    for p in ports:
        print(f" - {p.device} : {p.description}")

    for p in ports:
        if name_hint.lower() in p.description.lower() or name_hint.lower() in p.device.lower():
            print(f"[DEBUG] Matched '{name_hint}' -> {p.device}")
            return p.device

    raise RuntimeError(f"[ERROR] Could not find device matching '{name_hint}'")

arduino_port = find_port("CH340")
robot_port = find_port("mega")

arduino = serial.Serial(arduino_port, 9600, timeout=1)
time.sleep(2)

robot = serial.Serial(robot_port, 115200, timeout=1)
time.sleep(2)

print("[DEBUG] Serial connected")

# ----------------------------
# UTILITIES
# ----------------------------
def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def increment_counter():

    try:
        with open(SAVER_FILE, "r") as f:
            count = int(f.read().strip())
    except:
        count = 0

    count += 1

    with open(SAVER_FILE, "w") as f:
        f.write(str(count))

# ----------------------------
# CAMERA
# ----------------------------
def record_photo():

    ensure_folder_exists(SAVE_FOLDER)

    filename = os.path.join(
        SAVE_FOLDER,
        f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    )

    print("[CAMERA] Capturing photo")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "dshow",
        "-video_size", "1280x720",
        "-framerate", "30",
        "-i", "video=HD Pro Webcam C920",
        "-vframes", "1",
        filename
    ])

def start_video_recording():

    ensure_folder_exists(SAVE_FOLDER)

    filename = os.path.join(
        SAVE_FOLDER,
        f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )

    process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-rtbufsize", "100M",
            "-f", "dshow",
            "-video_size", "800x600",
            "-framerate", "30",
            "-i", "video=HD Pro Webcam C920:audio=Microphone (HD Pro Webcam C920)",
            "-vcodec", "h264_qsv",
            "-preset", "veryfast",
            "-acodec", "aac",
            "-pix_fmt", "yuv420p",
            filename
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return process

# ----------------------------
# ROBOT
# ----------------------------
def send_robot_line(cmd):

    print(f"[SEND] {cmd}")

    robot.write((cmd + "\r").encode())

    while True:

        if robot.in_waiting:

            line = robot.readline().decode().strip()

            if line:
                print("[ROBOT]", line)

            if line.lower() == "ok":
                break

def run_coords_sequence():

    print("[ROBOT] Running coords.txt")

    with open(COORDS_FILE) as f:

        for line in f:

            cmd = line.strip()

            if cmd:
                send_robot_line(cmd)

    arduino.write(b"SEQUENCE_COMPLETE\n")

# ----------------------------
# BUTTON
# ----------------------------
def button_pressed():

    if arduino.in_waiting:

        msg = arduino.readline().decode().strip()

        print("[ARDUINO]", msg)

        if "BUTTON_PRESSED" in msg:
            return True

    return False

# ----------------------------
# SCREENSAVER
# ----------------------------
def run_screensaver():

    global last_activity

    print("[SCREENSAVER] Started")

    while True:

        with open(SCREENSAVER_FILE) as f:

            for line in f:

                cmd = line.strip()

                if not cmd:
                    continue

                if button_pressed():
                    print("[SCREENSAVER] Exit by button")
                    last_activity = time.time()
                    return True

                if cmd.lower().startswith("sleep("):

                    seconds = float(cmd.split("(")[1].split(")")[0])

                    print(f"[SCREENSAVER] Sleep {seconds}")

                    start = time.time()

                    while time.time() - start < seconds:

                        if button_pressed():
                            print("[SCREENSAVER] Exit during sleep")
                            last_activity = time.time()
                            return True

                        time.sleep(0.05)

                else:

                    print("[SCREENSAVER]", cmd)
                    send_robot_line(cmd)


# ----------------------------
# WAIT SYSTEM
# ----------------------------
def wait_for_button():

    global last_activity

    print("[DEBUG] Waiting for button")

    last_print = -1

    while True:

        if button_pressed():
            print("[DEBUG] Button accepted")
            last_activity = time.time()
            return

        elapsed = time.time() - last_activity
        remaining = int(INACTIVITY_TIMEOUT - elapsed)

        # only print once per second
        if remaining != last_print and remaining >= 0:
            print(f"[SCREENSAVER IN] {remaining} seconds")
            last_print = remaining

        if elapsed > INACTIVITY_TIMEOUT:

            print("[DEBUG] Starting screensaver")

            pressed = run_screensaver()

            if pressed:
                print("[DEBUG] Button came from screensaver")
                last_activity = time.time()
                return

        time.sleep(0.05)
# ----------------------------
# STARTUP
# ----------------------------
print("[DEBUG] Running startup")

send_robot_line("G28")
send_robot_line("G0 E90 F40")

print("[DEBUG] Startup complete")

# ----------------------------
# MAIN LOOP
# ----------------------------
while True:

    increment_counter()

    wait_for_button()

    if CAMERA_MODE == "A":

        record_photo()
        run_coords_sequence()

    elif CAMERA_MODE == "B":

        ffmpeg_process = start_video_recording()

        run_coords_sequence()

        print("[CAMERA] stopping")

        ffmpeg_process.communicate(input=b"q")

    else:

        run_coords_sequence()

    last_activity = time.time()

    print("Ready for next button")
