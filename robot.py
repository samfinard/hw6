import cv2
import numpy as np
import asyncio
from game import get_blue_yellow_objects
import shared_vars
import sys

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.camera import Camera
from viam.components.board import Board
from viam.components.motor import Motor
from viam.components.base import Base
from viam.components.encoder import Encoder
from viam.components.movement_sensor import MovementSensor
from viam.services.vision import VisionClient

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

    #CHECK FOR HIT
    if (np.abs(blueX-yellowX) < 10) and (np.abs(blueY-yellowY) < 10):
        print("YOU LOSE (ROBOT TAGGED YOU)")
        sys.exit()

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

    # # Cancel any pending tasks
    # for task in pending:
    #     task.cancel()

    # # Handle exceptions
    # for task in done:
    #     if task.exception():
    #         print(f"Error encountered: {task.exception()}")

async def defend_forward(video_feed, base, home, speed=200, ratio=0.453):
    print("FORWARD MODE")
    #GLOBAL VARIABLE RESET set to TRUE when player has scored point, set to false again once robot arrives at starting pos

    for i in range(100):
        ret, frame = video_feed.read()
        contours_blue, contours_yellow = get_blue_yellow_objects(frame)
        leftRight, upDown = await positions(frame)
        if contours_blue and contours_yellow:
            contour_blue = contours_blue[0]
            contour_yellow = contours_yellow[0]
            (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
            (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
        else:
            print("contours_blue, yellow DNE")
            break
        
        #CHECK FOR HIT
        if (np.abs(blueX-yellowX) < 10) and (np.abs(blueY-yellowY) < 10):
            print("YOU LOSE (ROBOT TAGGED YOU)")
            sys.exit()

        if (home == 0 and ((yellowX < blueX))):
            #print(shared_vars.reset)
            if upDown == 1:
                await base.move_straight(velocity=speed, distance=200)
            elif upDown == -1:
                await base.move_straight(velocity=speed, distance=-200)
        elif (home == 0 and ((yellowX > blueX))):
            print("YELLOW0: ")
            print(yellowX)
            print("BLUE0: ")
            print(blueX)
            shared_vars.home = 1
            shared_vars.points += 1
            print(shared_vars.points)
            print("HOME TARGET: ")
            print(shared_vars.home)
            await returnToHome(video_feed, base, shared_vars.home)
            break

        if (home == 1 and ((yellowX > blueX))):
            #print(shared_vars.reset)
            if upDown == 1:
                await base.move_straight(velocity=speed, distance=200)
            elif upDown == -1:
                await base.move_straight(velocity=speed, distance=-200)
        elif (home == 1 and ((yellowX < blueX))):
            print("YELLOW1: ")
            print(yellowX)
            print("BLUE1: ")
            print(blueX)
            shared_vars.home = 0
            shared_vars.points += 1
            print(shared_vars.points)
            print("HOME TARGET: ")
            print(shared_vars.home)
            await returnToHome(video_feed, base, shared_vars.home)
            break


    # #while shared_vars.reset == False:
    # for i in range(100):
    #     if shared_vars.reset == False:
    #         print(shared_vars.reset)
    #         ret, frame = video_feed.read()
    #         contours_blue, contours_yellow = get_blue_yellow_objects(frame)
    #         leftRight, upDown = await positions(frame)
    #         if upDown == 1:
    #             await base.move_straight(velocity=speed, distance=200)
    #         elif upDown == -1:
    #             await base.move_straight(velocity=speed, distance=-200)
    #     else:
    #         await returnToHome(video_feed, base, home)


#home = 0 or 1 depending which side robot is defending now
async def returnToHome(video_feed, base, home):
    print("Returning home")
    if home == 0:
        homeX = 180
        homeY = 350
    elif home == 1:
        homeX = 1200
        homeY = 350
    
    ret, frame = video_feed.read()
    contours_blue, contours_yellow = get_blue_yellow_objects(frame)
    if contours_blue and contours_yellow:
            contour_blue = contours_blue[0]
            contour_yellow = contours_yellow[0]
            (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
            (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
    #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
    yellowYtemp = yellowY
    await base.move_straight(velocity=200, distance=50)
    if contours_blue and contours_yellow:
        contour_blue = contours_blue[0]
        contour_yellow = contours_yellow[0]
        (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
        (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
    #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
    if yellowY < yellowYtemp:
        #FACING UP
        while np.abs(homeY-yellowY)>20:
            ret, frame = video_feed.read()
            contours_blue, contours_yellow = get_blue_yellow_objects(frame)
            if contours_blue and contours_yellow:
                contour_blue = contours_blue[0]
                contour_yellow = contours_yellow[0]
                (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
            #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
            if yellowY < homeY:
                await base.move_straight(velocity=200, distance=-50)
            if yellowY > homeY:
                await base.move_straight(velocity=200, distance=50)

        if contours_blue and contours_yellow:
            contour_blue = contours_blue[0]
            contour_yellow = contours_yellow[0]
            (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
            (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
        #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
        if yellowX < homeX:
            await base.spin(velocity=100, angle=90)
            while np.abs(homeX-yellowX)>20:
                ret, frame = video_feed.read()
                contours_blue, contours_yellow = get_blue_yellow_objects(frame)
                if contours_blue and contours_yellow:
                    contour_blue = contours_blue[0]
                    contour_yellow = contours_yellow[0]
                    (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                    (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
                #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
                await base.move_straight(velocity=200, distance=-50)
        if yellowX > homeX:
            await base.spin(velocity=100, angle=-90)
            while np.abs(homeX-yellowX)>20:
                ret, frame = video_feed.read()
                contours_blue, contours_yellow = get_blue_yellow_objects(frame)
                if contours_blue and contours_yellow:
                    contour_blue = contours_blue[0]
                    contour_yellow = contours_yellow[0]
                    (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                    (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
                #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
                await base.move_straight(velocity=200, distance=50)
        await base.spin(velocity=100, angle=180)
    elif yellowY > yellowYtemp:
        #FACING DOWN
        while np.abs(homeY-yellowY)>20:
            ret, frame = video_feed.read()
            contours_blue, contours_yellow = get_blue_yellow_objects(frame)
            if contours_blue and contours_yellow:
                contour_blue = contours_blue[0]
                contour_yellow = contours_yellow[0]
                (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
            #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
            if yellowY < homeY:
                await base.move_straight(velocity=200, distance=50)
            if yellowY > homeY:
                await base.move_straight(velocity=200, distance=-50)
        
        if contours_blue and contours_yellow:
            contour_blue = contours_blue[0]
            contour_yellow = contours_yellow[0]
            (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
            (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
        #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
        if yellowX < homeX:
            await base.spin(velocity=100, angle=-90)
            while np.abs(homeX-yellowX)>20:
                ret, frame = video_feed.read()
                contours_blue, contours_yellow = get_blue_yellow_objects(frame)
                if contours_blue and contours_yellow:
                    contour_blue = contours_blue[0]
                    contour_yellow = contours_yellow[0]
                    (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                    (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
                #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
                await base.move_straight(velocity=200, distance=-50)
        if yellowX > homeX:
            await base.spin(velocity=100, angle=90)
            while np.abs(homeX-yellowX)>20:
                ret, frame = video_feed.read()
                contours_blue, contours_yellow = get_blue_yellow_objects(frame)
                if contours_blue and contours_yellow:
                    contour_blue = contours_blue[0]
                    contour_yellow = contours_yellow[0]
                    (blueX, blueY), radiusB = cv2.minEnclosingCircle(contour_blue)
                    (yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contour_yellow)
                #(yellowX, yellowY), radiusY = cv2.minEnclosingCircle(contours_yellow)
                await base.move_straight(velocity=200, distance=50)
        await base.spin(velocity=100, angle=180)
