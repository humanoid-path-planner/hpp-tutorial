"""Time-parameterize manipulation paths with stops at geometric junctions."""

from itertools import pairwise

from pyhpp.core import InterpolatedPath, Straight
from pyhpp.core.path import Vector
from pyhpp.manipulation import SplineGradientBased_bezier3
from pyhpp_toppra import Toppra as _Toppra


class Toppra(_Toppra):
    """Time-parameterize paths with stops at geometric junctions."""

    def optimize(self, path):
        """Preserve graph constraints and stop at each interpolation point."""
        flat = Vector(path.outputSize(), path.outputDerivativeSize())
        path.flatten(flat)
        timed = Vector(path.outputSize(), path.outputDerivativeSize())
        for rank in range(flat.numberPaths()):
            leaf = flat.pathAtRank(rank)
            if isinstance(leaf, InterpolatedPath):
                params = [t for t, _ in leaf.interpolationPoints()]
            else:
                params = [leaf.timeRange().first, leaf.timeRange().second]
            for start, end in pairwise(params):
                if end - start <= 1e-9:
                    continue
                if end - start < 1e-6:
                    raise ValueError("Path portion is too short for TOPPRA timing")
                portion = Vector(path.outputSize(), path.outputDerivativeSize())
                portion.appendPath(leaf.extract(start, end))
                timed.concatenate(super().optimize(portion))
        return timed


class SplineToppra(_Toppra):
    """Smooth transitions, join them within manipulation states, then time."""

    def __init__(self, problem, graph):
        super().__init__(problem)
        self.straight = Straight(problem)
        self.graph = graph
        self.singleSplineTransitions = ()
        self.spline = SplineGradientBased_bezier3(problem)
        # Penalize changes of tangent before applying acceleration-limited timing.
        self.spline.costOrder = 2
        self.spline.maxIterations(100)

    def optimize(self, path):
        flat = Vector(path.outputSize(), path.outputDerivativeSize())
        path.flatten(flat)
        groups = []
        previous = None
        cursor = 0.0
        for rank in range(flat.numberPaths()):
            leaf = flat.pathAtRank(rank)
            start, cursor = cursor, cursor + leaf.length()
            if cursor - start <= 1e-9:
                continue
            name = self.graph.transitionAtParam(path, (start + cursor) / 2).name()
            if name != previous:
                groups.append(Vector(path.outputSize(), path.outputDerivativeSize()))
                previous = name
            if isinstance(leaf, InterpolatedPath):
                params = [t for t, _ in leaf.interpolationPoints()]
            else:
                params = [leaf.timeRange().first, leaf.timeRange().second]
            for a, b in pairwise(params):
                if b - a > 1e-9:
                    groups[-1].appendPath(leaf.extract(a, b))

        states = []
        previous = None
        for group in groups:
            if group.length() < 1e-6:
                raise ValueError("Path transition is too short for TOPPRA timing")
            transition = self.graph.transitionAtParam(group, group.length() / 2)
            if transition.name() in self.singleSplineTransitions:
                # Fit constrained insertions with one spline between their endpoints.
                self.straight.constraints(group.pathAtRank(0).constraints())
                insertion = self.straight(group.initial(), group.end())
                group = Vector(path.outputSize(), path.outputDerivativeSize())
                group.appendPath(insertion)
            state = str(self.graph.getContainingNode(transition))
            if state != previous:
                states.append(Vector(path.outputSize(), path.outputDerivativeSize()))
                previous = state
            states[-1].concatenate(self.spline.optimize(group))

        timed = Vector(path.outputSize(), path.outputDerivativeSize())
        for group in states:
            timed.concatenate(super().optimize(self.spline.optimize(group)))
        return timed
