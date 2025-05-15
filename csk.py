#!/home/ficova/TIPE/CSK/.venv/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from colour.plotting import *

matplotlib.use("Qt5Agg")

# Création du diagramme et affichage des points (gamut)

def creationDiagrammeCIE1931(listePositions:list):
    # Plotting the *CIE 1931 Chromaticity Diagram*.
    # The argument *show=False* is passed so that the plot doesn't get
    # displayed and can be used as a basis for other plots.
    plot_chromaticity_diagram_CIE1931(show=False)

    # Plotting  chromaticity coordinates.
    for point in range(len(listePositions)):
        plt.plot(listePositions[point][0], listePositions[point][1], 'o-', color='black')

    # Displaying the plot.
    render(
        show=True,
        limits=(-0.1, 0.9, -0.1, 0.9),
        x_tighten=True,
        y_tighten=True)

# Partie émission

def codageBinaire(nombre:int, taillePaquet:int) -> str:
    """
    nombre décimal -> nombre en binaire
    attention on code de gauche à droite (petites puissances à gauche)
    """
    nombreBin = ''
    while nombre > 0:
        nombreBin += str(nombre % 2)
        nombre //= 2
    while len(nombreBin) < taillePaquet: # on veut une taille fixe, on ajoute des 0
        nombreBin += '0'
    return nombreBin

def encodage(message:str, taillePaquet:int) -> str:
    """
    message texte (str) -> message en binaire (str)
    on demande la taille des paquets car on utilisera cette fonction pour coder des strings de longueur variable (accroche et ID)
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre, taillePaquet)
    return messageBin

def creationAccroche(lettre:str) -> str:
    """
    on créée une succesion improbable
    on lui donne un identifiant pour estimer le début du message (fonction detectionAccroche())
    """
    accroche = ''
    for k in range(8): # car 8 valeurs possibles de id
        id = codageBinaire(k, 3) # id codé sur 3 bits (8 valeurs possibles)
        accroche += encodage(lettre, 8) + id # accroche est répétée et possède un identifiant unique
    return accroche

# Codage Manchester (IEEE 802.3)
def codageManchester(messageBin:str) -> str:
    """
    pour synchroniser l'émetteur et le récepteur (savoir combien de 0 ou de 1 on reçoit d'affilé) on utilise le codage Manchester
    le message codé est synchrone, il contient l'horloge en lui en plus du message
    pour chaque bit du message, l'horloge fait une transition (donc deux valeurs)
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    horloge = [k%2 for k in range(1, 2*len(messageBin)+1)] # On commence à 1 pour que l'horloge commence par 1
    messageMan = ""
    for indiceBit in range(len(messageBin)):
        for indiceHorloge in range(2*indiceBit, 2*(indiceBit+1)):
            if int(messageBin[indiceBit]) != horloge[indiceHorloge]:
                messageMan += "1"
            else:
                messageMan += "0"
    return messageMan

def positionsDiagramme(messageMan:str, pointsDiag:dict) -> list:
    """
    pointDiag["00"] = np.array([[x], [y]]) red
    pointDiag["01"] = np.array([[x], [y]])
    ...
    pointDiag["11"] = np.array([[x], [y]]) blue
    """
    messageChromacity = np.zeros((2, len(messageMan)/2))
    indice = 0
    for k in range(0, len(messageMan)-2, 2):
        chromacity = pointsDiag[messageMan[k:k+2]]
        if chromacity >= 0 and chromacity <= 4:
            messageChromacity[:, indice] = chromacity
        else:
            print("couleur incorrecte")
        indice += 1
    if len(messageChromacity) == (len(messageMan)/2):
        return messageChromacity
    else:
        print("len(messageChromacity) != (len(messageMan)/2)")

def xyY_to_XYZ(xy:list, Y:list):
    x = xy[0]
    y = xy[1]
    return [Y*x/y, Y, (1-x-y)*Y/y]

def XYZ_to_RGB(): # RGB = voltage entre 0 et 10 V

def csk(messageMan:str, tensionMin:int, tensionMax:int, N:int) -> list:
    """
    transforme le message en chromacité en valeurs de tension pour les LEDS
    on utilise la modulation colors shifting keying (CSK)
    """
    tension = np.zeros((2, len(messageMan)/2))
    for bit in messageMan:
        if bit == '0':
            tension += [tensionMin]*N
        elif bit == '1':
            tension += [tensionMax]*N
        else:
            print('Erreur : le message binaire est corrompu, une valeur autre que 0 et 1 a été trouver')
            return []
    return np.array(tension, dtype=np.float32)

def emission(message:str, tensionMin:int, tensionMax:int, N:int, startMan:str, endMan:str) -> list:
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan # accroches ajoutées au message
    messageChromacity = positionsDiagramme(messageMan, pointsDiag)
    return csk(messageChromacity, tensionMin, tensionMax, N)


# Partie réception
# ATTENTION le message sera à l'envers car les infos envoyées en premières seront reçues en première