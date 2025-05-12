#!/home/ficova/TIPE/CSK/.venv/bin/python

import colour
from colour.plotting import *
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Qt5Agg")


# Computing *xy* chromaticity coordinates for the *neutral 5 (.70 D)* patch.
# xy =  colour.XYZ_to_xy(XYZ)
xy = [0.31259787, 0.32870029]
print(xy)

# Plotting the *CIE 1931 Chromaticity Diagram*.
# The argument *show=False* is passed so that the plot doesn't get
# displayed and can be used as a basis for other plots.
plot_chromaticity_diagram_CIE1931(show=False)

# Plotting the *xy* chromaticity coordinates.
x, y = xy
plt.plot(x, y, 'o-', color='black')

# Annotating the plot.
"""
plt.annotate(patch_sd.name.title(),
             xy=xy,
             xytext=(-50, 30),
             textcoords='offset points',
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3, rad=-0.2'))
"""

# Displaying the plot.
render(
    show=True,
    limits=(-0.1, 0.9, -0.1, 0.9),
    x_tighten=True,
    y_tighten=True)