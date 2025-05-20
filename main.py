from csk import *
import matplotlib.pyplot as plt
import pycanum.main as pycan

###########################################################################################################sys = pycan.Sysam("SP5")

# PARAMETRES EMISSION

couleursPrimairesXYZ = {"red":[0.794186, 0.3447768, 0.00013596], # liste X = x(lambda), Y = y(lambda)...  lambda = 623 nm
                        "green":[0.08973996, 0.7619694, 0.06456784], # lambda = 523 nm
                        "blue":[0.2184072, 0.0836668, 1.3898799]} # lambda = 468 nm

techantSortie = 1e-3 # période d'échantillonnage en secondes
temissionBit = 1e-2
N = int(temissionBit/techantSortie) # nombre de points représentant 1 bit
tensionMax = 5
nombreSubdivisions = 3
# message = input("Message à envoyer : ")
message = 'jellooo'
(start, end) = creationAccroches('a', 'z', 10)
signal = emission(message, couleursPrimairesXYZ, nombreSubdivisions, tensionMax, N, 1, start, end)

sys.config_sortie(1, techantSortie*1e6, signal[0])
sys.config_sortie(2, techantSortie*1e6, signal[2]) # en microsecondes et non périodique
sys.declencher_sorties(1, 0)
sys.declencher_sorties(0, 1)

# PARAMETRES RECEPTION

# TECHANTENTREE < TECHANTSORTIE sinon on va mesurer des couleurs intermédiaire !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
techantEntree = 1e-3 # période d'échantillonnage en secondes
tempsReception = 5 # en secondes
nbpoints = int(tempsReception/techantEntree)
N_reception = int(temissionBit/techantEntree) # IDEALEMENT IMPAIR POUR MOSTCOMMON()

sys.config_entrees([2, 3], [10]) # attention 10 V max
sys.config_echantillon(techantEntree*1e6, nbpoints) # période d'échantillonnage en microsecondes
sys.config_quantification(12)


# Emission/acquisition

sys.acquerir()
sys.declencher_sorties(1, 1)
sys.stopper_sorties(1, 1)

# Ce que l'on reçoit
temps = sys.temps()
tensions = sys.entrees()
sys.fermer()

# Résultats

print(N)
print(N_reception)


# Ce qu'on envoie aux LEDs

t = [1]*len(signal)
c=1
for k in range(len(t)):
    t[k] = techantSortie*c
    c += 1

plt.figure()
plt.scatter(t, signal, label="SA1", s=1)
plt.xlabel("t (s)")
plt.ylabel("u (V)")
plt.grid()
plt.legend()

# Ce que l'on reçoit

plt.figure()
plt.scatter(temps[0], tensions[0], label="EA2", s=1)
plt.xlabel("t (s)")
plt.ylabel("u (V)")
plt.grid()
plt.legend()
plt.show()