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

## Path optimization

The path returned by the planner is collision-free but typically jagged, with unnecessary detours.
Before time-parameterizing, we should optimize the geometric path using shortcutting algorithms:

```python
from pyhpp.core import RandomShortcut

shortcut = RandomShortcut(problem)
p1_opt = shortcut.optimize(p1)
print(f"Optimized path length: {p1_opt.length():.3f} (was {p1.length():.3f})")
```

`RandomShortcut` repeatedly picks two random points along the path and tries to connect them with a
straight segment. If the shortcut is collision-free and shorter, it replaces the original sub-path.

## Time parameterization
### SimpleTimeParameterization

`SimpleTimeParameterization` computes a polynomial time parameterization that maps real time `t` to
the path parameter `s`, while respecting joint velocity and acceleration limits.

```python
from pyhpp.core import SimpleTimeParameterization

stp = SimpleTimeParameterization(problem)
stp.order = 2
stp.safety = 0.95
stp.maxAcceleration = 0.5
p1_stp = stp.optimize(p1_opt)
```

After optimization, `p1_stp.length()` returns the total execution time in seconds:
```python
print(f"Optimized path length: {p1_opt.length():.3f}")
print(f"STP duration: {p1_stp.length():.3f} s")
```

The parameters control the time parameterization:
- `order`: polynomial continuity order. `0` = linear (C0), `1` = cubic (C1, zero velocity at
  endpoints), `2` = quintic (C2, zero velocity and acceleration at endpoints).
- `safety`: scaling factor for velocity limits (0.95 = use 95% of max velocity).
- `maxAcceleration`: maximum acceleration per DOF in rad/s². Only used when `order >= 2`. Set to a
  negative value to disable. **Use a small value** (e.g. 0.5) to produce slower, more visible
  motions — this makes the difference between the raw path `p1` and the parameterized trajectory
  `p1_stp` easier to observe.

Try different values to see the effect on execution time:
```python
for acc in [0.25, 0.5, 1.0, 2.0]:
    stp.maxAcceleration = acc
    p = stp.optimize(p1_opt)
    print(f"  maxAcceleration={acc:.2f} -> duration={p.length():.3f} s")
```

## TOPPRA

TOPPRA (Time-Optimal Path Parameterization based on Reachability Analysis) computes the
time-optimal parameterization subject to velocity and torque constraints. Unlike
`SimpleTimeParameterization`, it accounts for the robot's dynamics.

```python
from pyhpp_toppra import Toppra

toppra = Toppra(problem)
toppra.velocityScale = 0.5
toppra.effortScale = -1
toppra.N = 100
p1_toppra = toppra.optimize(p1_opt)
```

Compare the results:
```python
print(f"TOPPRA duration: {p1_toppra.length():.3f} s")
```

TOPPRA typically produces shorter execution times than `SimpleTimeParameterization` because it
computes the time-optimal solution rather than a conservative polynomial approximation.

The parameters are:
- `velocityScale`: scaling factor for velocity limits (1.0 = full velocity). Use a small value
  (e.g. 0.5) for slower, more visible motions.
- `effortScale`: scaling factor for torque limits. Set to a negative value to disable torque
  constraints. **Note**: torque constraints require mass and inertia data in the robot URDF. The
  current Staubli model has no dynamics data, so `effortScale` must be set to `-1` (disabled).
- `N`: minimal number of discretization points along the path.
- `interpolationMethod`: `"constant_acceleration"` or `"hermite"`.
- `gridpointMethod`: `"param_space"` or `"time_space"`.

## Visualization

You can visualize the path in the viewer:
```python
v = display()
v.loadPath(p1_stp)
```
