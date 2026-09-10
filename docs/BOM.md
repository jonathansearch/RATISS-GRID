# 📦 BOM — Bill of Materials RATISS-GRID (config Standard 2 kW)

Tous les prix sont des **estimations FCFA** (TTC import, marge douane ~20 % incluse) sourçables Chine (Alibaba) / Dubaï (Deira) / local (Douala, Yaoundé). Les références sont des points de départ — valider la disponibilité et la contrefaçon avant commande (voir SOURCING.md). Taux indicatif : 1 USD ≈ 600 FCFA.

## ⚡ Production & conversion

| # | Composant | Référence type | Qté | PU (FCFA) | Total (FCFA) | Source |
|---|-----------|----------------|:---:|:---:|:---:|--------|
| 1 | Panneau PV monocristallin 550 Wc | Jinko Tiger / Longi Hi-MO 550M | 9 | 95 000 | 855 000 | Chine/Dubaï |
| 2 | Onduleur hybride sinus pur 5 kVA 48 V | Growatt SPF 5000 ES / Voltronic Axpert | 1 | 480 000 | 480 000 | Dubaï/local |
| 3 | Contrôleur MPPT 100 A (si onduleur non hybride) | Victron SmartSolar 150/100 ou clone Epever | 1 | 220 000 | 220 000 | Dubaï/local |
| 4 | Structure de montage PV (alu + visserie) | sur mesure, toiture ou sol | 1 | 180 000 | 180 000 | local (ENSPY) |

**Sous-total production : ~1 735 000 FCFA** (9 × 550 Wc = 4 950 Wc ≥ 4 500 Wc requis)

## 🔋 Stockage (cœur du coffre-fort)

| # | Composant | Référence type | Qté | PU (FCFA) | Total (FCFA) | Source |
|---|-----------|----------------|:---:|:---:|:---:|--------|
| 5 | Cellule LiFePO4 3.2 V 280 Ah | EVE LF280K (grade A, ~6000 cycles) | 16 | 55 000 | 880 000 | Chine (Alibaba) |
| 6 | BMS 16S 48 V 200 A (LiFePO4) | JBD / JK BMS avec équilibrage actif | 1 | 95 000 | 95 000 | Chine |
| 7 | Module supercondensateurs 48 V 50 F | 18× Maxwell BCAP0310 en série + équilibrage | 1 | 260 000 | 260 000 | Chine/Dubaï |
| 8 | Boîtier batterie + busbar cuivre + câblage 50 mm² | sur mesure | 1 | 120 000 | 120 000 | local |

**Sous-total stockage : ~1 355 000 FCFA** (16S × 280 Ah = 14.3 kWh ; supercaps 48 V 50 F)

## 🛡️ Protections & distribution (non négociables — orages)

| # | Composant | Référence type | Qté | PU (FCFA) | Total (FCFA) | Source |
|---|-----------|----------------|:---:|:---:|:---:|--------|
| 9 | Parafoudre DC (côté PV) type 1+2 | 1000 V DC, 40 kA | 1 | 45 000 | 45 000 | local/Dubaï |
| 10 | Parafoudre AC (tableau général) | type 1+2, 230 V, 40 kA | 1 | 40 000 | 40 000 | local |
| 11 | Disjoncteur DC 63 A (batterie) | courbe DC, pouvoir de coupure 10 kA | 2 | 18 000 | 36 000 | local |
| 12 | Disjoncteur AC 32 A (sortie onduleur) | courbe C | 2 | 12 000 | 24 000 | local |
| 13 | Sectionneur + fusibles PV 15 A | par string | 2 | 8 000 | 16 000 | local |
| 14 | Piquet de terre + câble 25 mm² + barrette | mise à la terre < 10 Ω | 1 | 55 000 | 55 000 | local |
| 15 | Tableau de distribution + coffret IP65 | 12 modules | 1 | 60 000 | 60 000 | local |

**Sous-total protections : ~276 000 FCFA** (la foudre est la 1re cause de mort des installations au Cameroun)

## 🧠 Supervision (recommandé — l'œil RATISS)

| # | Composant | Référence type | Qté | PU (FCFA) | Total (FCFA) | Source |
|---|-----------|----------------|:---:|:---:|:---:|--------|
| 16 | ESP32 + capteurs tension/courant (INA219, ZMPT101B) | kit supervision open-source | 1 | 35 000 | 35 000 | local/Dubaï |
| 17 | Écran + boîtier + alim | affichage SoC, P_sig, alertes | 1 | 25 000 | 25 000 | local |

**Sous-total supervision : ~60 000 FCFA** (fait tourner le TopologicalWatchdog en temps réel)

---

## 💰 TOTAL CONFIG STANDARD

| Poste | Montant (FCFA) |
|---|:---:|
| Production & conversion | 1 735 000 |
| Stockage | 1 355 000 |
| Protections & distribution | 276 000 |
| Supervision | 60 000 |
| Main d'œuvre assemblage local (ENSPY/AIMS) | ~400 000 |
| Imprévu (10 %) | ~380 000 |
| **TOTAL** | **≈ 4 200 000 FCFA** |

> Cible doctrine : 5–8 M FCFA → **tenu, avec marge**. La supervision ESP32 et l'assemblage local gardent la maintenance 100 % camerounaise.

## 📊 Récapitulatif des 3 configs

| Config | Charge pic | Charge critique garantie | PV | Batterie | Budget total |
|---|:---:|:---:|:---:|:---:|:---:|
| Minimal | 500 W | 500 W | 1 500 Wc | 7.2 kWh | ≈ 2 300 000 FCFA |
| **Standard** ⭐ | 2 000 W | 700 W | 4 500 Wc | 14.3 kWh | **≈ 4 200 000 FCFA** |
| Labo complet | 5 000 W | 1 500 W | 9 000 Wc | 28.7 kWh | ≈ 8 500 000 FCFA |
