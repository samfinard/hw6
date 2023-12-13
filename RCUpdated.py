import cv2
import numpy as np
import time

class ObjectDetector:
    def __init__(self):
        # Color detection thresholds
        self.blue_lower = np.array([110, 50, 50])    
        self.blue_upper = np.array([130, 255, 255])  
        self.yellow_lower = np.array([20, 100, 100])      
        self.yellow_upper = np.array([30, 255, 255])  

        # Minimum contour area to be considered as a valid object
        self.min_contour_area = 2500

    def detect_blue(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, self.blue_lower, self.blue_upper)
        return blue_mask

    def detect_green(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        return green_mask

    def detect_object(self, frame):
        blue_mask = self.detect_blue(frame)
        green_mask = self.detect_green(frame)

        contours_blue, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_green, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        return contours_blue, contours_green

class RCCarGame:
    def __init__(self, left_threshold=0.3, right_threshold=0.3, gold_collection_interval=3):
        self.left_threshold = left_threshold
        self.right_threshold = right_threshold
        self.gold_collection_interval = gold_collection_interval
        self.score = 0
        self.gold_collected = 0
        self.last_gold_collection_time = None

    def determine_position(self, x, width):
        if x < width * self.left_threshold:
            return "left"
        elif x > width * (1 - self.right_threshold):
            return "right"
        else:
            return "middle"

    def update_game_state(self, position, x, frame_width):
        current_time = time.time()

        if position == "left":
            if self.last_gold_collection_time is None:
                self.last_gold_collection_time = current_time
            elif current_time - self.last_gold_collection_time >= self.gold_collection_interval:
                self.gold_collected += 1
                self.last_gold_collection_time = current_time
                print(f"Gold piece collected! Total Gold: {self.gold_collected}")

        elif position == "right":
            self.score += self.gold_collected
            if self.gold_collected > 0:
                print(f"Gold deposited! Score: {self.score}")
            self.gold_collected = 0

        # Reset the gold collection timer if the car leaves the left zone
        elif not position == "left" and self.last_gold_collection_time is not None:
            self.last_gold_collection_time = None

def video_stream_loop(cap, object_detector, game):
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Crop the carpet 
        frame_height = frame.shape[0]
        frame_width = frame.shape[1]
        # X1, Y1 = 90, 650 # Bottom left corner
        # X2, Y2, = 1260, 325 # Top right corner
        # frame = frame[Y1:Y2, X1:X2]

        contours_blue, contours_green = object_detector.detect_object(frame)

        # Process Blue Contours (RC Car)
        for contour in contours_blue:
            if cv2.contourArea(contour) < object_detector.min_contour_area:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            center_x = (x + w) // 2
            center_y = (y + h) // 2
            position = game.determine_position(center_x, frame_width)
            game.update_game_state(position, center_x, frame_width)
            print(f"Rover Coordinates: X={center_x}, Y={center_y}")  # Print the coordinates of the rover
            cv2.circle(frame, (center_x, center_y), 15, (255, 0, 0), 2)  # Green circle for RC Car

        # Process Green Contours (Rover)
        for contour in contours_green:
            if cv2.contourArea(contour) < object_detector.min_contour_area:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            center_x = (x + w) // 2
            center_y = (y + h) // 2
            cv2.circle(frame, (center_x, center_y), 15, (0, 255, 0), 2) 

        # Draw threshold lines
        frame_width = frame.shape[1]
        left_threshold_x = int(frame_width * game.left_threshold)
        right_threshold_x = int(frame_width * (1 - game.right_threshold))
        cv2.line(frame, (left_threshold_x, 0), (left_threshold_x, frame.shape[0]), (255, 0, 0), 2)
        cv2.line(frame, (right_threshold_x, 0), (right_threshold_x, frame.shape[0]), (255, 0, 0), 2)

        # Display the processed frame
        cv2.imshow("Video Stream", frame)

        # Exit the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()

def main():
    cap = cv2.VideoCapture(0)
    object_detector, game = ObjectDetector(), RCCarGame()

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture initial frame")
        cap.release()
        return
    
    video_stream_loop(cap, object_detector, game)

if __name__ == "__main__":
    main()
    