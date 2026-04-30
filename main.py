import cv2
import mediapipe as mp
import math
import numpy as np
import os
import time
import urllib.request

import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def ensure_model_exists() -> None:
    """Download the hand landmarker model once and cache it locally."""
    if os.path.exists(MODEL_PATH):
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def calculate_distance(p1, p2) -> float:
    """Calculate Euclidean distance between two 2D points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def is_palm_open(hand_landmarks) -> bool:
    """Return True if all five fingers look extended."""
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    count = 0

    for t, p in zip(tips, pips):
        if hand_landmarks[t].y < hand_landmarks[p].y:
            count += 1

    # Thumb check uses x-axis separation as a simple heuristic.
    if abs(hand_landmarks[4].x - hand_landmarks[17].x) > 0.1:
        count += 1

    return count == 5


def draw_hand(img, landmarks, width, height) -> None:
    """Draw hand points and skeleton lines."""
    points = []
    for lm in landmarks:
        x = int(lm.x * width)
        y = int(lm.y * height)
        points.append((x, y))
        cv2.circle(img, (x, y), 4, (255, 200, 0), -1)

    for start, end in HAND_CONNECTIONS:
        cv2.line(img, points[start], points[end], (0, 255, 255), 2) 


def create_landmarker() -> vision.HandLandmarker:
    ensure_model_exists()
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    return vision.HandLandmarker.create_from_options(options)


def setup_volume_control():
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
    return volume


def main() -> None:
    landmarker = create_landmarker()
    volume = setup_volume_control()
    print(f"System volume initialized. Current scalar: {volume.GetMasterVolumeLevelScalar():.2f}")

    cap = cv2.VideoCapture(0)
    p_time = 0.0

    try:
        while True:
            success, img = cap.read()
            if not success:
                break

            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            timestamp_ms = int(time.time() * 1000)
            results = landmarker.detect_for_video(mp_image, timestamp_ms)

            h, w, _ = img.shape
            open_palms_count = 0

            if results.hand_landmarks:
                print(f"Hands detected: {len(results.hand_landmarks)}")
                for i, hand_lms in enumerate(results.hand_landmarks):
                    label = results.handedness[i][0].category_name
                    print(f"  Hand {i}: label={label}")
                    draw_hand(img, hand_lms, w, h)

                    landmarks = [[int(lm.x * w), int(lm.y * h)] for lm in hand_lms]
                    thumb_tip = landmarks[4]
                    index_tip = landmarks[8]
                    dist = calculate_distance(thumb_tip, index_tip)

                    if is_palm_open(hand_lms):
                        open_palms_count += 1

                    if label == "Right":
                        vol_scalar = float(np.interp(dist, [30, 180], [0, 1]))
                        vol_per = np.interp(dist, [30, 180], [0, 100])
                        print(f"DEBUG Right hand: dist={dist:.1f}, vol_scalar={vol_scalar:.2f}, vol_per={vol_per:.1f}%")
                        try:
                            volume.SetMasterVolumeLevelScalar(vol_scalar, None)
                            print(f"  -> Volume set to {vol_per:.1f}%")
                        except Exception as e:
                            print(f"  -> ERROR setting volume: {e}")
                        cv2.putText(
                            img,
                            f"VOL: {int(vol_per)}%",
                            (thumb_tip[0], thumb_tip[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 0, 0),
                            2,
                        )
                    elif label == "Left":
                        bright_per = np.interp(dist, [30, 180], [0, 100])
                        print(f"DEBUG Left hand: dist={dist:.1f}, bright_per={bright_per:.1f}%")
                        try:
                            sbc.set_brightness(int(bright_per))
                            print(f"  -> Brightness set to {bright_per:.1f}%")
                        except Exception as e:
                            print(f"  -> ERROR setting brightness: {e}")
                        cv2.putText(
                            img,
                            f"BRIGHT: {int(bright_per)}%",
                            (thumb_tip[0], thumb_tip[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2,
                        )

                if open_palms_count == 2:
                    try:
                        volume.SetMasterVolumeLevelScalar(0.5, None)
                    except Exception:
                        pass
                    sbc.set_brightness(50)
                    cv2.putText(
                        img,
                        "RESET TO 50%",
                        (w // 2 - 100, 50),
                        cv2.FONT_HERSHEY_DUPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )

            c_time = time.time()
            fps = 0 if p_time == 0 else 1 / (c_time - p_time)
            p_time = c_time

            cv2.putText(
                img,
                f"FPS: {int(fps)}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2,
            )

            cv2.imshow("Dual-Hand System Control", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
