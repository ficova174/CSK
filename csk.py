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

def creationCodagePoints(primariesColorsxy:dict, nombreSubdivisions:int):
    """
    on pose 2 couleurs primaires sur le diagramme puis on met des points équidistants sur la droite les rejoignant
    x = (G*primary_green_x + B*primary_blue_x)/(G + B)
    y = (G*primary_green_y + B*primary_blue_y)/(G + B)
    c'est linéaire
    G, B entre 0.0 et 1.0
    primariesColorsxy["red"] = [x,
                                y]
    np array
    
    ointDiag["00"] = np.array([[x], [y]]) red
    pointDiag["01"] = np.array([[x], [y]])
    ...
    pointDiag["11"] = np.array([[x], [y]]) blue
    """
    distanceCouleursPrimaires = primariesColorsxy["red"]-primariesColorsxy["blue"]
    listePointsxy = np.zeros((2, nombreSubdivisions))
    listePointsxy[:, 0] = primariesColorsxy["blue"]
    listePointsxy[:, nombreSubdivisions] = primariesColorsxy["red"]
    for point in range(1, nombreSubdivisions-1):
        listePointsxy[:, point] = primariesColorsxy["blue"] + point*distanceCouleursPrimaires
    
    pointsDiagramme = {}
    for valeur in range(nombreSubdivisions):
        pointsDiagramme[codageBinaire(valeur, 2)] = listePointsxy # codage binaire à l'envers = problème ?

    return np.round(pointsDiagramme, 2)

def positionsDiagramme(messageMan:str, pointsDiagramme:dict) -> list:
    """
    """
    messagexy = np.zeros((2, len(messageMan)/2))
    indice = 0
    for k in range(0, len(messageMan)-2, 2):
        chromacity = pointsDiagramme[messageMan[k:k+2]]
        messagexy[:, indice] = chromacity
        indice += 1
    if messagexy.shape[1] == len(messageMan)/2:
        return messagexy
    print("messageChromacity.shape[1] == len(messageMan)/2")

def xyY_to_XYZ(messagexy:list, Y:int): # Y représente la luminance, à choisir expérimentalement et en fonction du RGB obtenu
    messageXYZ = np.zeros((3, len(messagexy)))
    for indice in range(messagexy.shape[1]):
        x = messagexy[0, indice]
        y = messagexy[1, indice]
        messageXYZ[0, ] = Y*x/y
        messageXYZ[1, ] = Y
        messageXYZ[2, ] = (1-x-y)*Y/y
    return messageXYZ

def XYZ_to_RB(): # R, G, B = scalaire entre 0.0 et 1.0
    pass

def csk(messageMan:str, nombreSubdivisions:int, tensionMin:int, tensionMax:int, N:int, Y:int) -> list:
    """
    transforme le message en chromacité en valeurs de tension pour les LEDS
    on utilise la modulation colors shifting keying (CSK)
    """


    primariesColorsxy = {}


    dicoPointsPrimaires = creationCodagePoints(primariesColorsxy, nombreSubdivisions)
    messagexy = positionsDiagramme(messageMan, dicoPointsPrimaires)
    messageXYZ = xyY_to_XYZ(messagexy, Y)
    messageRGB = XYZ_to_RB(messageXYZ) # tableau numpy 2 lignes len(messageXYZ) colonnes

    tension = np.zeros((2, messageRGB.shape[1])) # RB
    for indice in range(messageRGB.shape[1]):
        tension[0, indice] = tensionMin - messageRGB[0, indice]*(tensionMin - tensionMax)
        tension[1, indice] = tensionMin - messageRGB[1, indice]*(tensionMin - tensionMax)

        if tension[0, indice] < float(tensionMin):
            tension[0, indice] = float(tensionMin)
            print("valeur de tension inférieure à tensionMin V")
        elif tension[0, indice] > float(tensionMax):
            tension[0, indice] = float(tensionMax)
            print("valeur de tension supérieure à tensionMax V")

    np.round(tension, 2)
    tensionEchantillonnee = np.zeros((2, tension.shape[1]), dtype=np.float32)

    for indice in range(tension.shape[1]):
        for k in range(N):
            tensionEchantillonnee[0, k + N*indice] = tension[0, indice]

    return tensionEchantillonnee

def emission(message:str, nombreSubdivisions:int, tensionMin:int, tensionMax:int, N:int, Y:int, startMan:str, endMan:str) -> list:
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan # accroches ajoutées au message
    return csk(messageMan, nombreSubdivisions, tensionMin, tensionMax, N, Y)


# Partie réception
# ATTENTION le message sera à l'envers car les infos envoyées en premières seront reçues en première