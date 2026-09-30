"""Native HPP regressions for manipulation timing."""

import numpy as np
import pytest
from pinocchio import SE3
from pyhpp.core import InterpolatedPath, Problem, StraightPath, interval
from pyhpp.core.path import Vector
from pyhpp.pinocchio import Device, urdf
from tools import Toppra


@pytest.fixture
def timing_problem():
    robot = Device("timing")
    urdf.loadModelFromString(
        robot,
        0,
        "arm",
        "anchor",
        """<robot name="timing">
          <link name="base"/><link name="tip"/>
          <joint name="joint" type="revolute">
            <parent link="base"/><child link="tip"/><axis xyz="0 0 1"/>
            <limit lower="-2" upper="2" velocity="1" effort="1"/>
          </joint>
        </robot>""",
        "",
        SE3.Identity(),
    )
    problem = Problem(robot)
    toppra = Toppra(problem)
    toppra.velocityScale = 0.5
    toppra.accelerationLimits = np.array([0.5])
    toppra.N = 100
    toppra.selectJoints(["arm/joint"])
    return robot, toppra


def test_stops_at_nested_boundaries_and_internal_interpolation_points(timing_problem):
    robot, toppra = timing_problem
    q0, q1 = np.array([0.0]), np.array([0.3])
    projected = InterpolatedPath(robot, q0, q0, interval(0.0, 2.0))
    projected.insert(0.75, q1)
    nested = Vector(1, 1)
    nested.appendPath(projected)
    path = Vector(1, 1)
    path.appendPath(StraightPath(robot, q0, q0, interval(0.0, 0.0), None))
    path.appendPath(StraightPath(robot, np.array([-0.2]), q0, interval(0.0, 0.2), None))
    path.appendPath(nested)

    timed = toppra.optimize(path)

    assert timed.numberPaths() == 3
    assert path.numberPaths() == 3
    assert len(path.pathAtRank(2).pathAtRank(0).interpolationPoints()) == 3
    for rank, (start, end) in enumerate([(-0.2, 0.0), (0.0, 0.3), (0.3, 0.0)]):
        leaf = timed.pathAtRank(rank)
        np.testing.assert_allclose(leaf(0.0)[0], [start], atol=1e-12)
        np.testing.assert_allclose(leaf(leaf.length())[0], [end], atol=1e-12)
        for t in [0.0, leaf.length()]:
            np.testing.assert_allclose(leaf.derivative(t, 1), [0.0], atol=1e-8)
        for t in np.linspace(0.0, leaf.length(), 101):
            assert np.abs(leaf.derivative(float(t), 1)).max() <= 0.5 + 1e-8
            assert np.abs(leaf.derivative(float(t), 2)).max() <= 0.5 + 1e-8


def test_rejects_portions_that_toppra_would_return_untimed(timing_problem):
    robot, toppra = timing_problem
    path = Vector(1, 1)
    path.appendPath(
        StraightPath(
            robot, np.array([0.0]), np.array([1e-7]), interval(0.0, 1e-7), None
        )
    )
    with pytest.raises(ValueError, match="too short"):
        toppra.optimize(path)
