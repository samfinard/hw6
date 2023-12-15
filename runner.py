import cv2
import asyncio
from game import GameState, display_frame
from robot import defend_rotate, defend_forward
from viam.robot.client import RobotClient
from viam.components.base import Base
from viam.components.motor import Motor
from viam.rpc.dial import Credentials, DialOptions
import shared_vars


async def connect():
    creds = Credentials(
        type="robot-location-secret",
        payload="ueg84ir6sdbxw388tcqz3ycupdzfrlicmgt1h7aev467sh7w")
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address("samgubb2-main.wm4vlppvex.viam.cloud", opts)

async def main():
    video_feed = cv2.VideoCapture(0)
    
    # Game state and robot setup
    # To change difficulty of game, change these 4 variables
    left_zone, right_zone = 0.3, 0.7
    maxScore, maxTime = 5, 120000

    game_state = GameState(left_zone, right_zone, maxScore, maxTime)
    
    # Connect to the robot
    robot = await connect()  
    base = Base.from_robot(robot, "viam_base")
    left_motor = Motor.from_robot(robot, "left")
    right_motor = Motor.from_robot(robot, "right")

    while shared_vars.points < 5:
        # Robot defense logic here, running in the main async loop
        ret, frame = video_feed.read()
        await defend_rotate(frame, left_motor, right_motor)
        await defend_forward(video_feed, base, shared_vars.home)

    video_feed.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    asyncio.run(main())
