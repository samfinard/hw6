import cv2
import asyncio
import sys
import numpy as np
import math

from viam.robot.client import RobotClient
from viam.components.base import Base
from viam.components.motor import Motor
from viam.rpc.dial import Credentials, DialOptions


DEFAULT_COORDS = ((0,0), (1080, 1920))
CROP_COORDS = ((400, 160), (1100, 1600))
FRAME_WIDTH_CROP = CROP_COORDS[1][1] - CROP_COORDS[0][1]

MAGENTA = (255, 0, 255)
RED = (255, 0, 0)

# Detecting blue/yellow objects
blue_lower = np.array([70, 50, 50])
blue_upper = np.array([130, 255, 255])
yellow_lower = np.array([20, 100, 100])
yellow_upper = np.array([30, 255, 255])

# Blue object has area ~ 1430, Yellow object has area ~ 1800
min_contour_area = 1000
max_contour_area = 3000

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

def parse_contours(contours_blue, contours_yellow):
    if contours_blue and contours_yellow:
        contour_blue = contours_blue[0]
        contour_yellow = contours_yellow[0]
        (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
        (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
        return blueX, blueY, yellowX, yellowY
    else:
        sys.exit("Error: blue, yellow DNE")

def get_blue_yellow_contours(frame):
    def detect_color(color_lower, color_upper):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, color_lower, color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    contours_blue = detect_color(blue_lower, blue_upper)
    contours_yellow = detect_color(yellow_lower, yellow_upper)
    return [b for b in contours_blue if area_in_range(b)], \
           [y for y in contours_yellow if area_in_range(y)]

def is_hit(x1, y1, x2, y2, minDist = 150):
    if minDist > math.sqrt((x2 - x1)**2 + (y2 - y1)**2):
        sys.exit("You lose! Robot tagged you.")

async def up_or_down(frame, threshold = 50):
    blue_contours, yellow_contours = get_blue_yellow_contours(frame)
    blueX, blueY, yellowX, yellowY = parse_contours(blue_contours, yellow_contours)
    
    # Checks for hit
    is_hit(blueX, blueY, yellowX, yellowY)

    diff = yellowY - blueY
    
    if -threshold < diff < threshold:
        upDown = 0
    # Mirrors y coordinate
    elif diff > threshold:
        upDown = -1 # go down
    elif diff < -threshold: 
        upDown = 1 # go up
    return upDown



async def mirror(video_feed, base, speed=200, ratio=0.453, noMoveLimit = 50):
    print("Mirroring RC car")
    for i in range(100000):
        ret, frame = video_feed.read()
        frame = frame[CROP_COORDS[0][0]:CROP_COORDS[1][0], CROP_COORDS[0][1]:CROP_COORDS[1][1]]
        contours_blue, contours_yellow = get_blue_yellow_contours(frame)
        blueX, blueY, yellowX, yellowY = parse_contours(contours_blue, contours_yellow)
        upDown = await up_or_down(frame)
        
        is_hit(blueX, blueY, yellowX, yellowY)

        if yellowX < blueX:
            if upDown == 1: # move forwards
                await base.move_straight(velocity=speed, distance=200)
            elif upDown == 0: # do nothing
                continue
            elif upDown == -1: # move backwards
                await base.move_straight(velocity=speed, distance=-200)
        elif yellowX > blueX:
            sys.exit("Game over, you win!")


async def main():
    video_feed = cv2.VideoCapture(0)
    
    # Connect to the robot
    robot = await connect()  
    base = Base.from_robot(robot, "viam_base")
    left_motor = Motor.from_robot(robot, "left")
    right_motor = Motor.from_robot(robot, "right")

    await mirror(video_feed, base)
    

    video_feed.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    asyncio.run(main())