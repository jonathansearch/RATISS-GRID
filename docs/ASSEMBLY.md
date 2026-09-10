# 🔧 ASSEMBLY — Plan d'assemblage RATISS-GRID (config Standard)

Document exécutable par un ingénieur/technicien électricien (ENSPY, AIMS Limbé,
diaspora). Chaque étape est vérifiable. **Sécurité d'abord : le DC batterie ne
pardonne pas — gants, lunettes, outils isolés, jamais de bijoux métalliques.**

## ⚠️ Consignes de sécurité (lire AVANT)
- Le banc LiFePO4 48 V / 280 Ah peut débiter > 1000 A en court-circuit → arc
  électrique violent. Toujours laisser le disjoncteur DC 63 A OUVERT pendant
  l'assemblage, ne le fermer qu'à la toute fin.
- Ordre de connexion : d'abord la terre, ensuite le négatif, enfin le positif.
- Vérifier la polarité 2 fois avant chaque connexion définitive.

## 1️⃣ Schéma unifilaire (texte)

```
[9× PV 550Wc] --(string DC)--> [Sectionneur+fusible PV] --> [Parafoudre DC]
      |                                                        |
      v                                                        v
[MPPT / Onduleur hybride 5kVA 48V] <---------------------------
      |
      |---- [Disjoncteur DC 63A] ---- [BMS 16S] ---- [Batterie 16×280Ah]
      |                                        |
      |---- [Disjoncteur DC 63A] ---- [Supercaps 48V 50F]
      |
      |---- sortie AC 230V --> [Parafoudre AC] --> [Tableau de distribution]
                                                        |
                          [Disjoncteur AC 32A] ------> circuit CRITIQUE
                          [Disjoncteur AC 32A] ------> circuit CONFORT (délestable)
      |
[Eneo AC] ---- entrée appoint chargeur de l'onduleur hybride
[Piquet de terre <10Ω] ---- relié à TOUS les châssis (équipotentialité)
```

## 2️⃣ Étapes d'assemblage

1. **Structure PV** : fixer les 9 panneaux (toiture ou sol, inclinaison ~10°
   vers le sud à Yaoundé, ~5° à Douala, face équateur). Résistance mécanique
   aux vents (saison des pluies). Câblage string : 3×3 (3 strings de 3 en série)
   selon la tension d'entrée MPPT (vérifier Vmp×3 < Vmax MPPT).
2. **Mise à la terre** : planter le piquet, mesurer < 10 Ω à la barrette,
   relier structure PV + châssis onduleur + boîtier batterie.
3. **Banc batterie** : assembler les 16 cellules en série (16S) avec busbar
   cuivre, serrage au couple, cosses serties. Monter le BMS selon son schéma
   (B− vers négatif pack, P− vers sortie, fils d'équilibrage sur chaque cellule).
4. **Supercaps** : monter le module 48 V sur le bus DC via son propre
   disjoncteur 63 A. C'est lui qui prend les micro-coupures.
5. **Conversion** : raccorder MPPT → bus DC 48 V, onduleur → bus DC puis
   sortie AC → tableau.
6. **Protections** : installer parafoudres DC et AC, tous les disjoncteurs.
7. **Supervision** : câbler ESP32 + capteurs (tension bus DC, courant batterie,
   tension AC). Flasher le firmware RATISS (TopologicalWatchdog).

## 3️⃣ Procédure de test de réception (avant mise en service)

| Étape | Test | Critère d'acceptation |
|---|---|---|
| T1 | Tension à vide du string PV au multimètre | ≈ 3 × Voc panneau (±10 %) |
| T2 | Continuité de terre | < 10 Ω piquet ↔ châssis |
| T3 | Tension pack batterie | 51.2 V nominal (16 × 3.2 V) ±1 V |
| T4 | Équilibrage cellules BMS | écart < 50 mV entre cellules |
| T5 | Isolement DC (mégohmmètre si dispo) | > 1 MΩ vers la terre |
| T6 | Tension supercaps | ≈ 48 V chargé |
| T7 | Sortie onduleur à vide | 230 V ±5 %, 50 Hz, sinus pur (THD < 5 %) |
| T8 | Bascule sur coupure Eneo simulée | charge critique maintenue sans coupure |
| T9 | Charge pleine 2 kW pendant 30 min | pas d'échauffement anormal (< 60 °C cosses) |
| T10 | P_sig supervision | affichage cohérent, alerte sur creux simulé |

## 4️⃣ Séparation critique / confort
- Le **circuit critique** (QPU, incubateur, contrôle — 700 W) est câblé sur un
  départ dédié NON délestable, dimensionné pour l'autonomie solaire pure.
- Le **circuit confort** (postes de travail, clim, ~1.3 kW) est délestable :
  l'onduleur hybride ou un relais de délestage le coupe quand le SoC < 40 %.
- C'est cette séparation qui permet d'atteindre 99.9 % de disponibilité sur le
  critique à budget raisonnable (voir sizing.py).

## 5️⃣ Documentation de l'installation
Remplir une fiche de réception : mesures T1–T10, photos, numéros de série,
date. Archiver dans `docs/installations/` (photo du tableau câblé, relevé de
terre). Toute modification ultérieure met à jour la fiche.
