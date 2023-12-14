import cv2
import numpy as np
import time
import asyncio

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.camera import Camera
from viam.components.board import Board
from viam.components.motor import Motor
from viam.components.base import Base
from viam.components.encoder import Encoder
from viam.components.movement_sensor import MovementSensor
from viam.services.vision import VisionClient



DEFAULT_COORDS = ((0,0), (1080, 1920))
CROP_COORDS = ((400, 160), (1100, 1600))

FRAME_WIDTH_CROP = CROP_COORDS[1][1] - CROP_COORDS[0][1]

MAGENTA = (255, 0, 255)
RED = (255, 0, 0)

reset = False

# Detecting blue/yellow objects
blue_lower = np.array([110, 50, 50])
blue_upper = np.array([130, 255, 255])
yellow_lower = np.array([20, 100, 100])
yellow_upper = np.array([30, 255, 255])

# Blue object has area ~ 1430, Yellow object has area ~ 1800
min_contour_area = 1000
max_contour_area = 2500

async def connect():
    creds = Credentials(
        type="robot-location-secret",
        payload="ueg84ir6sdbxw388tcqz3ycupdzfrlicmgt1h7aev467sh7w")
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address("samgubb2-main.wm4vlppvex.viam.cloud", opts)

def area_in_range(contour):
    area = cv2.contourArea(contour)
    return min_contour_area < area < max_contour_area

def get_blue_yellow_objects(frame):
    def detect_color(color_lower, color_upper):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, color_lower, color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    contours_blue = detect_color(blue_lower, blue_upper)
    contours_yellow = detect_color(yellow_lower, yellow_upper)
    return [b for b in contours_blue if area_in_range(b)], \
           [y for y in contours_yellow if area_in_range(y)]

class GameState:
    def __init__(self, left_zone, right_zone, max_score, max_time):
        self.left_zone = left_zone
        self.right_zone = right_zone
        self.max_score = max_score
        self.max_time = max_time
        
        self.start_time = time.time()
        self.score = 0
        self.target_left = True
        self.prev_x_normalized = 0

    def update_score_and_zone(self, object_x):
        left_zone_x = int(self.left_zone * FRAME_WIDTH_CROP)
        right_zone_x = int((1 - self.right_zone) * FRAME_WIDTH_CROP)

        if self.target_left and object_x < left_zone_x and self.prev_x_normalized >= 0.0:
            self.score += 1
            self.target_left = False
        elif not self.target_left and object_x > right_zone_x and self.prev_x_normalized <= 1.0:
            self.score += 1
            self.target_left = True
        
        """normalized x falls into range [0,1] such that
        if x = 0, it's at the left zone boundary.
        elif x = 1, it's at the right zone boundary.
        used to ensure you don't continuously get points while in the target zone"""
        self.prev_x_normalized = (object_x - left_zone_x) / right_zone_x 
    
    def is_over(self):
        if self.score >= self.max_score:
            return "You win!"
        if time.time() - self.start_time > self.max_time: # or if you get hit
            return "You lose!"
        return None

def process_frame(video_feed, game_state):
    ret, frame = video_feed.read()
    frame = frame[CROP_COORDS[0][0]:CROP_COORDS[1][0], CROP_COORDS[0][1]:CROP_COORDS[1][1]]
    contours_blue, contours_yellow = get_blue_yellow_objects(frame)

    for contour in contours_blue:
        x, y, w, h = cv2.boundingRect(contour)
        centroid_x = x + w // 2
        centroid_y = y + h // 2
        game_state.update_score_and_zone(centroid_x)

    

    draw_contours(frame, contours_blue, RED)
    draw_contours(frame, contours_yellow, RED)
    
    display_frame(frame, game_state)

def draw_contours(frame, contours, color):
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        center_x = x + w // 2
        center_y = y + h // 2
        # print(f"({center_x}, {center_y})")
        area = int(cv2.contourArea(contour))
        text = f'Area: {area}'
        cv2.putText(frame, text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

def display_frame(frame, game_state):
    frame_height, frame_width, _ = frame.shape
    left_zone_x = int(game_state.left_zone * frame_width)
    right_zone_x = int(game_state.right_zone * frame_width)

    cv2.line(frame, (left_zone_x, 0), (left_zone_x, frame_height), MAGENTA, 2)
    cv2.line(frame, (right_zone_x, 0), (right_zone_x, frame_height), MAGENTA, 2)
    cv2.putText(frame, f'Score: {game_state.score}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 2)
    
    cv2.imshow('Gameplay', frame)

async def positions(frame, leftRight = 0, upDown = 0):
    contours_blue, contours_yellow = get_blue_yellow_objects(frame)
    if contours_blue and contours_yellow:
        contour_blue = contours_blue[0]
        contour_yellow = contours_yellow[0]
        (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
        (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
    else:
        print("contours_blue, yellow DNE")
        return None, None
    # if (yellowY<blueY):
    #     print("Setting upDown to 1")
    #     upDown = 1
    #     if (blueX>yellowX):
    #         leftRight = -1
    #     elif (blueX<yellowX):
    #         leftRight = 1
    # elif (yellowY>blueY):
    #     print("Setting upDown to -1")
    #     upDown = -1
    #     if (blueX>yellowX):
    #         leftRight = 1
    #     elif (blueX<yellowX):
    #         leftRight = -1


    if (yellowY<blueY):
        upDown = 1
        if (blueX<yellowX):
            leftRight = -1
        elif (blueX>yellowX):
            leftRight = 1
    elif (yellowY>blueY):
        upDown = -1
        if (blueX<yellowX):
            leftRight = 1
        elif (blueX>yellowX):
            leftRight = -1
    return leftRight, upDown

async def defend_rotate(frame, leftMotor, rightMotor, speed=100, ratio=0.453):
    contours_blue, contours_yellow = get_blue_yellow_objects(frame)
    leftRight, upDown = await positions(frame)
    print("GOALIE MODE")
    # Wrap coroutine objects in asyncio Tasks
    revNumber = 5
    if leftRight == -1:
        left_motor_task = asyncio.create_task(leftMotor.go_for(ratio * speed, -revNumber))
        right_motor_task = asyncio.create_task(rightMotor.go_for(speed, -revNumber))
    elif leftRight == 1:
        left_motor_task = asyncio.create_task(leftMotor.go_for(speed, -revNumber))
        right_motor_task = asyncio.create_task(rightMotor.go_for(ratio * speed, -revNumber))

    # Use asyncio.wait with the Task objects
    done, pending = await asyncio.wait(
        [left_motor_task, right_motor_task], 
        return_when=asyncio.FIRST_COMPLETED
    )

    # Cancel any pending tasks
    for task in pending:
        task.cancel()

    # Handle exceptions
    for task in done:
        if task.exception():
            print(f"Error encountered: {task.exception()}")

async def defend_forward(video_feed, base, speed=200, ratio=0.453):
    print("FORWARD MODE")
    #GLOBAL VARIABLE RESET set to TRUE when player has scored point, set to false again once robot arrives at starting pos
    while reset == False:
        ret, frame = video_feed.read()
        leftRight, upDown = await positions(frame)
        if upDown == 1:
            await base.move_straight(velocity=speed, distance=200)
        elif upDown == -1:
            await base.move_straight(velocity=speed, distance=-200)

async def main():
    video_feed = cv2.VideoCapture(0)
    
    # To change difficulty of game, change these 4 variables
    left_zone, right_zone = 0.3, 0.7
    maxScore, maxTime = 5, 120000

    robot = await connect()
    base = Base.from_robot(robot, "viam_base")

    left_motor = Motor.from_robot(robot, "left")
    right_motor = Motor.from_robot(robot, "right")

    game_state = GameState(left_zone, right_zone, maxScore, maxTime)
    while True:
        process_frame(video_feed, game_state)
        if reset == False:
            ret, frame = video_feed.read()
            await defend_rotate(frame, left_motor, right_motor)
            await defend_forward(video_feed, base)

        if game_state.is_over():
         print(game_state.is_over())
         break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_feed.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    asyncio.run(main())