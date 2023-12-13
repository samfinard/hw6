import cv2
import numpy as np

class ObjectDetector:
    def __init__(self):
        # HSV color range for blue
        self.blue_lower = np.array([110, 50, 50])
        self.blue_upper = np.array([130, 255, 255])

        # HSV color range for yellow
        self.yellow_lower = np.array([20, 100, 100])
        self.yellow_upper = np.array([30, 255, 255])

        # Minimum contour area for detection
        self.min_contour_area = 500

    def detect_color(self, frame, color_lower, color_upper):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, color_lower, color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def detect_objects(self, frame):
        contours_blue = self.detect_color(frame, self.blue_lower, self.blue_upper)
        contours_yellow = self.detect_color(frame, self.yellow_lower, self.yellow_upper)
        return contours_blue, contours_yellow

class GameController:
    def __init__(self, frame_width, left_zone_ratio=0.3, right_zone_ratio=0.7):
        self.left_zone = int(frame_width * left_zone_ratio)
        self.right_zone = int(frame_width * right_zone_ratio)
        self.score = 0
        self.target_left = True

    def update_score_and_zone(self, object_x):
        if (self.target_left and object_x < self.left_zone) or \
           (not self.target_left and object_x > self.right_zone):
            self.score += 1
            self.target_left = not self.target_left

    def get_score(self):
        return self.score

    def is_target_left(self):
        return self.target_left

class VideoProcessor:
    def __init__(self, detector, game_controller, original_frame_width):
        self.detector = detector
        self.game_controller = game_controller
        self.cap = cv2.VideoCapture(0)
        self.crop_coords = ((400, 160), (1100, 1600))
        self.original_frame_width = original_frame_width

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        frame = frame[self.crop_coords[0][0]:self.crop_coords[1][0], self.crop_coords[0][1]:self.crop_coords[1][1]]
        contours_blue, contours_yellow = self.detector.detect_objects(frame)
        for contour in contours_blue:
            if cv2.contourArea(contour) > self.detector.min_contour_area:
                x, y, w, h = cv2.boundingRect(contour)
                centroid_x = x + w // 2
                self.game_controller.update_score_and_zone(centroid_x)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        self.draw_contours(frame, contours_yellow, (255, 255, 0), self.detector.min_contour_area)
        self.display_frame(frame)
        return True

    def draw_contours(self, frame, contours, color, min_contour_area):
        for contour in contours:
            if cv2.contourArea(contour) > min_contour_area:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

    def display_frame(self, frame):
        frame_height, frame_width, _ = frame.shape

        # Update coordinates based on the cropped frame size
        left_zone = int(self.game_controller.left_zone * frame_width / self.original_frame_width)
        right_zone = int(self.game_controller.right_zone * frame_width / self.original_frame_width)

        # Draw lines at left and right zones
        cv2.line(frame, (left_zone, 0), (left_zone, frame_height), (0, 255, 0), 2)
        cv2.line(frame, (right_zone, 0), (right_zone, frame_height), (0, 255, 0), 2)
        cv2.putText(frame, f'Score: {self.game_controller.get_score()}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.imshow('Object Detector', frame)

    def release_resources(self):
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    detector = ObjectDetector()
    cap = cv2.VideoCapture(0)  # Capture video
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Get original frame width
    processor = VideoProcessor(detector, GameController(frame_width=frame_width), original_frame_width=frame_width)

    while True:
        if not processor.process_frame():
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    processor.release_resources()

if __name__ == "__main__":
    main()
