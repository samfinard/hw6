# hw6

### Two players: 
	RC car (human controlled)
	Rover (computer controlled)

RC Car Goal: Score x points within t seconds without getting hit
Rover Goal: Hit the RC car once OR prevent from scoring x points in t seconds

Difficulties: 
easy (large playing field, large L/R zone size)
hard (small playing field, small L/R zone size)

RC Car Behavior (human):
	- Go to target zone without being hit
		- wait until Rover resets before going to new target zone

Rover Behavior (computer):
	- Let x_t be the x coordinate of the current target zone.
	- Go to x_t and mirror the y coordinate of the RC car, trying to block it.
		- If distance from RC and Rover is small enough, just attack it
	- If RC car successfully gets a point, reset by going to new target x coordinate
