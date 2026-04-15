import matplotlib.pyplot as plt
import numpy as np


# Plot a trajectory with respect to times
#
#  \param p pyhpp.core.Path instance
#  \param rmin, rmax: range of the path to be plot. For example passing rmin=0, rmax=6 will
#                     plot the 6 first coordinates of the path,
#  \param dt: time step,
#  \param order: 0 for configuration, 1 for configuration and velocity, 2 for configuration
#                velocity and acceleration
def plotTraj(p, rmin, rmax, dt=0.01, order=2):
    times = dt * np.arange(int(p.length() / dt))
    fig = plt.figure(layout="constrained")
    gs = fig.add_gridspec(order + 1, 1)
    values = np.array([p.eval(t)[0] for t in times])
    ax0 = fig.add_subplot(gs[0, 0])
    if order >= 1:
        velocities = np.array([p.derivative(t, 1) for t in times])
        ax1 = fig.add_subplot(gs[1, 0])
    if order >= 2:
        accelerations = np.array([p.derivative(t, 2) for t in times])
        ax2 = fig.add_subplot(gs[2, 0])
    for i in range(rmin, rmax):
        ax0.plot(times, values[:, i], label=f"q{i}")
        if order >= 1:
            ax1.plot(times, velocities[:, i], label=f"q{i}")
        if order >= 2:
            ax2.plot(times, accelerations[:, i], label=f"q{i}")
    fig.show()
