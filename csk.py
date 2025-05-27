#!/home/ficova/TIPE/CSK/.venv/bin/python

import numpy as np
import matplotlib.pyplot as plt
# import pycanum.main as pycan
from bitarray import bitarray

###########################################################################################################sys = pycan.Sysam("SP5")


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

def encodage(message:str) -> str:
    """
    message texte (str) -> message en binaire (str)
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre, 8)
    return messageBin

def creationAccroches(lettre1:str, lettre2:str, repetitions:int) -> tuple:
    """
    on créée une succesion improbable
    """
    return (encodage(lettre1)*repetitions, encodage(lettre2)*repetitions)

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

def centreToBits(tensionMax:float, nombreSubdivisions:int):
    dictCentres = {}
    line = np.linspace(0, tensionMax, num=nombreSubdivisions+1, endpoint=True)
    centres = np.array([line, line[::-1]])

    for k in range(nombreSubdivisions+1):
        dictCentres[codageBinaire(k, 2)] = centres[:, k]
    
    return dictCentres

def csk(messageMan:str, nombreSubdivisions:int, tensionMax:int, N:int) -> np.ndarray:
    """
    transforme le message en chromacité en valeurs de tension pour les LEDS
    on utilise la modulation color shifting keying (CSK)
    """
    dictCentres = centreToBits(tensionMax, nombreSubdivisions)
    tensions = np.zeros((2, int(len(messageMan)/2))) # /2 pas de problème car Manchester double taille donc paire

    indice = 0
    for k in range(0, len(messageMan), 2):
        tensions[:, indice] = dictCentres[messageMan[k:k+2]]
        indice += 1

    return np.repeat(tensions, repeats=N, axis=1) # chaque colonne est dupliqué N fois

def emission(message:str, startMan:str, endMan:str, nombreSubdivisions:int, tensionMax:int, N:int) -> np.ndarray:
    messageMan = startMan + codageManchester(encodage(message)) + endMan
    return csk(messageMan, nombreSubdivisions, tensionMax, N)


# Partie réception


def calibragePhotodiodes(tensionMax:float) -> np.ndarray:
    """
    A chaque couleur primaire on attribue les valeurs des photodiodes
    """
    techantSortie = 1e-3 # période d'échantillonnage en secondes
    temissionBit = 1e-2
    N = int(temissionBit/techantSortie)

    tension_RB = np.identity(2)*tensionMax
    tensionsEmission = np.repeat(tension_RB, repeats=N, axis=1) # axis = colonnes

    tensionsReceptionMoy = np.zeros((2, 2))
    indiceCouleur = 0
    for couleur in tensionsEmission:
        sys.config_sortie(1, techantSortie*1e6, couleur) # en microsecondes et non périodique
        sys.declencher_sorties(1, 0)

        # TECHANTENTREE < TECHANTSORTIE sinon on va mesurer des couleurs intermédiaire !!!!!!!!!!!
        techantEntree = 1e-3 # période d'échantillonnage en secondes
        tempsReception = 2 # en secondes
        nbpoints = int(tempsReception/techantEntree)
        
        sys.config_entrees([1, 2], [10]) # attention 10 V max
        sys.config_echantillon(techantEntree*1e6, nbpoints) # période d'échantillonnage en microsecondes
        sys.config_quantification(12)

        # Emission/acquisition

        sys.acquerir()
        sys.declencher_sorties(1, 1)
        sys.stopper_sorties(1, 1)

        # Ce que l'on reçoit
        tensions = sys.entrees()
        sys.fermer()

        print(tensions)
        # tensions = [liste_entrée1, liste_entrée2]
        for tensionCouleur in tensions:
            np.mean(tensionCouleur)

        tensionsReceptionMoy[indiceCouleur, :] = tensions
        indiceCouleur += 1

    """
                                 rouge, bleu
    on veut tensionsReceptionMoy = [U_r, U_r,
                                    U_b, U_b]
    """
    # RGB (Id) = M * tensionsReceptionMoy
    # M = (tensionsReceptionMoy)^-1
    return np.linalg.inv(tensionsReceptionMoy)

def pointsPlan(tensions:np.ndarray, tension_to_RB:np.ndarray) -> np.ndarray:
    positions = np.zeros((2, tensions.shape[1])) # positions x, y
    for indice in range(tensions.shape[1]):
        positions[:, indice] = tension_to_RB @ tensions[:, indice]
    return positions

def pointsToBits(pointsBits:np.ndarray, dictCentres:dict) -> str:
    signalBinMan = ''
    for indicePoint in range(pointsBits.shape[1]):
        distance = float('inf')
        bits_temp = ''
        for bits in dictCentres:
            distance_temp = (pointsBits[0, indicePoint]-dictCentres[bits][0])**2 + (pointsBits[1, indicePoint]-dictCentres[bits][1])**2
            if distance_temp <= distance:
                distance = distance_temp
                bits_temp = bits
        if distance == float('inf'):
            print("Erreur dans pointsToBits(), distance non calculée")
        signalBinMan += bits_temp
    return signalBinMan

def chercheIndicesAccroche(signalBinMan:str, role:str, motif:str, maxErreursMotif:int) -> int:
    """
    on cherche l'accroche, or celle-ci n'a pas été transmise parfaitement
    on doit alors accepter un certains nombre d'erreurs dans le motif de l'accroche (id pas de problème)
    on utilise une méthode inspirée de la distance de Hamming pour connaitre ce nombre d'erreurs
    on renvoie la liste des indices de début des motifs avec autant ou moins d'erreurs que maxErreurMotif
    chaque bit est répété N_reception fois (la période d'échantillonage)
    """
    indiceAccroche = []
    motifBits = bitarray(motif)
    for indice in range(len(signalBinMan)-len(motif)):
        signalBits = bitarray(signalBinMan[indice:indice+len(motif)])
        nombreErreurs = (signalBits ^ motifBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursMotif:
            indiceAccroche.append(indice)
    if len(indiceAccroche) != 1:
        print('Plus ou aucune accroche trouvée')
        print(indiceAccroche)
        return -1
    
    if role == 'start':
        indiceAccroche = indiceAccroche[-1]
    elif role == 'end':
        indiceAccroche = indiceAccroche[0]
    else:
        print('Mauvais rôle d\'accroche sélectionné')
        return -1

    return indiceAccroche

def detectionAccroche(signalBinMan:str, startDoublonsMan:str, endDoublonsMan:str, maxErreursMotif:int) -> tuple:
    startPos = chercheIndicesAccroche(signalBinMan, 'start', startDoublonsMan, maxErreursMotif)
    endPos = chercheIndicesAccroche(signalBinMan, 'end', endDoublonsMan, maxErreursMotif)
    
    if endPos <= startPos:
        print("Erreur dans la position des accroches trouvées")

    return (startPos, endPos)

def mostCommon(liste:list | str, type:str) -> (None | float | int | str):
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

def demodulation(tensions:np.ndarray, tensionMax:float, startMan:str, endMan:str, nombreSubdivisions:int, maxErreursMotif:int, N_reception:int) -> str:
    dictCentres = centreToBits(tensionMax, nombreSubdivisions)
    tension_to_RB = calibragePhotodiodes(tensionMax)

    pointsBits = pointsPlan(tensions, tension_to_RB)
    signalBinManDouble = pointsToBits(pointsBits, dictCentres)

    startDoublonsMan = ""
    endDoublonsMan = ""

    for k in range(0, len(startMan), 2):
        startDoublonsMan += N_reception * startMan[k:k+2]
        endDoublonsMan += N_reception * endMan[k:k+2]

    (startPos, endPos) = detectionAccroche(signalBinManDouble, startDoublonsMan, endDoublonsMan, maxErreursMotif) # chaque bit est répété N_reception fois par rapport au message Man envoyé

    messageBinMan = '' # on enlève les doublons

    valeursBit = [int(signalBinManDouble[startPos+len(startDoublonsMan):startPos+len(startDoublonsMan)+1])]
    indiceModulo = 1
    for indice in range(startPos+len(startDoublonsMan), endPos-1, 2): # -1 ???
        if indiceModulo % N_reception == 0:
            messageBinMan += mostCommon(valeursBit, 'str')
            valeursBit = [int(signalBinManDouble[indice:indice+2])]
        else:
            valeursBit.append(int(signalBinManDouble[indice:indice+2]))
        indiceModulo += 1
    messageBinMan += mostCommon(valeursBit, 'str')

    return messageBinMan

def decodageMan(messageBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    et à l'utilisation de XOR
    """
    horloge = [k%2 for k in range(1, len(messageBinMan)+1)] # On commence à 1 pour que l'horloge commence par 1
    messageBinTemp = ''

    for indice in range(len(messageBinMan)):
        if horloge[indice] == messageBinMan[indice]:
            messageBinTemp += '0'
        else:
            messageBinTemp += '1'
    
    if len(messageBinMan) % 2 != 0:
        print('len(messageBinTemp) n\'est pas paire')

    messageBin = ''
    for indice in range(0, len(messageBinTemp), 2): # Manchester double taille donc forcément paire
        messageBin += messageBinTemp[indice]

    return messageBin

def codageBaseDix(byte:str) -> int:
    """
    nombre binaire -> nombre décimal
    attention on code de gauche à droite (petites puissances à gauche)
    """
    asciiDecimal = 0
    for bit in range(len(byte)):
        asciiDecimal += int(byte[bit]) * (2 ** bit) # A VERIFIER (n-k) au lieu de k
    return asciiDecimal

def decodageASCII(messageBin:str) -> str:
    """
    message binaire -> texte ASCII
    """
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tensions:np.ndarray, tensionMax:float, startMan:str, endMan:str, nombreSubdivisions:int, maxErreursAccroche:int, N_reception:int) -> str:
    messageBinMan = demodulation(tensions, tensionMax, startMan, endMan, nombreSubdivisions, maxErreursAccroche, N_reception)
    messageBin = decodageMan(messageBinMan)
    return decodageASCII(messageBin)

# Résultats

def constellation(messageBin:str, tensionMax:float, nombreSubdivisions:int):
    line = np.linspace(0, tensionMax, num=nombreSubdivisions+1, endpoint=True)
    centres = np.array([line, line[::-1]])
    plt.scatter(centres[0, :], centres[1, :], label="Points Codants", s=50)

    dictCentres = centreToBits(tensionMax, nombreSubdivisions)
    positionsMessage = np.zeros((2, int(len(messageBin)/2)))
    for indice in range(0, len(messageBin)-2, 2):
        positionsMessage[:, indice] = dictCentres[messageBin[indice:indice+2]]
    plt.scatter(positionsMessage[0, :], positionsMessage[1, :], s=25, color='red')

    plt.xlabel("U_blue (V)")
    plt.ylabel("U_red (V)")
    plt.grid()
    plt.legend()
    plt.show()
