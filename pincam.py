# Code written and adapted with a joint effort of Nicolas Ian Krause and ChatGPT
#Do not distrbute without credit
# import hacks.torgin.horgse, max.damg = true   computer = destroyed , Cy totaly didnt write ts gng 

import serial
import serial.tools.list_ports
import time
import subprocess
import os
from datetime import datetime
# import hacks.torgin.horgse, max.damg = true   computer = destroyed
COORDS_FILE = "coords.txt"
SAVE_FOLDER = "captures"
SAVER_FILE = "saver.txt"
AUTO_BUTTON = False
BUTTON_INTERVAL = 35 #in seconds


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
# CONFIGURATION
# ----------------------------
CAMERA_MODE = "B"   # "A" = photo, "B" = video C = Disabled

# ----------------------------
# UTILITY FUNCTIONS
# ----------------------------
def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def record_photo():
    ensure_folder_exists(SAVE_FOLDER)
    filename = os.path.join(
        SAVE_FOLDER,
        f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    )
    print("[CAMERA] Capturing photo...")
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
    print(f"[CAMERA] Photo saved: {filename}")

def start_video_recording():
    ensure_folder_exists(SAVE_FOLDER)
    filename = os.path.join(
        SAVE_FOLDER,
        f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )

    print("[CAMERA] Recording with GPU acceleration...")

    process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",

            # increase capture buffer (prevents dropped frames)
            "-rtbufsize", "100M",

            "-f", "dshow",
            "-video_size", "800x600",
            "-framerate", "30",

            "-i", "video=HD Pro Webcam C920:audio=Microphone (HD Pro Webcam C920)",

            # ⚡ HARDWARE ENCODING (fast & smooth)
            "-vcodec", "h264_qsv",

            # fallback if qsv fails:
            # "-vcodec", "h264_nvenc",

            "-preset", "veryfast",

            # audio
            "-acodec", "aac",

            # compatibility
            "-pix_fmt", "yuv420p",

            filename
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return process

# ----------------------------
# SERIAL PORT DETECTION
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

    raise RuntimeError(f"[ERROR] Could not find device matching '{name_hint}'.")

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

# ----------------------------
# ROBOT FUNCTIONS
# ----------------------------
def send_robot_line(cmd):
    print(f"[SEND] {cmd}")
    robot.write((cmd + "\r").encode())

    # wait for real completion
    while True:
        if robot.in_waiting:
            line = robot.readline().decode().strip()
            if line:
                print(f"[ROBOT] {line}")
            if line.lower() == "ok":
                break

def run_coords_sequence():
    print("[ROBOT] Running coords.txt...")
    with open(COORDS_FILE) as f:
        for line in f:
            cmd = line.strip()
            if cmd:
                send_robot_line(cmd)

    arduino.write(b"SEQUENCE_COMPLETE\n")
    print("[ROBOT] Sequence complete.")

def wait_for_button():

    if AUTO_BUTTON:
        print(f"[AUTO] Simulating button press in {BUTTON_INTERVAL} seconds...")
        time.sleep(BUTTON_INTERVAL)
        print("[AUTO] Button simulated")
        return

    print("[DEBUG] Waiting for button press... THIS WAS MADE BY NIC KRAUSE AND JUST NIC KRAUSE IF YOU TAKE CREDIT FOR THIS I WILL FIND YOU -love nic ")

    while True:

        if arduino.in_waiting:

            msg = arduino.readline().decode().strip()

            print(f"[ARDUINO] {msg}")

            if "BUTTON_PRESSED" in msg:
                print("[DEBUG] Button accepted.")
                return

# ----------------------------
# STARTUP
# ----------------------------
print("\n[DEBUG] Running startup sequence...")
send_robot_line("G28")
send_robot_line("G0 E90 F40")
print("[DEBUG] Startup done.\n")
print("Ready for button.")

# ----------------------------
# MAIN LOOP
# ----------------------------
while True:
    increment_counter()
    wait_for_button()

    if CAMERA_MODE.upper() == "A":
        # Photo mode
        record_photo()
        run_coords_sequence()

    else:
        # Video mode: record while robot moves
        ffmpeg_process = start_video_recording()

        run_coords_sequence()

        print("[CAMERA] Stopping recording...")
        ffmpeg_process.communicate(input=b"q")

    print("Ready for next button press.")