## Drive motors

| Position | Port | Reversed | Cartridge |
|---|---|---|---|
| Front left | 1 | True | Green 18:1 |
| Rear left | 2 | True | Green 18:1 |
| Front right | 3 | False | Green 18:1 |
| Rear right | 4 | False | Green 18:1 |

## Controller

| Input | Function |
|---|---|
| Left stick vertical (`axis3`) | Forward/reverse |
| Right stick horizontal (`axis1`) | Turning left and right |
| Up/down buttons | Maximum driving speed ±10%, range 20~100% |
| L2 / L1 | Lift raising / lowering |
| R1 / R2 | Claw opening / closing |
| Left/right buttons | Claw rotation up/down |

Starting maximum speed is 100%, the deadzone is 5 (does not respond below 5)
`PERCENT` is a motor speed command unit, it does not represent a power consumption ratio or an exact ground speed

## Lift·Claw settings

Adjust the following settings in `main.py` to match the actual mechanism

- `LIFT_PORT_1`, `LIFT_PORT_2`, `CLAW_PORT`, `WRIST_PORT`: Actual Smart Port. Default is `None`.
- Each `GEARS`, `REVERSED`: Actual cartridge and operating direction.
- Each `MAX_DEG`: Maximum travel angle of the motor shaft. Set with clearance from the mechanical end.
- Each `SPEED`, `TORQUE`: Speed and maximum torque suited to the mechanism.
- Each `ENABLED`: Set only fully configured mechanisms to `True`.

Each mechanism raises/opens/rotates upward in the positive direction, and its position value should also increase
The two lift motors are assumed to use the same direction setting with matching linkages and gear ratios, the current code does not automatically correct position differences between the two motors
