#!/home/ficova/TIPE/CSK/.venv/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pycanum.main as pycan
from colour.plotting import *
from bitarray import bitarray

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


def codageBinaire(nombre:int) -> str:
    """
    nombre décimal -> nombre en binaire
    attention on code de gauche à droite (petites puissances à gauche)
    """
    nombreBin = ''
    while nombre > 0:
        nombreBin += str(nombre % 2)
        nombre //= 2
    while len(nombreBin) < 8: # on veut une taille fixe, on ajoute des 0
        nombreBin += '0'
    return nombreBin

def encodage(message:str) -> str:
    """
    message texte (str) -> message en binaire (str)
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre)
    return messageBin

def creationAccroche(lettre:str, nombreRepetitions) -> str:
    """
    on créée une succession improbable
    """
    return encodage(lettre)*nombreRepetitions

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
    RGB : chaque ligne = couleur, colonnes = LED rouge, LED verte, LED bleu
    """
    techantSortie = 1e-3 # période d'échantillonnage en secondes
    temissionBit = 1e-2
    N = int(temissionBit/techantSortie)

    RGB = np.identity(3)
    tensionsEmission = np.repeat(RGB*tensionMax, repeats=N, axis=1) # axis = colonnes

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

    # RGB (Id) = M * tensionsReceptionMoy
    # M = (tensionsReceptionMoy)^-1
    M = np.linalg.inv(tensionsReceptionMoy)

    return M

def RGB_to_xyY(): # Approximation X = x(lambda) parait ici moins réaliste
    pass

def xyY_to_binary():
    # On cherche le point codant le plus proche
    pass

def codageBaseDix(byte:str) -> int:
    """
    nombre binaire -> nombre décimal
    attention on code de gauche à droite (petites puissances à gauche)
    """
    asciiDecimal = 0
    for bit in range(len(byte)):
        asciiDecimal += int(byte[bit]) * (2 ** bit) # A VERIFIER (n-k) au lieu de k
    return asciiDecimal

def mostCommon(liste:list, type:str):
    """
    trouve l'élément le plus commun d'une liste
    on peut choisir le datatype renvoyé
    """
    if liste == []:
        print('Erreur : la liste est vide')
        return -1
    
    dict = {}
    for element in liste:
        if element not in dict:
            dict[element] = 1
        else:
            dict[element] += 1
    
    elementMax = liste[0]
    nbApparitionMax = 0
    for element in dict:
        if dict[element] > nbApparitionMax:
            elementMax = element
            nbApparitionMax = dict[element]
    
    if type == "float":
        return elementMax
    elif type == "int":
        return int(elementMax)
    elif type == "str":
        return str(elementMax)
    else:
        print("Mauvais datatype sélectionné : choisir int, float ou str")

def decoupeListe(dividedSignal:list, tension:list, size:int):
    """
    découpe la liste des tension reçues en morceau de tailles prédéfinis
    la fonction ne fait pas des paquets parfait mais elle découpe la liste de la manière la plus optimale possible
    elle fonction en utilisant l'effet de bord des listes
    """
    lenT = len(tension)
    if lenT <= size:
        dividedSignal.append(tension)
    else:
        lenT2 = lenT//2
        decoupeListe(dividedSignal, tension[:lenT2], size)
        decoupeListe(dividedSignal, tension[lenT2:], size)

def voltageToBinary(tension:list, N_reception:int) -> str:
    """
    cette fonction normalise les valeurs de tensions reçues
    on découpe la liste tension car des variations de luminosité ambiante rendraient la fonction inopérante
    le principal défi est d'avoir des variations importantes dans chacun des morceaux sinon on perd de l'information
    la taille des morceaux dépend de son nombre de bits et de la fréquence d'échantillonnage
    """
    signalBinMan = ''
    dividedSignal = []
    nb_bits = 4 # expérimentalement on ne voit jamais plus de 2 bits valant 0 ou 1 émis d'affilé
    size = N_reception * 2 * nb_bits # car Manchester double la taille du message
    decoupeListe(dividedSignal, tension, size)

    for morceau in dividedSignal:
        tensionMax = np.max(morceau)
        tensionMin = np.min(morceau)

        if tensionMax == 0:
            signalBinMan += '0'*len(morceau)
        elif (tensionMax - tensionMin) < 0.5:
            print(f'Attention le morceau {morceau} dans voltageToBinary ne possède pas de variation de tension')
            signalBinMan += '0'*len(morceau) # Arbitraire on aurait pu prendre 1
        else:
            morceau = morceau/tensionMax
            min = tensionMin/tensionMax
            milieu = (1 + min)/2
            for i in range(len(morceau)):
                if morceau[i] > milieu:
                    signalBinMan += '1'
                else:
                    signalBinMan += '0'
    return signalBinMan

def chercheIndicesAccroche(signalBinMan:str, motif:str, maxErreursMotif:int) -> list:
    """
    on cherche l'accroche, or celle-ci n'a pas été transmise parfaitement
    on doit alors accepter un certains nombre d'erreurs dans le motif de l'accroche (id pas de problème)
    on utilise une méthode inspirée de la distance de Hamming pour connaitre ce nombre d'erreurs
    on renvoie la liste des indices de début des motifs avec autant ou moins d'erreurs que maxErreurMotif
    chaque bit est répété N_reception fois (la période d'échantillonage)
    """
    # motif = motifBinMan
    listeIndicesAccroche = []
    motifBits = bitarray(motif)
    for indice in range(len(signalBinMan)-len(motif)):
        signalBits = bitarray(signalBinMan[indice:indice+len(motif)])
        nombreErreurs = (signalBits ^ motifBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursMotif:
            listeIndicesAccroche.append(indice)
    return listeIndicesAccroche

def position(signalBinMan:str, N_reception:int, motif:str, role:str, maxErreursMotif:int) -> int:
    """
    prédis la position de début/fin du message dans signalBinMan grâce à l'identifiant des accroches
    en effet on connait la taille des motifs et le nombre total de (motif + id) -> 8
    """
    positionAccroche = []
    N_reception16 = 16*N_reception # 2*8 car codage Manchester double taille accroche
    N_reception22 = 22*N_reception
    listeIndicesAccroche = chercheIndicesAccroche(signalBinMan, motif, maxErreursMotif)
    
    if listeIndicesAccroche == []:
        print(f"Erreur pas d'accroche {role} trouvée")
        return -1
    for indiceAccroche in listeIndicesAccroche:
        accrocheID = signalBinMan[indiceAccroche+N_reception16:indiceAccroche+N_reception22]
        idBin = ''
        for indiceID in range(0, 2*N_reception, N_reception):
            idBin += mostCommon(accrocheID[indiceID:indiceID+N_reception], 'str')
        id = codageBaseDix(idBin)
        if 0 <= id < 8:
            if role == 'start':
                start = indiceAccroche + (8 - id)*N_reception22 # 22 = taille de chaque accroche après codage Manchester, 8 = nombre de motifs de l'accroche
                positionAccroche.append(start)
            elif role == 'end':
                end = indiceAccroche - id*N_reception22
                positionAccroche.append(end)
            else:
                print(f'Erreur : {role} n\'est pas un rôle valide (start ou end)')
                return -1
        else:
            print('Erreur : id pas dans intervalle (pas grave)')
    print(f"{role} : {positionAccroche}")
    return mostCommon(positionAccroche, 'int')

def detectionAccroche(signalBinMan:str, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    """
    slice le signal binaire (toujours codé en Manchester) pour ne garder que le message sans les accroches
    """
    startDoublonsMan = ""
    endDoublonsMan = ""

    for k in range(len(startMan)):
        startDoublonsMan += N_reception * startMan[k]
        endDoublonsMan += N_reception * endMan[k]
    
    motifStart = startDoublonsMan[:N_reception*16] # car codage Manchester a doublé la taille de l'accroche
    motifEnd = endDoublonsMan[:N_reception*16]

    start = position(signalBinMan, N_reception, motifStart, 'start', maxErreursMotif)
    end = position(signalBinMan, N_reception, motifEnd, 'end', maxErreursMotif)
    
    if end >= start:
        print("Erreur dans la position des accroches trouvées")

    return signalBinMan[start:end]

def demodulation(tension:list, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    """
    on extraie le message binaire (sans les accroches) de la liste des tensions
    on enlève les répétitions causé par la fréquence d'échantillonnage N_reception
    si les valeurs sont légérement différente, on prend la plus commune
    """
    print(tension)
    tension = np.round(tension, 1)
    print(len(tension))

    signalBinMan = voltageToBinary(tension, N_reception)

    messageBinManDouble = detectionAccroche(signalBinMan, N_reception, startMan, endMan, maxErreursMotif) # chaque bit est répété N_reception fois par rapport au message Man envoyé

    messageBinMan = '' # on enlève les doublons

    valeursBit = [int(messageBinManDouble[0])]
    for indice in range(1, len(messageBinManDouble)):
        if indice % N_reception == 0:
            messageBinMan += mostCommon(valeursBit, 'str')
            valeursBit = [int(messageBinManDouble[indice])]
        else:
            valeursBit.append(int(messageBinManDouble[indice]))
    return messageBinMan

def decodageMan(messageBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    messageBin = ''
    for k in range(0, len(messageBinMan), 2): # pas de 2 car on saute la transition
        if messageBinMan[k] == '0': # transition 0 --> 1
            messageBin += '1'
        else: # transition 1 --> 0
            messageBin += '0'
    return messageBin

def decodageASCII(messageBin:str) -> str:
    """
    message binaire -> texte ASCII
    """
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tension:list, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    return decodageASCII(decodageMan(demodulation(tension, N_reception, startMan, endMan, maxErreursMotif)))