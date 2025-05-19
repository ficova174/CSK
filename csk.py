#!/home/ficova/TIPE/CSK/.venv/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pycanum.main as pycan
from colour.plotting import *

matplotlib.use("Qt5Agg")
###########################################################################################################sys = pycan.Sysam("SP5")

# Création du diagramme et affichage des points (gamut)

def creationDiagrammeCIE1931(dictTriangle:list, dictPoints:list, positionsBitsMessage:list):
    # Plotting the *CIE 1931 Chromaticity Diagram*.
    # The argument *show=False* is passed so that the plot doesn't get
    # displayed and can be used as a basis for other plots.
    plot_chromaticity_diagram_CIE1931(show=False)

    positionsTriangle = np.array(list(dictTriangle.values())).T
    positionsTriangle = np.concatenate((positionsTriangle, positionsTriangle[:, 0].reshape(-1, 1)), axis=1) # reshape permet de transformer un tableau ligne en tableau colonne (.T ne marche pas)

    positionsBitsRef = np.array(list(dictPoints.values())).T

    # Plotting  chromaticity coordinates.
    plt.plot(positionsTriangle[0], positionsTriangle[1], 'x-', color='black')
    plt.scatter(positionsBitsRef[0, :], positionsBitsRef[1, :], marker='x', color='green', s=100)
    # plt.scatter(positionsBitsMessage[0, :], positionsBitsMessage[1, :], marker='x', color='yellow')

    # Displaying the plot.
    render(
        show=True,
        limits=(-0.1, 0.9, -0.1, 0.9),
        x_tighten=True,
        y_tighten=True)



# Partie émission



# Codage du message


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


# Creation fonctions de transformations et points des couleurs primaires


def creationCouleursPrimairesxy(couleursPrimairesXYZ:dict) -> dict:
    """
    on suppose que le spectre de la distribution de puissance des couleurs primaires possède un pic au niveau
    de leur longueur d'onde dominante, on néglige le reste
    donc X = x(lambda) ...
    """
    listeCouleursPrimaires = ["red", "green", "blue"]
    couleursPrimairesxy = {}

    for couleur in listeCouleursPrimaires:
        denominateur = np.sum(couleursPrimairesXYZ[couleur])
        couleursPrimairesxy[couleur] = np.array([couleursPrimairesXYZ[couleur][0]/denominateur, couleursPrimairesXYZ[couleur][1]/denominateur])
    
    return couleursPrimairesxy


def creationCodagePoints(couleursPrimairesxy:dict, nombreSubdivisions:int):
    """
    on pose 2 couleurs primaires sur le diagramme puis on met des points équidistants sur la droite les rejoignant
    x = (G*primary_green_x + B*primary_blue_x)/(G + B)
    y = (G*primary_green_y + B*primary_blue_y)/(G + B)
    c'est linéaire
    G, B entre 0.0 et 1.0
    couleursPrimairesxy["red"] = [x,
                                y]
    np array
    
    pointDiag["00"] = np.array([[x], [y]]) red
    pointDiag["01"] = np.array([[x], [y]])
    ...
    pointDiag["11"] = np.array([[x], [y]]) blue
    """
    distanceCouleursPrimaires = (couleursPrimairesxy["red"]-couleursPrimairesxy["blue"])/nombreSubdivisions
    listePointsxy = np.zeros((2, nombreSubdivisions+1))

    listePointsxy[:, 0] = couleursPrimairesxy["blue"]
    listePointsxy[:, nombreSubdivisions] = couleursPrimairesxy["red"]

    for point in range(nombreSubdivisions+1):
        listePointsxy[:, point] = couleursPrimairesxy["blue"] + point*distanceCouleursPrimaires

    pointsDiagramme = {}
    for valeur in range(nombreSubdivisions+1):
        pointsDiagramme[codageBinaire(valeur, 2)] = np.round(listePointsxy[:, valeur], 2) # codage binaire à l'envers = problème ?

    print(pointsDiagramme)

    return pointsDiagramme

def positionsDiagramme(messageMan:str, pointsDiagramme:dict) -> list:
    """
    """
    nb_colonnes = int(len(messageMan)/2) # aucun soucis car manchester double taille message donc longueur forcément paire
    messagexy = np.zeros((2, nb_colonnes))
    indice = 0
    for k in range(0, len(messageMan)-2, 2):
        messagexy[:, indice] = pointsDiagramme[messageMan[k:k+2]]
        indice += 1
    if messagexy.shape[1] == len(messageMan)/2:
        return messagexy
    print("messageChromacity.shape[1] == len(messageMan)/2")

def xyY_to_XYZ(messagexy:list, Y:int): # Y représente la luminance, à choisir expérimentalement et en fonction du RGB obtenu
    messageXYZ = np.zeros((3, messagexy.shape[1]))
    for indice in range(messagexy.shape[1]):
        x = messagexy[0, indice]
        y = messagexy[1, indice]
        messageXYZ[0, ] = Y*x/y
        messageXYZ[1, ] = Y
        messageXYZ[2, ] = (1-x-y)*Y/y
    return messageXYZ

def XYZ_to_RGB(messageXYZ:list, couleursPrimairesXYZ:list): # R, G, B = scalaire entre 0.0 et 1.0
    # On veut la ligne du milieu 0 pour avoir G = 0
    M = np.ones((3, 3))
    M[1, :] = 0
    return M

def csk(messageMan:str, couleursPrimairesXYZ:dict, nombreSubdivisions:int, tensionMax:int, N:int, Y:int) -> list:
    """
    transforme le message en chromacité en valeurs de tension pour les LEDS
    on utilise la modulation color shifting keying (CSK)
    """
    couleursPrimairesxy = creationCouleursPrimairesxy(couleursPrimairesXYZ)
    dicoPointsPrimaires = creationCodagePoints(couleursPrimairesxy, nombreSubdivisions)
    messagexy = positionsDiagramme(messageMan, dicoPointsPrimaires)

    # AFFICHAGE
    creationDiagrammeCIE1931(couleursPrimairesxy, dicoPointsPrimaires, messagexy)

    messageXYZ = xyY_to_XYZ(messagexy, Y)
    messageRGB = XYZ_to_RGB(messageXYZ, couleursPrimairesXYZ) # tableau numpy 3 lignes len(messageXYZ) colonnes
    tensions = messageRGB*(tensionMax)

    return np.repeat(tensions, repeats=N, axis=1) # chaque colonne est dupliqué N fois

def emission(message:str, couleursPrimairesXYZ:dict, nombreSubdivisions:int, tensionMax:int, N:int, Y:int, startMan:str, endMan:str) -> list:
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan # accroches ajoutées au message
    return csk(messageMan, couleursPrimairesXYZ, nombreSubdivisions, tensionMax, N, Y)


# Partie réception

def calibragePrimaires(tensionMax:int) -> list:
    """
    A chaque couleur primaire on attribue les valeurs des photodiodes
    tensionsCouleurs : chaque ligne = couleur, colonnes = LED rouge, LED verte, LED bleu
    """
    techantSortie = 1e-3 # période d'échantillonnage en secondes
    temissionBit = 1e-2
    N = int(temissionBit/techantSortie)

    tensionsCouleurs = np.identity(3)*tensionMax
    tensionsEmission = np.repeat(tensionsCouleurs, repeats=N, axis=1) # axis = colonnes

    tensionsReceptionMoy = np.zeros((3, 3))
    indiceCouleur = 0
    for couleur in tensionsEmission:
        sys.config_sortie(1, techantSortie*1e6, couleur) # en microsecondes et non périodique
        sys.declencher_sorties(1, 0)

        # TECHANTENTREE < TECHANTSORTIE sinon on va mesurer des couleurs intermédiaire !!!!!!!!!!!
        techantEntree = 1e-3 # période d'échantillonnage en secondes
        tempsReception = 2 # en secondes
        nbpoints = int(tempsReception/techantEntree)
        
        sys.config_entrees([1, 2, 3], [10]) # attention 10 V max
        sys.config_echantillon(techantEntree*1e6, nbpoints) # période d'échantillonnage en microsecondes
        sys.config_quantification(12)

        # Emission/acquisition

        sys.acquerir()
        sys.declencher_sorties(1, 0)
        sys.stopper_sorties(1, 0)

        # Ce que l'on reçoit
        tensions = sys.entrees()
        sys.fermer()

        # tensions = [liste_entrée1, liste_entrée2, liste_entrée3]
        for tensionCouleur in tensions:
            np.mean(tensionCouleur)

        tensionsReceptionMoy[indiceCouleur, :] = tensions
        indiceCouleur += 1

    # tensionsCouleurs = M * tensionsReceptionMoy
    # M = tensionsCouleurs * (tensionsReceptionMoy)^-1
    M = tensionsCouleurs @ np.linalg.inv(tensionsReceptionMoy)

    return M

