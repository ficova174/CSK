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
redLEDXYZ = [x(lambda), y(lambda), z(lambda)] # trouver lambda puis données expérimentales
greenLEDXYZ = [x(lambda), y(lambda), z(lambda)] # trouver lambda puis données expérimentales
blueLEDXYZ = [x(lambda), y(lambda), z(lambda)] # trouver lambda puis données expérimentales

def XYZ_to_uv(XYZ:list) -> list:
    denominateur = XYZ[0] + 15*XYZ[1] + 3*XYZ[2]
    return [4*XYZ[0]/denominateur, 9*XYZ[1]/denominateur]

def uv_to_XYZ(uv:list) -> list:
    denominateur = 6*uv[0] - 16*uv[1] + 12
    return [9*uv[0]/denominateur, 4*uv[]]


# Plotting the *CIE 1976 Chromaticity Diagram*.
# The argument *show=False* is passed so that the plot doesn't get
# displayed and can be used as a basis for other plots.
plot_chromaticity_diagram_CIE1976UCS(show=False)

# Plotting the *uv* chromaticity coordinates.
redLEDUV = XYZ_to_uv(redLEDXYZ)
greenLEDUV = XYZ_to_uv(greenLEDXYZ)
blueLEDUV = XYZ_to_uv(blueLEDXYZ)
plt.plot(redLEDUV[0], redLEDUV[1], 'o-', color='black')
plt.plot(greenLEDUV[0], greenLEDUV[1], 'o-', color='black')
plt.plot(blueLEDUV[0], blueLEDUV[1], 'o-', color='black')

# Annotating the plot --> plt.annotate()

# Displaying the plot.
render(
    show=True,
    limits=(-0.1, 0.9, -0.1, 0.9),
    x_tighten=True,
    y_tighten=True)