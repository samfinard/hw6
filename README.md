# The Setup
RC Car Used: Amazon.com: Force1 Tornado LED Remote Control Car for Kids - Double Sided Fast RC Car, 4WD Off-Road Stunt Car 360 Flips, All Terrain Tires, LEDs, Rechargeable Toy Car Battery, 2.4 GHz Remote, Interactive Display

iPhone Casting Software: Iriun Webcam

# Original Objective:
Two players: 
RC car (human controlled) 
Rover (computer controlled)

RC Car Goal: Score x points within t seconds without getting hit 

Rover Goal: Hit the RC car once OR prevent from scoring x points in t seconds

RC Car Behavior (human): - Go to target zone without being hit - wait until Rover resets before going to new target zone

Rover Behavior (computer): - Let x_t be the x coordinate of the current target zone. - Go to x_t and mirror the y coordinate of the RC car, trying to block it. - If distance from RC and Rover is small enough, just attack it - If RC car successfully gets a point, reset by going to new target x coordinate

# Pitfalls:
Due to multiprocessing issues, we are unable to control the rover and display the video at the same time. We are also unable to update points while the rover is being controlled. Therefore, we chose to annotate the raw footage to give you a better sense of the game.

# Updated Objective:
Two players:
RC car (human controlled)
Rover (computer controlled)

RC Car Goal: Score x points within t seconds without getting hit
Rover Goal: Hit the RC car once OR prevent RC car from scoring enough points

RC Car Behavior: The RC car will start at the opposite end of the arena to the robot. The RC car needs to navigate around the robot without being hit. If the RC car passes the robot, you need to wait until the Rover finds its position at the opposite end of the arena. This works better than target zones because our multiprocessing issues made it impossible to update the score based on the virtual goal lines and also made it impossible to tell the robot to return home while it is actively trying to block the RC car. Since the blocking behavior now relies on the relative position of the RC car, the Rover can determine when the RC car has passed it in any direction, and can use that as a trigger for increasing points and returning to its position on the other side of the arena.

Rover Behavior:
The rover starts at the opposite end of the arena to the RC car. Depending on whether the RC car is coming from a higher or lower Y value, the rover moves backwards in an arc in that direction to try to block it. Once the rover is perpendicular to its starting position (aligned with Y axis), it mirrors the RC car’s Y movements to block it from passing its X position by moving forward and backwards. If the RC car “hits” the rover, the rover wins and the game is over. If the RC car successfully passes the rover, the rover will find and return to the starting point at the other end of the arena and repeat its behavior. If the RC car can repeat this cycle and gain a certain number of points without being hit, the RC car wins.
