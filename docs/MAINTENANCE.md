# 🛠️ MAINTENANCE — RATISS-GRID (maintenance 100 % locale)

Objectif : le système doit être réparable par un technicien camerounais avec
des pièces trouvées à Douala/Yaoundé. Pas de dépendance à un SAV étranger.

## 📅 Calendrier préventif

| Fréquence | Action | Outil |
|---|---|---|
| Mensuel | Nettoyage panneaux (poussière/Harmattan) | eau + balai doux |
| Mensuel | Vérification visuelle cosses/câbles (échauffement) | œil + thermomètre IR |
| Trimestriel | Relevé SoC, tension cellules, P_sig moyen | supervision ESP32 |
| Trimestriel | Test de délestage simulé (couper Eneo) | interrupteur |
| Semestriel | Resserage connexions DC (couple) | clé dynamométrique |
| Annuel | Test de capacité batterie (décharge contrôlée) | testeur / charge connue |
| Annuel | Mesure de terre | telluromètre |

## 🔩 Pièces d'usure (stock local recommandé)
- Fusibles PV 15 A (×4), disjoncteur DC 63 A (×1), cosses et câble 50 mm² (5 m).
- 1 cellule LiFePO4 280 Ah de rechange (remplacement à l'unité possible).
- 1 carte BMS de rechange, 1 ESP32 de rechange, connecteurs MC4 (×10).

## 🩺 Diagnostic rapide (panne → cause probable)

| Symptôme | Cause probable | Action |
|---|---|---|
| Charge critique coupée | SoC batterie < 20 % + pas de soleil | vérifier appoint Eneo, réduire confort |
| P_sig effondré en continu | réseau Eneo très dégradé ou capteur | vérifier tension réelle au multimètre |
| BMS en défaut | cellule déséquilibrée ou HS | mesurer chaque cellule, remplacer si < 2.5 V |
| Onduleur en alarme | surcharge ou surchauffe | réduire charge, vérifier ventilation |
| Production PV faible | salissure ou string coupé | nettoyer, vérifier fusibles string |
| Parafoudre DC claqué (voyant rouge) | coup de foudre proche | remplacer la cartouche parafoudre |

## 🎓 Formation & transmission
Former au moins 2 techniciens locaux à : lecture du schéma unifilaire, mesure
de terre, remplacement cellule, réinitialisation BMS, lecture du P_sig. Toute
intervention est consignée dans un cahier de maintenance (date, symptôme,
action, pièce). La connaissance reste au Cameroun.
