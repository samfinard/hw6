# The Setup
**RC Car Used:** Amazon.com: Force1 Tornado LED Remote Control Car for Kids - Double Sided Fast RC Car, 4WD Off-Road Stunt Car 360 Flips, All Terrain Tires, LEDs, Rechargeable Toy Car Battery, 2.4 GHz Remote, Interactive Display

**iPhone Casting Software:** Iriun Webcam

# Updated Objective:
Two players:

RC Car (human controlled)

Rover (computer controlled)

RC Car Goal: Get on the other side of the rover without being hit by the rover.

Rover Goal: Hit the RC car.

The rover mirrors the y-coordinate of the RC car, trying to block it from going to the other side.

# Pitfalls:
Due to multiprocessing issues, we were unable to control the rover and display the iPhone video at the same time. 

# Initial Objective
We wanted that when the RC car goes to the left of the rover, 1 point gets added and the rover resets on the other side. However, due to multiprocessing issues we were unable to simultaneously update the score and control the robot - thus, we chose to implement a slightly different game. 

points_RCCAR.mov shows our attempts at this initial objective. However, our final game is main.mp4.

**It should also be noted that points_RCCAR.py is unrelated to main.py.**
