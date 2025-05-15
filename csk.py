import numpy as np

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

def csk(messageMan:str, tensionMin:int, tensionMax:int, N:int) -> list:
    """
    transforme le message codé (Manchester) en valeurs de tension pour les LEDS
    on utilise la modulation on-off keying (OOK)
    """
    tension = []
    for byte in messageMan:
        if byte == '0':
            tension += [tensionMin]*N
        elif byte == '1':
            tension += [tensionMax]*N
        else:
            print('Erreur : le message binaire est corrompu, une valeur autre que 0 et 1 a été trouver')
            return []
    return np.array(tension, dtype=np.float32)

def emission(message:str, tensionMin:int, tensionMax:int, N:int, startMan:str, endMan:str) -> list:
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan # accroches ajoutées au message
    return ook(messageMan, tensionMin, tensionMax, N)


# Partie réception
# ATTENTION le message sera à l'envers car les infos envoyées en premières seront reçues en première