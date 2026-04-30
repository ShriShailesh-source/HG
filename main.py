import cv2
import mediapipe as mp
import math
import numpy as np
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

# --- 1. INITIALIZATION ---
# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Volume Control setup (Windows pycaw)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()  # Returns (min, max, increment)
min_vol, max_vol = vol_range[0], vol_range[1]

# Variables for smoothing and UI
vol_per = 0
bright_per = 0
pTime = 0

def calculate_distance(p1, p2):
    """Calculates Euclidean distance between two landmarks."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def is_palm_open(hand_landmarks):
    """Returns True if all fingers are extended (palm open)."""
    # Landmark IDs for tips: Index(8), Middle(12), Ring(16), Pinky(20)
    # We compare tip y-coordinate with the PIP joint y-coordinate
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    count = 0
    for t, p in zip(tips, pips):
        if hand_landmarks.landmark[t].y < hand_landmarks.landmark[p].y:
            count += 1
    # Check thumb separately (x-axis comparison usually better for thumb)
    if abs(hand_landmarks.landmark[4].x - hand_landmarks.landmark[17].x) > 0.1:
        count += 1
    return count == 5

# --- 2. MAIN LOOP ---
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1) # Flip for natural mirror effect
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    h, w, _ = img.shape
    open_palms_count = 0

    if results.multi_hand_landmarks:
        # Iterate through detected hands and identify them
        for i, hand_lms in enumerate(results.multi_hand_landmarks):
            # Get handedness (Left vs Right)
            # MediaPipe's handedness can be tricky due to mirroring, 
            # so we use the classification label directly.
            label = results.multi_handedness[i].classification[0].label 
            
            # Draw landmarks
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # Extract coordinates for Thumb tip (4) and Index tip (8)
            landmarks = []
            for id, lm in enumerate(hand_lms.landmark):
                landmarks.append([int(lm.x * w), int(lm.y * h)])
            
            thumb_tip = landmarks[4]
            index_tip = landmarks[8]
            
            # Gesture Calculation: Distance between thumb and index
            dist = calculate_distance(thumb_tip, index_tip)
            
            # Detect open palm for reset feature
            if is_palm_open(hand_lms):
                open_palms_count += 1

            # --- 3. SYSTEM CONTROL ---
            # Right Hand -> Volume Control
            if label == 'Right':
                # Map distance (approx 20 to 200 pixels) to volume dB range
                # Thresholding: dist < 25 is 0%, dist > 180 is 100%
                vol_val = np.interp(dist, [30, 180], [min_vol, max_vol])
                vol_per = np.interp(dist, [30, 180], [0, 100])
                volume.SetMasterVolumeLevel(vol_val, None)
                cv2.putText(img, f'VOL: {int(vol_per)}%', (thumb_tip[0], thumb_tip[1]-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Left Hand -> Brightness Control
            elif label == 'Left':
                bright_per = np.interp(dist, [30, 180], [0, 100])
                sbc.set_brightness(int(bright_per))
                cv2.putText(img, f'BRIGHT: {int(bright_per)}%', (thumb_tip[0], thumb_tip[1]-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # --- 4. EXTRA FEATURE: RESET TO 50% ---
        if open_palms_count == 2:
            volume.SetMasterVolumeLevel(np.interp(50, [0, 100], [min_vol, max_vol]), None)
            sbc.set_brightness(50)
            cv2.putText(img, "RESET TO 50%", (w//2-100, 50), 
                        cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)

    # UI: FPS and Labels
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
    
    cv2.imshow("Dual-Hand System Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()