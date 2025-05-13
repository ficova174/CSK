#!/home/ficova/TIPE/CSK/.venv/bin/python

from colour.plotting import *
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Qt5Agg")

# Computing *uv* chromaticity coordinates for the *neutral 5 (.70 D)* patch.
# uv =  colour.uvZ_to_uv(XYZ)
uv = [0.31259787, 0.32870029]


# (X, Y, Z) = (k*x(lambda), k*y(lambda), k*z(lambda))  (found in CIE dataset) (au pire on le )
# Let's assume that k = 1 as CIE 1976 is k-independant (k cancels out in u and v formula), it only has an effect on brightness
redLEDXYZ = [1.5, 1.5] # trouver lambda puis données expérimentales


# Plotting the *CIE 1976 Chromaticity Diagram*.
# The argument *show=False* is passed so that the plot doesn't get
# displayed and can be used as a basis for other plots.
plot_chromaticity_diagram_CIE1931(show=False)

# Plotting the *uv* chromaticity coordinates.
plt.plot(redLEDXYZ[0], redLEDXYZ[1], 'o-', color='black')

# Annotating the plot --> plt.annotate()

# Displaying the plot.
render(
    show=True,
    limits=(-0.1, 0.9, -0.1, 0.9),
    x_tighten=True,
    y_tighten=True)