from vex import *

brain = Brain()
controller = Controller(PRIMARY)

# Based on the verified directions the left side is reversed, the right side uses the default direction
# Using green cartridges so the gear ratio is set to 18:1
left_front = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True)
left_rear = Motor(Ports.PORT3, GearSetting.RATIO_18_1, True)
right_front = Motor(Ports.PORT2, GearSetting.RATIO_18_1, False)
right_rear = Motor(Ports.PORT4, GearSetting.RATIO_18_1, False)
drive_motors = [left_front, left_rear, right_front, right_rear]
for motor in drive_motors:
    motor.set_stopping(BRAKE)

# Ignore small inputs when the stick is released to prevent unintended movement.
DEADZONE = 5
# Maximum speed is fixed at 100%
speed_limit = 100

# Claw on port 5, left lift pulley on port 6, right lift pulley on port 7
# No separate motor has been assigned for claw rotation yet
LIFT_PORT_1 = Ports.PORT6
LIFT_PORT_2 = Ports.PORT7
CLAW_PORT = Ports.PORT5
WRIST_PORT = None

# Keep the pulley directions confirmed during measurement
# For both motors REVERSE raises the lift and decreases the angle
LIFT_LEFT_REVERSED = False
LIFT_RIGHT_REVERSED = True
# The claw also opens with REVERSE, and closes with FORWARD
CLAW_REVERSED = False
WRIST_REVERSED = False

# Additional motors are initially assumed to use green cartridges so change this if the actual cartridges differ
LIFT_GEARS = GearSetting.RATIO_36_1
CLAW_GEARS = GearSetting.RATIO_18_1 ########################### !!Uncertain so needs checking!! #################################
WRIST_GEARS = GearSetting.RATIO_18_1

# At the lower lift reference position press A to register both motors at 0
# For the claw press X at the physical position that measured -59 degrees to register the reference ########################## Needs measurement and review again ################################
LIFT_LOWER_LIMIT = 0
LIFT_UPPER_LIMIT = -2200
# Block control of both pulleys until A is pressed
lift_ready = False
CLAW_CLOSED_LIMIT = -59
CLAW_OPEN_LIMIT = -388
# The claw position is unknown at startup, so block control until the reference is confirmed with X
claw_ready = False
WRIST_MAX_DEG = None

# Set to True only for mechanisms with verified ports, directions, travel ranges and starting positions
LIFT_ENABLED = True
CLAW_ENABLED = True
WRIST_ENABLED = False

# The lift uses the speed/torque setting of 100% that the user confirmed could raise it
# Stopping may be delayed at the end so the -2600 degree limit needs verification on the actual mechanism
LIFT_SPEED = 100
CLAW_SPEED = 40
WRIST_SPEED = 15

# Torque limit to reduce excessive force when blocked
# These values are not guaranteed to be safe for the gears so verify them for the mechanism
LIFT_TORQUE = 100
CLAW_TORQUE = 15
WRIST_TORQUE = 20


def apply_deadzone(value):
    # abs gives the magnitude without the sign so small forward and reverse inputs are filtered together
    return 0 if abs(value) < DEADZONE else value


def command_motor(motor, speed):
    # Use stop when the value is 0 to stop with the configured BRAKE/HOLD mode
    if speed == 0:
        motor.stop()
    else:
        motor.spin(FORWARD, speed, PERCENT)


def create_motors(ports, gears, reversed_direction, torque, stopping):
    # Return an empty list so driving remains available even with unconfigured mechanisms
    if any(port is None for port in ports):
        return []
    motors = []
    for port in ports:
        motor = Motor(port, gears, reversed_direction)
        motor.set_max_torque(torque, PERCENT)
        motor.set_stopping(stopping)
        motors.append(motor)
    return motors


# The lift and rotation axis apply force to maintain their current positions when the buttons are released
# Even HOLD cannot support the load without power so mechanical support is needed
lift_left = Motor(LIFT_PORT_1, LIFT_GEARS, LIFT_LEFT_REVERSED)
lift_right = Motor(LIFT_PORT_2, LIFT_GEARS, LIFT_RIGHT_REVERSED)
lift_motors = [lift_left, lift_right]
for motor in lift_motors:
    motor.set_max_torque(LIFT_TORQUE, PERCENT)
    motor.set_stopping(HOLD)
# The claw uses BRAKE for now but its ability to keep gripping an object is uncertain so #################################### Needs review ##########################################
claw_motors = create_motors(
    [CLAW_PORT], CLAW_GEARS, CLAW_REVERSED, CLAW_TORQUE, BRAKE
)
wrist_motors = create_motors(
    [WRIST_PORT], WRIST_GEARS, WRIST_REVERSED, WRIST_TORQUE, HOLD
)


def set_reference(motors, enabled, maximum):
    # Only records the current position as 0, does not move to find the physical home position
    # Place the mechanism at the designated reference position each time the program runs
    if enabled and maximum is not None and maximum > 0:
        for motor in motors:
            motor.set_position(0, DEGREES)


# The lift and claw do not automatically zero their starting positions
# Confirm the physical reference positions and register them with A and X respectively
set_reference(wrist_motors, WRIST_ENABLED, WRIST_MAX_DEG)


def control_limited(motors, enabled, maximum,
                    positive_button, negative_button, speed):
    if not motors:
        return
    if not enabled or maximum is None or maximum <= 0:
        for motor in motors:
            motor.stop()
        return

    # Stop when both buttons are pressed or both are released
    if positive_button == negative_button:
        output = 0
    elif positive_button:
        # With two motors such as the lift stop both when either reaches the upper limit
        at_limit = any(m.position(DEGREES) >= maximum for m in motors)
        output = 0 if at_limit else speed
    else:
        # The lower limit is 0 degrees and returning in the opposite direction is allowed even at a limit
        at_limit = any(m.position(DEGREES) <= 0 for m in motors)
        output = 0 if at_limit else -speed
    for motor in motors:
        command_motor(motor, output)


def show_speed():
    controller.screen.clear_row(1)
    controller.screen.set_cursor(1, 1)
    controller.screen.print("Speed:", speed_limit, "%")

    controller.screen.clear_row(2)
    controller.screen.set_cursor(2, 1)
    controller.screen.print("Lift: READY" if lift_ready else "Lift: press A")

    controller.screen.clear_row(3)
    controller.screen.set_cursor(3, 1)
    controller.screen.print("Claw: READY" if claw_ready else "Claw: press X")


def confirm_lift_reference():
    global lift_ready

    # Register only once per run to prevent accidental registration again after moving
    if lift_ready or not LIFT_ENABLED:
        return
    if controller.buttonL1.pressing() or controller.buttonL2.pressing():
        return

    # Place it at the same physical lower position used when pressing A during measurement and register
    # Does not lower automatically, records the current position as 0 degrees
    for motor in lift_motors:
        motor.stop()
        motor.set_position(LIFT_LOWER_LIMIT, DEGREES)
    lift_ready = True
    show_speed()


def control_lift():
    if not LIFT_ENABLED or not lift_ready:
        for motor in lift_motors:
            motor.stop()
        return

    up = controller.buttonL1.pressing()
    down = controller.buttonL2.pressing()
    output = 0

    if up and not down:
        # Both angles decrease while raising
        # Stop both if either reaches -2600 degrees to avoid tilting the mechanism
        if all(m.position(DEGREES) > LIFT_UPPER_LIMIT for m in lift_motors):
            output = -LIFT_SPEED
    elif down and not up:
        # Angles increase while lowering and both stop if either reaches 0 degrees
        if all(m.position(DEGREES) < LIFT_LOWER_LIMIT for m in lift_motors):
            output = LIFT_SPEED

    # Releasing both buttons or pressing both sets output to 0 and stops with HOLD
    # This limits the end positions, it does not automatically synchronize the heights of both sides
    for motor in lift_motors:
        command_motor(motor, output)

def confirm_claw_reference():
    global claw_ready

    # Once registered the reference cannot be registered again until the program restarts
    # Prevent accidental presses of X from changing the reference while the claw is open
    if claw_ready or not CLAW_ENABLED or not claw_motors:
        return
    
    # Prevent changes to the reference position while the claw is being moved
    if controller.buttonR1.pressing() or controller.buttonR2.pressing():
        return

    for motor in claw_motors:
        motor.stop()

        # Place the claw at the physical position that measured -59 degrees and press X ########################### Needs updating(only update the comment since the code only requires changing the variable) ##############################
        # X labels the current position and does not close the claw automatically
        motor.set_position(CLAW_CLOSED_LIMIT, DEGREES)

    claw_ready = True
    show_speed()


def control_claw():
    if not claw_motors:
        return

    # Block claw control until the reference position is registered with X
    if not CLAW_ENABLED or not claw_ready:
        for motor in claw_motors:
            motor.stop()
        return

    opening = controller.buttonR1.pressing()
    closing = controller.buttonR2.pressing()

    for motor in claw_motors:
        position = motor.position(DEGREES)

        # Stop when both are pressed or both are released
        if opening == closing:
            motor.stop()

        elif opening:
            # The angle decreases as the claw opens
            # Stop opening further when -388 degrees is reached ########################### Needs updating(only update the comment since the code only requires changing the variable) ##############################
            if position > CLAW_OPEN_LIMIT:
                motor.spin(REVERSE, CLAW_SPEED, PERCENT)
            else:
                motor.stop()

        elif closing:
            # The angle increases as it closes
            # Stop closing further when -59 degrees is reached ########################### Needs updating(only update the comment since the code only requires changing the variable) ##############################
            if position < CLAW_CLOSED_LIMIT:
                motor.spin(FORWARD, CLAW_SPEED, PERCENT)
            else:
                motor.stop()


# Each time the program starts register the pulley reference with A, and the claw reference with X
controller.buttonA.pressed(confirm_lift_reference)
controller.buttonX.pressed(confirm_claw_reference)

# Maximum speed is fixed so the up/down buttons are not assigned speed adjustment
show_speed()

while True:
    # Left stick vertical: forward/reverse, right stick horizontal: turning
    forward = apply_deadzone(controller.axis3.position())
    turn = apply_deadzone(controller.axis1.position())
    left_speed = forward + turn
    right_speed = forward - turn

    # Adding forward and turning inputs can exceed 100 so scale both sides down by the same ratio
    # Apply the maximum speed at the end so turning also stays within the setting
    largest = max(abs(left_speed), abs(right_speed), 100)
    left_speed = left_speed / largest * speed_limit
    right_speed = right_speed / largest * speed_limit
    command_motor(left_front, left_speed)
    command_motor(left_rear, left_speed)
    command_motor(right_front, right_speed)
    command_motor(right_rear, right_speed)

    # L2 raises / L1 lowers. Release the button to stop
    control_lift()
    
    
    # The claw angle decreases when opening so use a dedicated limit function
    control_claw()
    
    # Left directional button: up / right directional button: down
    control_limited(
       wrist_motors, WRIST_ENABLED, WRIST_MAX_DEG,
        controller.buttonLeft.pressing(),
        controller.buttonRight.pressing(),
        WRIST_SPEED
    )
    wait(20, MSEC)
