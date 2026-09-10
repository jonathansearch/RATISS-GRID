# 🧭 MEMO_GRID — État d'avancement RATISS-GRID (Priorité 0)

Mémo de session (style MEMO_KTN_LI). Ce fichier est LA source de vérité sur où
on en est, ce qui marche, et ce qui reste. **Jamais figé, toujours itérer.**

## ✅ ÉTAT ACTUEL (Phase 0 — simulation validée)
- [x] Dépôt créé : `samajonathan9-source/ratiss-grid`
- [x] Modèle réseau Eneo (`eneo_model.py`) — micro-coupures, délestage, creux, THD
- [x] Signature topologique (`topology.py`) — détecteur P_sig par aire de cycle de Takens
- [x] Stockage (`storage.py`) — LiFePO4 (Arrhenius) + supercaps (E=½CV²)
- [x] Climat tropical (`climate.py`) — GHI 4.2 kWh/m²/j, coef -0.35 %/°C, soiling
- [x] CPA complet (`cpa.py`) — PV→MPPT→[batt‖supercaps]→onduleur→charge
- [x] Solveur dimensionnement (`sizing.py`) — 3 configs + contraintes dures
- [x] CLI (`size_my_grid.py`) — `python -m ratiss_grid.size_my_grid --load 2000 --days 30`
- [x] Tests internes : **18/18 verts** (`pytest tests/ -q`)
- [x] BOM chiffrée FCFA (`docs/BOM.md`) — Standard ≈ 4.2 M FCFA
- [x] Sourcing (`docs/SOURCING.md`) — Chine/Dubaï/local, pièges douane
- [x] Assemblage (`docs/ASSEMBLY.md`) — schéma unifilaire + tests T1–T10
- [x] Maintenance (`docs/MAINTENANCE.md`) — 100 % locale
- [x] **Affinement Phase 0.5** : firmware ESP32 (`firmware/main.py`) avec
      TopologicalWatchdog embarqué + script campagne mesure Eneo
      (`scripts/eneo_field_campaign.py`) pour recalibrer sur données réelles

## 📐 DÉCISIONS D'INGÉNIERIE CLÉS (ne pas ré-ouvrir sans raison)
1. **Séparation critique/confort** : on ne dimensionne PAS 2 kW en continu solaire
   pur (~15 kWc, irréaliste). On garantit 99.9 % sur la **charge critique 700 W**
   (QPU 500 + incubateur 150 + contrôle 50) ; le confort (1.3 kW) est délestable.
   C'est LA décision qui rend l'autonomie abordable.
2. **Supercaps AVANT batterie** : réponse < 10 ms pour les micro-coupures ≤ 500 ms,
   sans commutation mécanique. Autonomie supercaps à pleine charge = 20 s (config
   Standard) >> seuil dur de 2 s.
3. **P_sig = aire de cycle de Takens (m=2)**, PAS H1 Vietoris-Rips exact : le H1
   naïf donne un score PLUS élevé au bruit blanc (cycles persistants à grande
   échelle) → inversé, inutilisable. L'aire de cycle est robuste, O(N), honnête.
4. **Conservation d'énergie** : `discharge()` délivre ≤ P·dt, les pertes sont
   portées par le SoC (η=0.95 à charge et décharge). Vérifié par test.

## ⚠️ LIMITES HONNÊTES (à ne jamais oublier)
- Disponibilité 99.9 % garantie sur la **charge critique 700 W**, pas sur le pic
  2 kW. Sur worst_case 30 j à pleine charge 2 kW continue, la disponibilité
  totale tombe (le confort est délesté). C'est voulu et documenté.
- Tous les chiffres climat/Eneo sont des **ordres de grandeur documentés**, pas
  des mesures terrain. La calibration absolue exige le prototype physique +
  campagne de mesure (enregistreur de tension sur site, 30 j).
- Le P_sig est validé en simulation sur signaux synthétiques. Son pouvoir
  prédictif réel sur Eneo doit être mesuré sur le prototype.

## 🔜 PROCHAINES ÉTAPES (Phase 0.5 → physique)
1. **Commander un échantillon** de cellule EVE LF280K + tester la capacité réelle.
2. **Campagne de mesure Eneo** : enregistreur de tension 30 j sur site cible →
   recalibrer `EnoGridProfile` sur données réelles.
3. **Prototype Minimal (500 W)** d'abord : valider T1–T10 sur banc réel.
4. ~~Firmware ESP32~~ ✅ fait (`firmware/main.py`) — reste à flasher et calibrer.
5. Soumettre BOM Standard à ENSPY/AIMS pour devis d'assemblage.

## 📌 RÈGLES DE SESSION (conseil de Jonathan)
- Jamais figé, toujours itérer. Si un composant est indisponible, on remplace
  par une référence équivalente documentée et on relance la simu.
- Ne jamais prétendre un résultat non mesuré — documenter les échecs.
- Chaque chiffre de la BOM/sizing doit pouvoir être justifié par une datasheet
  ou une source. Pas de nombre magique.

---
*Priorité 0 sur 4. Ensuite : QPU non-cryogénique (Priorité 1).*
