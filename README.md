# Hand-Gesture System Control

A Python webcam application that controls system volume and display brightness with hand gestures. It uses MediaPipe's Hand Landmarker to track up to two hands, OpenCV to display the camera feed, Pycaw to set the Windows master volume, and `screen-brightness-control` to set display brightness.

## What it does

- Reads frames from the default webcam and shows a mirrored live preview.
- Detects and draws landmarks for up to two hands.
- Uses the distance between the thumb tip and index-finger tip as the control value.
- Maps the **right hand** gesture to master volume and the **left hand** gesture to display brightness.
- Smooths control changes and limits updates to at most 20 per second.
- Resets volume and brightness to 50% when it detects two open palms.
- Shows the current volume or brightness near the detected hand and shows the measured FPS.

Press `q` while the preview window is focused to exit.

## How it works

`main.py` loads the bundled MediaPipe hand-landmarker model from `models/hand_landmarker.task`. If the file is missing, the program downloads the same model from MediaPipe's Google Cloud Storage location and saves it in that directory.

For each camera frame, the application:

1. Mirrors the frame and runs MediaPipe hand-landmark detection in video mode.
2. Measures the pixel distance between landmark 4 (thumb tip) and landmark 8 (index-finger tip).
3. Interpolates a distance of 20–200 pixels to a 0–100% control range, then applies exponential smoothing.
4. Sends the right hand's result to the system volume endpoint and the left hand's result to the brightness controller.
5. Checks whether both detected hands meet the app's open-palm heuristic and, if so, resets both controls to 50%.

The program also prints detected hand labels, confidence values, and control updates to the console.

## Requirements

- Python (the repository does not specify a required version)
- A webcam accessible as camera device `0`
- Windows system audio support: volume control uses Pycaw's Windows audio endpoint
- A display supported by `screen-brightness-control`
- Internet access only if `models/hand_landmarker.task` is not already present

Install the Python packages imported by the project:

```bash
pip install opencv-python mediapipe numpy screen-brightness-control pycaw
```

## Setup

```bash
git clone https://github.com/ShriShailesh-source/HG.git
cd HG
pip install opencv-python mediapipe numpy screen-brightness-control pycaw
```

The repository already includes the hand-landmarker model at `models/hand_landmarker.task`; no separate model setup is normally needed.

## Usage

Start the gesture controller:

```bash
python main.py
```

Keep your hand visible to the webcam and change the separation between your thumb and index finger:

- Right hand: adjusts master volume.
- Left hand: adjusts display brightness.
- Two open palms: sets both volume and brightness to 50%.

To quit, focus the OpenCV window and press `q`.

## Testing

There is no automated test suite or test runner configuration in the repository. `test_volume.py` is a manual Windows audio check: it prints the current master-volume scalar, sets it to `0.3`, then to `0.7`, and prints the values after each change.

Run it with:

```bash
python test_volume.py
```

This script changes the system master volume.

## Project structure

```text
.
├── main.py                     # Webcam gesture controller
├── test_volume.py              # Manual Pycaw volume-control check
├── models/
│   └── hand_landmarker.task    # MediaPipe hand-landmarker model
└── README.md
```
