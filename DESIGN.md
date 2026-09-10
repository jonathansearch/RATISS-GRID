# ⚡ RATISS-GRID — DOCUMENT DE CONCEPTION COMPLET

<div align="center">

![RATIS Labs](docs/images/06_logo_ratis_labs.png)

**Coffre-fort énergétique souverain — Priorité 0 de la doctrine RATISS**

Manuel d'ingénierie complet : conception, dimensionnement, assemblage, itérations.

*RATIS Labs · Cameroun · Propriété : JOHNKING0 & Jonathan Evina · ORCID 0009-0000-4092-5313*

</div>

---

> 🇨🇲 **Un mot au Gouvernement de la République du Cameroun**
>
> La souveraineté d'une nation se mesure à sa capacité à produire, contrôler et
> transmettre sa propre énergie. Tant que nos laboratoires, nos hôpitaux et nos
> industries dépendent d'un réseau fragile et d'équipements importés sans
> documentation, nous restons technologiquement vassaux. RATISS-GRID n'est pas
> un gadget : c'est la **brique fondatrice** d'une infrastructure scientifique
> nationale — une électricité pure, stable et ininterrompue, dimensionnée,
> documentée et reproductible par nos propres ingénieurs, avec des composants
> accessibles et un coût maîtrisé. Ce document est un acte de transfert de
> savoir-faire. Il appartient désormais au Cameroun de s'en saisir, de le
> financer à l'échelle, et d'en faire le standard de nos établissements
> critiques. La souveraineté énergétique n'attend pas : elle se construit.

---

## 📑 Table des matières

1. [Vue d'ensemble et philosophie de conception](#1-vue-densemble)
2. [Le problème physique : pourquoi Eneo ne suffit pas](#2-le-problème-physique)
3. [Plan de conception électrique](#3-plan-de-conception-électrique)
4. [Plan de conception mécanique](#4-plan-de-conception-mécanique)
5. [L'appareil une fois monté](#5-lappareil-une-fois-monté)
6. [Le cœur logiciel : architecture du simulateur](#6-le-cœur-logiciel)
7. [La détection topologique P_sig](#7-la-détection-topologique-p_sig)
8. [Guide de montage pas à pas](#8-guide-de-montage)
9. [Itérations de conception et leçons apprises](#9-itérations-de-conception)
10. [Validation et résultats de simulation](#10-validation-et-résultats)
11. [Sécurité](#11-sécurité)
12. [Maintenance et cycle de vie](#12-maintenance)

---

## 1. Vue d'ensemble

RATISS-GRID est un **Conditionneur de Puissance Actif (CPA)** hybride qui
transforme le réseau Eneo erratique en une alimentation de qualité laboratoire.
Il repose sur trois principes de conception non négociables :

1. **Le solaire est la source principale**, Eneo n'est qu'un appoint délesté.
2. **Le stockage est hybride** : supercondensateurs (réponse milliseconde) +
   LiFePO4 (endurance) — chaque technologie fait ce qu'elle fait le mieux.
3. **On valide in silico avant d'acheter** : chaque configuration est simulée
   sur 30+ jours de réseau dégradé avant de dépenser un franc.

### Configurations de référence

| Config | Pic | PV | Batterie | Supercaps | Budget (FCFA) | Charge critique garantie |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| Minimal | 500 W | 1500 Wc | 7.2 kWh | 50 F | ~2.5 M | 500 W |
| **Standard** | 2000 W | 4500 Wc | 14.3 kWh | 50 F | ~6.5 M | **700 W** |
| Labo complet | 5000 W | 9000 Wc | 28.7 kWh | 100 F | ~13 M | 1500 W |

La config **Standard** garantit 700 W de charge critique (QPU 500 W + incubateur
150 W + contrôle 50 W) en solaire pur à 99.9 %, le reste étant délestable.

---

## 2. Le problème physique

Le réseau Eneo présente trois pathologies qui détruisent un équipement de
laboratoire :

- **Micro-coupures** (< 2 s) : invisibles pour une ampoule, fatales pour un QPU
  dont la cohérence s'effondre à la moindre interruption d'horloge.
- **Creux de tension** : la tension chute sous 180 V, les alimentations à
  découpage sortent de leur plage et grillent.
- **Bruit harmonique** : la distorsion du 50 Hz perturbe toute mesure de
  précision (biologie, photonique).

**Conséquence** : sans conditionneur, tout investissement scientifique est
voué à l'échec. C'est pourquoi le CPA est la **Priorité 0** — le nerf de la
guerre avant toute autre brique.

---

## 3. Plan de conception électrique

![Plan électrique](docs/images/01_plan_electrique.png)

### Chaîne de puissance

```
Panneaux PV (4500 Wc) → MPPT (η≈98%) → Bus DC 48 V → Onduleur sinus pur 3 kVA → Charge critique
                                            ↑
                              LiFePO4 14.3 kWh ‖ Supercaps 50 F
                                            ↑
                                    Eneo (appoint délesté)
```

### Choix de conception électrique justifiés

| Choix | Alternative rejetée | Justification |
|-------|--------------------|--------------  |
| Bus DC 48 V | 12 V / 24 V | À 2 kW, 12 V → 167 A (câbles énormes, pertes I²R). 48 V → 42 A, standard industriel, sûr. |
| Onduleur sinus pur | Pseudo-sinus | Le pseudo-sinus grille les alimentations à découpage et fausse les mesures AC. |
| Supercaps en parallèle batterie | Batterie seule | Une batterie seule ne répond pas en <2 s (chimie lente) → la micro-coupure passe. Les supercaps comblent ce trou temporel. |
| MPPT séparé de l'onduleur | Tout-en-un bas de gamme | Redondance et remplacement unitaire ; un hybride 5kVA de qualité (Growatt SPF 5000 ES) reste acceptable. |

### Protections (non négociables sous les orages camerounais)

- **Parafoudre DC** côté PV, **parafoudre AC** côté sortie.
- **Disjoncteur DC 63 A** par branche de stockage (batterie, supercaps).
- **Mise à la terre < 10 Ω** : équipotentialité de tous les châssis.
- **BMS 16S 200 A** avec équilibrage actif sur la batterie LiFePO4.

---

## 4. Plan de conception mécanique

![Plan mécanique](docs/images/02_plan_mecanique.png)

### Règles d'implantation physique

1. **La masse en bas** : la batterie LiFePO4 (≈ 80 kg pour 14.3 kWh) au niveau
   le plus bas — centre de gravité bas, stabilité, et conformité au flux
   thermique (l'air chaud monte, la batterie déteste la chaleur).
2. **L'électronique de puissance en haut et ventilée** : MPPT et onduleur
   dissipent des centaines de watts — ils vont en partie haute, face à la
   sortie d'air.
3. **Les supercaps près du bus DC** : liaison courte = faible résistance série
   = réponse rapide. Un supercondensateur au bout d'un long câble perd sa
   raison d'être.
4. **Le watchdog ESP32 en façade** : accessible, visible, déconnectable pour
   reprogrammation sans ouvrir la puissance.
5. **Goulottes séparées** : puissance (DC fort courant) et signal (capteurs,
   ESP32) ne partagent jamais la même goulotte — sinon le bruit électromagnétique
   perturbe la mesure.

### Ventilation

Flux d'air **bas → haut** : entrée fraîche en partie basse (avec filtre à
poussière, indispensable en saison sèche), extraction chaude en partie haute.
Objectif : maintenir la batterie sous 35 °C (au-delà, vieillissement Arrhenius
accéléré — voir §12).

---

## 5. L'appareil une fois monté

![Appareil monté](docs/images/03_appareil_monte.png)

L'armoire fermée présente en façade :
- **Afficheur OLED** : état de charge (SOC), puissance instantanée, statut P_sig
  (santé topologique du réseau).
- **3 voyants** : PV (production), BATT (état batterie), GRID (réseau Eneo).
- **Ventilation basse** filtrée.
- **Poignée + serrure** : l'accès à la puissance est réservé au technicien habilité.

C'est un appareil qui **s'installe dans un couloir de laboratoire**, pas une
salle machine — silencieux (pas de groupe électrogène), propre (pas de carburant),
autonome.

---

## 6. Le cœur logiciel

Le simulateur valide chaque configuration avant achat. Architecture des modules :

| Module | Rôle | Classe/fonction clé |
|--------|------|---------------------|
| `climate.py` | Production solaire réaliste (saison, nébulosité) | `solar_power_w()`, `daily_energy_wh()` |
| `eneo_model.py` | Modèle stochastique du réseau Eneo | `EnoGridProfile` |
| `perturbations.py` | Scénarios de dégradation du réseau | `get_scenario()` |
| `storage.py` | Modèles LiFePO4 et supercondensateurs | `LiFePO4Bank`, `SupercapBank` |
| `cpa.py` | Moteur de simulation du conditionneur | `CPA.run()` → `CPAResult` |
| `sizing.py` | Dimensionnement + contraintes + Monte Carlo | `evaluate()`, `monte_carlo()` |
| `topology.py` | Détection de fragilité par P_sig | `TopologicalWatchdog` |

### Le moteur de simulation (`CPA.run`)

Pas de temps de **1 seconde** sur 30+ jours. À chaque pas :
1. Le réseau Eneo est disponible ou en coupure (modèle stochastique).
2. Le PV produit selon l'heure, la saison, la nébulosité.
3. La charge suit un profil réaliste (40 % de base + rampe de journée).
4. L'énergie est arbitrée : PV direct → supercaps (transitoire) → batterie
   (endurance) → Eneo (appoint) → blackout si tout échoue.
5. On comptabilise disponibilité, cycles batterie, énergie non servie.

### Contraintes dures (`hard_constraints_ok`)

Avant toute simulation (rapide, exact) :
- **Autonomie supercaps** ≥ seuil minimal (absorber une micro-coupure).
- **Ratio PV/charge** ≥ 1.3 (le PV doit produire 30 % de plus que la consommation
  critique journalière pour recharger la batterie même les jours nuageux).

### Monte Carlo (`monte_carlo`)

100+ tirages avec des graines aléatoires différentes → **distribution** du taux
de disponibilité, pas une valeur unique optimiste. C'est ce qui distingue un
dimensionnement honnête d'un dimensionnement marketing.

---

## 7. La détection topologique P_sig

![P_sig](docs/images/05_psig_topologie.png)

C'est l'innovation méthodologique transverse à tout le projet RATISS. Au lieu de
surveiller le réseau par des seuils de tension (trop tardif), on surveille sa
**signature topologique** :

1. On plonge le signal de tension dans un espace de phase par **emboîtement de
   Takens** : `x(t) → (x(t), x(t+τ))`.
2. Un réseau sain trace un **cycle large et ouvert** (aire élevée).
3. Un réseau qui se fragilise voit son cycle **se contracter** (aire qui s'effondre).

Le `TopologicalWatchdog` calcule le ratio `P_sig / P_ref` en fenêtre glissante :
quand ce ratio passe sous 0.5, le réseau est structurellement malade — **avant**
que la tension ne s'effondre réellement. On déleste préventivement.

> 💡 C'est la même signature P_sig qu'on applique à la cohérence quantique dans
> le QPU (contraction du rayon de Bloch). **Une même idée topologique, deux
> échelles** — c'est la force transdisciplinaire du projet.

---

## 8. Guide de montage

> 📖 **Guide d'assemblage détaillé et exécutable → [docs/ASSEMBLY.md](docs/ASSEMBLY.md)**

Résumé des étapes (chaque détail, schéma unifilaire et procédure de réception
est dans `ASSEMBLY.md`) :

| Étape | Action critique | Vérification |
|-------|-----------------|--------------|
| 1 | Structure PV (inclinaison 10° Yaoundé / 5° Douala, face équateur) | Résistance au vent, Vmp×3 < Vmax MPPT |
| 2 | Mise à la terre (piquet < 10 Ω, équipotentialité) | Mesure à la barrette |
| 3 | Banc batterie 16S + BMS (serrage au couple, cosses serties) | Équilibrage BMS, polarité ×2 |
| 4 | Supercaps 48 V sur bus DC via disjoncteur dédié | Continuité, serrage |
| 5 | Conversion MPPT → bus → onduleur → tableau | Tension à vide avant fermeture |
| 6 | Protections (parafoudres DC/AC, disjoncteurs) | Déclenchement test |
| 7 | Watchdog ESP32 + capteurs | Lecture P_sig sur OLED |
| 8 | Mise sous tension progressive + test blackout | Commutation < 2 s invisible pour la charge |

**Ordre de connexion DC** : terre → négatif → positif. Disjoncteur OUVERT
jusqu'à la toute fin. Jamais de bijoux métalliques.

---

## 9. Itérations de conception

Le projet a convergé par itérations documentées :

### Itération 1 → 2 : le trou temporel des micro-coupures
- **Problème** : une batterie LiFePO4 seule laissait passer les micro-coupures
  (< 2 s) — sa chimie ne répond pas assez vite.
- **Solution** : ajout des supercondensateurs en parallèle comme **pont
  temporel**. C'est devenu un pilier de la conception.

### Itération 2 → 3 : le dimensionnement trop optimiste
- **Problème** : un dimensionnement "meilleur cas" sur le PV surestimait la
  disponibilité.
- **Solution** : Monte Carlo sur scénario Eneo **worst_case** + contrainte
  PV ≥ 1.3× charge critique. Résultat honnête, pas flatteur.

### Itération 3 → 4 : la surveillance par seuils arrive trop tard
- **Problème** : détecter une coupure quand la tension a déjà chuté, c'est
  subir le blackout avant de réagir.
- **Solution** : watchdog topologique P_sig (§7) — détection **préventive**
  de la fragilité structurelle.

### Itération 4 → 5 (Phase 0.5) : l'embarqué
- **Problème** : la simulation ne protège rien tant qu'elle n'est pas sur le
  terrain.
- **Solution** : firmware ESP32 (`firmware/main.py`) qui embarque le watchdog
  P_sig sur le matériel réel, avec capteurs ZMPT101B (tension) et INA219 (courant).

---

## 10. Validation et résultats

![Simulation](docs/images/04_simulation.png)

Sur la config **Standard** (7 jours, saison humide, scénario Eneo dégradé) :
- **Disponibilité globale ≈ 91.6 %** en charge critique garantie.
- **5 événements blackout** absorbés sans interruption visible pour la charge
  critique (grâce aux supercaps).
- **Répartition énergétique** : majoritairement solaire + appoint Eneo délesté.
- **Durée de vie batterie ≈ 7.8 ans** (modèle Arrhenius, cycles LiFePO4 ~6000).

> ⚠️ **Honnêteté** : ces chiffres sont des **simulations** issues du modèle,
> pas des mesures terrain. La Phase 0.5 (campagne Eneo réelle,
> `scripts/eneo_field_campaign.py`) recalibrera le modèle sur données mesurées.

---

## 11. Sécurité

| Danger | Mitigation |
|--------|-----------|
| Court-circuit batterie (>1000 A, arc violent) | Disjoncteurs DC 63 A par branche, ordre de connexion terre→négatif→positif, outils isolés |
| Surchauffe LiFePO4 | BMS avec coupure thermique, ventilation basse→haute, T < 35 °C |
| Foudre (saison des pluies) | Parafoudres DC + AC, terre < 10 Ω, équipotentialité |
| Choc électrique DC | 48 V choisi (sécurité extra-basse tension), jamais de travail sous tension |

**Le DC batterie ne pardonne pas.** Gants, lunettes, outils isolés, disjoncteur
ouvert pendant l'assemblage.

---

## 12. Maintenance

| Composant | Surveillance | Durée de vie attendue |
|-----------|-------------|----------------------|
| Panneaux PV | Nettoyage trimestriel (poussière saison sèche) | 25 ans |
| LiFePO4 | SOC via BMS, équilibrage annuel | ~6000 cycles / 8-10 ans |
| Supercaps | Tension d'équilibrage annuelle | >10 ans (pas de chimie) |
| Onduleur/MPPT | Ventilation, serrage annuel | 10 ans |
| ESP32 watchdog | Mise à jour firmware, calibration capteurs | remplaçable, faible coût |

Le supercondensateur est le composant le plus fiable du système (pas de réaction
chimique) — c'est pourquoi on lui confie le transitoire, la fonction la plus
sollicitée.

---

<div align="center">

**RATIS Labs · Cameroun** — *Toujours itérer, jamais figé. Prouver, pas prétendre.* 🦇⚡

![RATIS Labs](docs/images/06_logo_ratis_labs.png)

</div>
