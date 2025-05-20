#!/home/ficova/TIPE/CSK/.venv/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pycanum.main as pycan
from bitarray import bitarray

matplotlib.use("Qt5Agg")
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

def creationAccroches(lettreStart:str, lettreEnd:str, nombreRepetitions:int) -> str:
    """
    on créée une succession improbable
    """
    return (encodage(lettreStart)*nombreRepetitions, encodage(lettreEnd)*nombreRepetitions)

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
    centres = np.ones((2, nombreSubdivisions+1))*np.linspace(0, tensionMax, num=nombreSubdivisions+1, endpoint=True)

    for k in range(nombreSubdivisions+1):
        dictCentres[codageBinaire(k, 2)] = centres[:, k]
    
    return dictCentres

def csk(messageMan:str, nombreSubdivisions:int, tensionMax:int, N:int) -> list:
    """
    transforme le message en chromacité en valeurs de tension pour les LEDS
    on utilise la modulation color shifting keying (CSK)
    """
    dictCentres = centreToBits(tensionMax, nombreSubdivisions)
    tensions = np.zeros((2, len(messageMan)/2)) # /2 pas de problème car Manchester double taille donc paire

    indice = 0
    while indice != len(messageMan)/2:
        for k in range(0, len(messageMan)-2, 2):
            tensions[:indice] = dictCentres[messageMan[k:k+2]]
            indice += 1

    return np.repeat(tensions, repeats=N, axis=1) # chaque colonne est dupliqué N fois

def emission(message:str, couleursPrimairesXYZ:dict, nombreSubdivisions:int, tensionMax:int, N:int, Y:int, start:str, end:str) -> list:
    messageMan = codageManchester(start + encodage(message) + end) # accroches ajoutées au message
    return csk(messageMan, couleursPrimairesXYZ, nombreSubdivisions, tensionMax, N, Y)


# Partie réception


def calibragePhotodiodes(tensionMax:float) -> list:
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

def pointsPlan(tensions:list, tension_to_RB:list) -> dict:
    positions = np.zeros((2, len(tensions))) # positions x, y
    for indice in range(len(tensions)):
        positions[:, indice] = tension_to_RB @ tensions[:, indice]
    return positions

def pointsToBits(pointsBits:list, dictCentres:list) -> str:
    signalBinMan = ''
    for indicePoint in range(pointsBits.shape[1]):
        distance = float.inf
        bits_temp = ''
        for bits in dictCentres:
            distance_temp = (pointsBits[0, indicePoint]-dictCentres[bits][0])**2 + (pointsBits[1, indicePoint]-dictCentres[bits][1])**2
            if distance_temp <= distance:
                distance = distance_temp
                bits_temp = bits
        if distance == float.inf:
            print("Erreur dans pointsToBits(), distance non calculée")
        signalMan += bits_temp
    return signalBinMan

def demodulation(tensions:list, tensionMax:float, nombreSubdivisions:int) -> str:
    dictCentres = centreToBits(tensionMax, nombreSubdivisions)
    tension_to_RB = calibragePhotodiodes(tensionMax)

    pointsBits = pointsPlan(tensions, tension_to_RB)
    signalBinMan = pointsToBits(pointsBits, dictCentres)
    return signalBinMan

def decodageMan(signalBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    signalBin = ''
    for indice in range(len(signalBinMan-1)):
        if signalBinMan[indice] == '0' and signalBinMan[indice+1] == '1':
            signalBin += '1'
        elif signalBinMan[indice] == '1' and signalBinMan[indice+1] == '0':
            signalBin += '0'
        else:
            print('Transition non définie dans decodageMan()')
    return signalBin

def chercheIndiceAccroche(signalBin:str, accroche:str, role:str, maxErreursAccroche:int) -> int:
    """
    lors de la transmission du message, des erreurs apparaissent causées par différents facteurs
    pour trouver lorsque le message débute et finit on utilise des accroches,
    on doit alors autoriser quelques erreurs sur ces accroches
    """
    if role != 'start' and role != 'end':
        print('Erreur dans le rôle des accroches dans chercheIndiceAccroche()')
        return []

    indiceAccroche = float.inf
    accrocheBits = bitarray(accroche)
    indice = 0
    while indiceAccroche == float.inf and indice <= len(signalBin)-len(accroche):
        indice += 1
        signalBits = bitarray(signalBin[indice:indice+len(accroche)])
        nombreErreurs = (signalBits ^ accrocheBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursAccroche and role == 'start':
            indiceAccroche = indice+len(role)
        elif nombreErreurs <= maxErreursAccroche and role == 'end':
            indiceAccroche = indice

    if indiceAccroche == float.inf:
        print('Accroche non trouvée')

    return indiceAccroche

def detectionAccroche(signalBin:str, start:str, end:str, maxErreursAccroche:int) -> str:
    """
    slice le signal binaire pour ne garder que le message sans les accroches
    """
    start = chercheIndiceAccroche(signalBin, start, 'start', maxErreursAccroche)
    end = chercheIndiceAccroche(signalBin, end, 'end', maxErreursAccroche)
    
    if end <= start:
        print("Erreur dans la position des accroches trouvées")

    return signalBin[start:end]

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

def reception(tension:list, tensionMax:float, start:str, end:str, nombreSubdivisions:int, maxErreursAccroche:int) -> str:
    signalBinMan = demodulation(tension, tensionMax, nombreSubdivisions)
    signalBin = decodageMan(signalBinMan)
    messageBin = detectionAccroche(signalBin, start, end, maxErreursAccroche)
    return decodageASCII(messageBin)
