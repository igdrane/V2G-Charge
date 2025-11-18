# -*- coding: utf-8 -*-
"""
Created on Oct  25 00:22:51 2025

@author: igadarne
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

class Voiture:
    def __init__(self, id, batterie, puissance, arrive, depart, batterie_init):
        self.id = id
        self.batterie = batterie  # kWh
        self.puissance = puissance  # kW
        self.arrive = arrive
        self.depart = depart
        self.batterie_init = batterie_init
        self.batterie_cible = 0.8

class SimulateurV2G:
    def __init__(self):
        self.voitures = []
        self.prix_electricite = self.creer_prix()
    
    def creer_prix(self):
        prix = [0.18]*16 + [0.12]*20 + [0.18]*12 
        # for crenau in range(48):
            # if 14 <= crenau <= 39:
            #     prix.append(0.18)
            # else:
            #     prix.append(0.12)
        return np.array(prix)
    
    def ajouter_voiture(self, voiture):
        self.voitures.append(voiture)
    
    def charge_naive(self):
        puissance_totale = np.zeros(48)
        cout_total = 0
        
        for voiture in self.voitures:
            puissance_voiture = np.zeros(48)
            energie_necessaire = (0.8 - voiture.batterie_init) * voiture.batterie
            energie_chargee = 0
            
            for t in range(voiture.arrive, min(voiture.depart, 48)):
                if energie_chargee >= energie_necessaire:
                    break
                    
                puissance_voiture[t] = voiture.puissance
                energie_chargee += voiture.puissance * 0.5
            
            puissance_totale += puissance_voiture
            cout_total += np.sum(puissance_voiture * self.prix_electricite*0.5)
        
        return puissance_totale, cout_total
    
    def charge_optimisee(self):
        contraintes = []
        limites = []
        
        for i, voiture in enumerate(self.voitures):
            energie_necessaire = (voiture.batterie_cible - voiture.batterie_init) * voiture.batterie
            
            def contrainte_energie(x, idx=i):
                puissance_voiture = x[idx * 48:(idx + 1) * 48]
                energie_chargee = 0
                for t in range(voiture.arrive, min(voiture.depart, 48)):
                    energie_chargee += puissance_voiture[t]*0.5
                return energie_chargee - energie_necessaire
            
            contraintes.append({'type': 'eq', 'fun': contrainte_energie})
            
            for t in range(48):
                if voiture.arrive <= t < voiture.depart:
                    limites.append((0, voiture.puissance))
                else:
                    limites.append((0, 0))
        
        def cout_total(x):
            cout = 0
            for i in range(len(self.voitures)):
                puissance_voiture = x[i * 48:(i + 1) * 48]
                cout += np.sum(puissance_voiture * self.prix_electricite * 0.5)
            return cout
        
        x0 = np.zeros(len(self.voitures) * 48)
        resultat = minimize(cout_total, x0, method='SLSQP', bounds=limites, constraints=contraintes)
        
        if resultat.success:
            puissance_optimisee = np.zeros(48)
            for i in range(len(self.voitures)):
                puissance_voiture = resultat.x[i * 48:(i + 1) * 48]
                puissance_optimisee += puissance_voiture
            return puissance_optimisee, resultat.fun
        else:
            return None, None
    def demarrer_simulation(self):
        print("Simulation V2G - 3 voitures")
        
        # Création des 3 voitures
        voiture1 = Voiture(1, 40, 7, 6, 36, 0.2)
        voiture2 = Voiture(2, 60, 11, 8, 38, 0.3)  
        voiture3 = Voiture(3, 75, 22, 10, 40, 0.4)
        
        self.ajouter_voiture(voiture1)
        self.ajouter_voiture(voiture2)
        self.ajouter_voiture(voiture3)
        
        # Calcul des stratégies
        puissance_naive, cout_naive = self.charge_naive()
        puissance_opti, cout_opti = self.charge_optimisee()
        
        # Création du graphique avec double axe
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Premier axe (gauche) pour la puissance
        ax1.plot(range(48), puissance_naive, 'r-', label='Charge naïve', linewidth=2)
        ax1.plot(range(48), puissance_opti, 'b-', label='Charge optimisée', linewidth=2)
        ax1.set_xlabel('Heures')
        ax1.set_ylabel('Puissance (kW)', color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True)
        
        # Configuration de l'axe X avec tous les créneaux
        ax1.set_xticks(range(48))
        ax1.set_xticklabels(range(48))
        
        # Deuxième axe (droite) pour le prix
        ax2 = ax1.twinx()
        ax2.plot(range(48), self.prix_electricite, 'g--', label='Prix électricité (€/kWh)', linewidth=2)
        ax2.set_ylabel('Prix (€/kWh)', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        
        # Titre et légende
        plt.title('Comparaison des stratégies de charge V2G')
        
        # Combinaison des légendes des deux axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        plt.savefig('resultats.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        economie = (cout_naive - cout_opti) / cout_naive * 100
        
        print(f"\nRésultats:")
        print(f"Coût charge naive: {cout_naive:.2f}€")
        print(f"Coût charge optimisée: {cout_opti:.2f}€")
        print(f"Économie: {economie:.1f}%")
        
        return cout_naive, cout_opti, economie

# Lancement de la simulation
if __name__ == "__main__":
    simulateur = SimulateurV2G()
    simulateur.demarrer_simulation()