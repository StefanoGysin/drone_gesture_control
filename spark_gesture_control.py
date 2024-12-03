import cv2
import mediapipe as mp
import numpy as np
from enum import Enum
from djitellopy import Tello
import time

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
    FLIP = "FLIP"
    PHOTO = "PHOTO"

class SparkController:
    def __init__(self):
        # Inicializa o drone
        self.drone = Tello()
        self.drone.connect()
        
        # Verifica a bateria
        self.battery = self.drone.get_battery()
        print(f"Battery Level: {self.battery}%")
        
        # Configurações de velocidade
        self.speed = 30  # Velocidade entre 0-100
        self.drone.set_speed(self.speed)
        
        # Inicializa o stream de vídeo
        self.drone.streamon()
        
    def execute_command(self, command):
        if not command:
            self.drone.send_rc_control(0, 0, 0, 0)  # Hover
            return
            
        try:
            if command == DroneCommands.TAKEOFF:
                if not self.drone.is_flying:
                    self.drone.takeoff()
            
            elif command == DroneCommands.LAND:
                self.drone.land()
            
            elif command == DroneCommands.FORWARD:
                self.drone.send_rc_control(0, self.speed, 0, 0)
            
            elif command == DroneCommands.BACKWARD:
                self.drone.send_rc_control(0, -self.speed, 0, 0)
            
            elif command == DroneCommands.LEFT:
                self.drone.send_rc_control(-self.speed, 0, 0, 0)
            
            elif command == DroneCommands.RIGHT:
                self.drone.send_rc_control(self.speed, 0, 0, 0)
            
            elif command == DroneCommands.UP:
                self.drone.send_rc_control(0, 0, self.speed, 0)
            
            elif command == DroneCommands.DOWN:
                self.drone.send_rc_control(0, 0, -self.speed, 0)
            
            elif command == DroneCommands.FLIP:
                self.drone.flip_forward()
            
            elif command == DroneCommands.PHOTO:
                self.drone.take_picture()
            
            else:  # HOVER
                self.drone.send_rc_control(0, 0, 0, 0)
                
        except Exception as e:
            print(f"Error executing command {command}: {str(e)}")
            self.drone.send_rc_control(0, 0, 0, 0)  # Emergency hover
    
    def get_frame(self):
        return self.drone.get_frame_read().frame
    
    def cleanup(self):
        self.drone.streamoff()
        self.drone.end()

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
        
        # Controle de tempo para evitar comandos muito rápidos
        self.last_command_time = time.time()
        self.command_cooldown = 1.0  # 1 segundo entre comandos
        
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
            
            # Analyze gesture with cooldown
            current_time = time.time()
            if current_time - self.last_command_time >= self.command_cooldown:
                command = self._interpret_gesture(landmarks)
                if command:
                    self.last_command_time = current_time
            
            # Display command
            if command:
                cv2.putText(frame, command.value, (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
        return frame, command
    
    def _interpret_gesture(self, landmarks):
        landmarks = np.array(landmarks)
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        palm_center = landmarks[0]
        
        fingers_extended = self._count_extended_fingers(landmarks)
        
        # Gestos específicos para o Spark
        if fingers_extended == 5:  # Mão aberta
            return DroneCommands.TAKEOFF
        
        elif fingers_extended == 0:  # Punho fechado
            return DroneCommands.LAND
        
        elif fingers_extended == 1 and self._is_finger_extended(landmarks, 8):  # Apenas indicador
            direction = index_tip - palm_center
            if abs(direction[0]) > abs(direction[1]):  # Movimento horizontal
                return DroneCommands.RIGHT if direction[0] > 0 else DroneCommands.LEFT
            else:  # Movimento vertical
                return DroneCommands.UP if direction[1] < 0 else DroneCommands.DOWN
        
        elif fingers_extended == 2:  # Dois dedos
            if self._is_finger_extended(landmarks, 8) and self._is_finger_extended(landmarks, 12):
                return DroneCommands.FORWARD
        
        elif fingers_extended == 3:  # Três dedos
            if (self._is_finger_extended(landmarks, 8) and 
                self._is_finger_extended(landmarks, 12) and 
                self._is_finger_extended(landmarks, 16)):
                return DroneCommands.FLIP
        
        elif fingers_extended == 4:  # Quatro dedos
            if (self._is_finger_extended(landmarks, 8) and 
                self._is_finger_extended(landmarks, 12) and 
                self._is_finger_extended(landmarks, 16) and 
                self._is_finger_extended(landmarks, 20)):
                return DroneCommands.PHOTO
        
        return DroneCommands.HOVER
    
    def _count_extended_fingers(self, landmarks):
        count = 0
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
        return tip[1] < pip[1]
    
    def _is_thumb_extended(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        return abs(thumb_tip[0] - thumb_ip[0]) > 0.1

def main():
    # Inicializa os controladores
    drone_controller = SparkController()
    gesture_controller = GestureController()
    
    print("Iniciando sistema de controle por gestos...")
    print(f"Bateria do drone: {drone_controller.battery}%")
    
    try:
        while True:
            # Obtém frame do drone
            frame = drone_controller.get_frame()
            if frame is None:
                continue
                
            # Flip frame horizontally for more intuitive interaction
            frame = cv2.flip(frame, 1)
            
            # Detecta gestos
            frame, command = gesture_controller.detect_gesture(frame)
            
            # Executa comando no drone
            drone_controller.execute_command(command)
            
            # Mostra status na tela
            battery = drone_controller.drone.get_battery()
            height = drone_controller.drone.get_height()
            cv2.putText(frame, f"Battery: {battery}%", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f"Height: {height}cm", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Mostra o frame
            cv2.imshow('Spark Gesture Control', frame)
            
            # Sai com 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        # Limpa recursos
        print("Encerrando sistema...")
        drone_controller.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()