import cv2
import mediapipe as mp
import numpy as np
from enum import Enum

class DroneCommands(Enum):
    TAKEOFF = "TAKEOFF"
    LAND = "LAND"
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DOWN = "DOWN"
    HOVER = "HOVER"

class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def detect_gesture(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        command = None
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw hand landmarks
            self.mp_draw.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Get landmark positions
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])
            
            # Analyze gesture
            command = self._interpret_gesture(landmarks)
            
            # Display command
            if command:
                cv2.putText(frame, command.value, (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
        return frame, command
    
    def _interpret_gesture(self, landmarks):
        # Convert landmarks to numpy array for easier calculations
        landmarks = np.array(landmarks)
        
        # Get specific finger positions
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        palm_center = landmarks[0]
        
        # Calculate if fingers are extended
        fingers_extended = self._count_extended_fingers(landmarks)
        
        # Interpret gestures
        if fingers_extended == 5:  # All fingers extended
            return DroneCommands.TAKEOFF
        
        elif fingers_extended == 0:  # Fist
            return DroneCommands.LAND
        
        elif fingers_extended == 1 and self._is_finger_extended(landmarks, 8):  # Only index finger
            # Check direction
            direction = index_tip - palm_center
            if abs(direction[0]) > abs(direction[1]):  # Horizontal movement
                return DroneCommands.RIGHT if direction[0] > 0 else DroneCommands.LEFT
            else:  # Vertical movement
                return DroneCommands.UP if direction[1] < 0 else DroneCommands.DOWN
        
        elif fingers_extended == 2 and self._is_finger_extended(landmarks, 8) and self._is_finger_extended(landmarks, 12):
            return DroneCommands.FORWARD
            
        return DroneCommands.HOVER
    
    def _count_extended_fingers(self, landmarks):
        count = 0
        # Check each finger
        if self._is_finger_extended(landmarks, 8):  # Index
            count += 1
        if self._is_finger_extended(landmarks, 12):  # Middle
            count += 1
        if self._is_finger_extended(landmarks, 16):  # Ring
            count += 1
        if self._is_finger_extended(landmarks, 20):  # Pinky
            count += 1
        if self._is_thumb_extended(landmarks):  # Thumb
            count += 1
        return count
    
    def _is_finger_extended(self, landmarks, tip_idx):
        tip = landmarks[tip_idx]
        pip = landmarks[tip_idx - 2]
        return tip[1] < pip[1]  # Y coordinate comparison
    
    def _is_thumb_extended(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        return abs(thumb_tip[0] - thumb_ip[0]) > 0.1

def main():
    cap = cv2.VideoCapture(0)
    controller = GestureController()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip frame horizontally for more intuitive interaction
        frame = cv2.flip(frame, 1)
        
        # Process frame and detect gestures
        frame, command = controller.detect_gesture(frame)
        
        # Display the frame
        cv2.imshow('Drone Gesture Control', frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()