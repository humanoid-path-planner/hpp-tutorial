# How to optimize and time-parameterize paths.

## Prerequisite

Having completed [tutorial 4](../tutorial_4/README.md)

## Initializing the problem

In the docker container, cd into `tutorial_5` directory. In a bash terminal, run

```
python -i init.py
```

The script contains the code of [tutorial 4](../tutorial_4/README.md) with an additional obstacle
placed between the robot and the plate. This forces the planner to find a non-straight path for `p1`
(the motion from `q_init` to the pregrasp configuration `qpg`).

The path `p1` uses a dimensionless path parameter `s` ranging from `0` to `p1.length()`. This
parameter does not correspond to real time: the robot has no notion of velocity or acceleration
along this path.

## SimpleTimeParameterization

`SimpleTimeParameterization` computes a polynomial time parameterization that maps real time `t` to
the path parameter `s`, while respecting joint velocity and acceleration limits.

```
from pyhpp.core import SimpleTimeParameterization

stp = SimpleTimeParameterization(problem)
stp.order = 2
stp.safety = 0.95
stp.maxAcceleration = 1.0
p1_stp = stp.optimize(p1)
```

After optimization, `p1_stp.length()` returns the total execution time in seconds:
```
print(f"Original path parameter range: {p1.length():.3f}")
print(f"STP duration: {p1_stp.length():.3f} s")
```

The parameters control the time parameterization:
- `order`: polynomial continuity order. `0` = linear (C0), `1` = cubic (C1, zero velocity at
  endpoints), `2` = quintic (C2, zero velocity and acceleration at endpoints).
- `safety`: scaling factor for velocity limits (0.95 = use 95% of max velocity).
- `maxAcceleration`: maximum acceleration per DOF. Only used when `order >= 2`. Set to a negative
  value to disable.

## TOPPRA

TOPPRA (Time-Optimal Path Parameterization based on Reachability Analysis) computes the
time-optimal parameterization subject to velocity and torque constraints. Unlike
`SimpleTimeParameterization`, it accounts for the robot's dynamics.

```
from pyhpp_toppra import Toppra

toppra = Toppra(problem)
toppra.velocityScale = 1.0
toppra.N = 100
p1_toppra = toppra.optimize(p1)
```

Compare the results:
```
print(f"TOPPRA duration: {p1_toppra.length():.3f} s")
```

TOPPRA typically produces shorter execution times than `SimpleTimeParameterization` because it
computes the time-optimal solution rather than a conservative polynomial approximation.

The parameters are:
- `velocityScale`: scaling factor for velocity limits (1.0 = full velocity).
- `effortScale`: scaling factor for torque limits. Set to a negative value to disable torque
  constraints.
- `N`: minimal number of discretization points along the path.
- `interpolationMethod`: `"constant_acceleration"` or `"hermite"`.
- `gridpointMethod`: `"param_space"` or `"time_space"`.

## Visualization

You can visualize the path in the viewer:
```
v = display()
v.loadPath(p1_toppra)
```
