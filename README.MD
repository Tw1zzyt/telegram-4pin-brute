# Android PIN Testing Tool

A Python utility for demonstrating PIN-entry automation on Android devices through Android Debug Bridge (ADB). The project is intended for authorized CTF exercises and controlled lab environments.

## Scope and Authorization

Use this tool only on devices you own or on systems for which you have explicit authorization. Do not use it to access another person's device or any system without permission.

The tool automates PIN entry and observes changes to the lock-screen image. It does not exploit a software vulnerability or bypass device encryption. The device must be accessible over ADB, with USB debugging enabled.

## Features

- Connects to an Android device through ADB.
- Captures a reference image of the lock screen.
- Enters PIN combinations using ADB input commands.
- Compares screenshots using the root mean square (RMS) image difference.
- Checks for persistent screen changes to reduce false positives from transient animations.
- Saves progress so a test can be resumed after interruption.

## Requirements

| Component | Requirement |
|---|---|
| Operating system | Windows by default; see the configuration notes for other platforms |
| Python | 3.10 or later |
| Python package | Pillow |
| Android tools | Android SDK Platform-Tools (`adb`) |
| Device | Android device with USB debugging enabled |

Install the Python dependency:

```bash
python -m pip install pillow
```

## Configuration

Open `tg.py` and review the configuration constants near the top of the file. Set `ADB_PATH` to the location of `adb.exe` on your system.

The `KEYPAD_COORDS` values must match the keypad layout and screen resolution of the test device. They are device-specific and should be verified before running a test. You’ll need to capture them manually (for example, via “Developer Options → Show Coordinates” or `adb shell getevent`) and substitute them for your specific setup. Review the timing and image-comparison settings as well, since behavior can vary between devices.

The script uses Python's `Image.Image | None` type syntax, which requires Python 3.10 or later.

## Running

Confirm that ADB can detect the authorized test device:

```bash
adb devices
```

Then run the script:

```bash
python tg.py
```

Keep the device connected throughout the test. Review the script's output for connection errors or other diagnostic messages.

## Output Files

| File | Description |
|---|---|
| `progress.txt` | Stores the current progress index for resuming an interrupted run |
| `SUCCESS_PIN.txt` | Stores the result reported by the script, including the PIN, attempt number, and RMS value |

Treat output files as sensitive: they may contain access credentials or test results. Do not publish them in the repository.

## Detection Logic

After an input attempt, the script waits for the configured delay and captures a screenshot. It compares that image with the reference using the RMS difference. If the difference exceeds the configured threshold, the script waits for the screen to settle and captures another screenshot.

A result is recorded only when the screen change persists across both checks. This is intended to reduce false positives caused by temporary lock-screen animations. Progress is written after each attempt so an interrupted run can be resumed.

## Troubleshooting

**The device is not listed by `adb devices`.**  
Check the USB connection, confirm that USB debugging is enabled, and verify that the device has authorized the connected computer.

**The script reports a false trigger.**  
Screen transitions and animations vary by device. Review the image-comparison threshold and settling delay in the configuration.

**Can I use an emulator?**  
The script may be used in a controlled emulator environment if ADB connectivity and keypad coordinates are configured for that environment.

**Is Linux or macOS supported?**  
The script's ADB interaction is not inherently Windows-specific, but the configured ADB path and device coordinates must match the environment. Verify compatibility before use.

## License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
