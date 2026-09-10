"""Bibliothèque de scénarios de défauts réalistes pour tests du CPA.

Chaque scénario retourne un profil `EnoGridProfile` pré-calibré.
Règle RATISS : chaque scénario documente son inspiration réelle et ses
ordres de grandeur ; aucun n'est prétendu mesuré sur site tant que la
campagne de mesure physique n'a pas eu lieu (voir MEMO_GRID.md).
"""

from __future__ import annotations

from .eneo_model import EnoGridProfile

SCENARIOS: dict[str, dict] = {
    # Quartier résidentiel Yaoundé en saison des pluies : réseau correct,
    # orages quotidiens → micro-coupures fréquentes, rares coupures longues.
    "yaounde_pluies": dict(
        severity=0.4,
        micro_outages_per_day=(3.0, 8.0),
        micro_outage_duration_s=(0.001, 0.3),
        long_outages_per_month=(1.0, 3.0),
        long_outage_duration_h=(0.5, 3.0),
        sag_events_per_day=(8.0, 20.0),
    ),
    # Douala zone industrielle, saison sèche : délestage planifié,
    # coupures longues quotidiennes possibles, THD élevé (charges non linéaires).
    "douala_seche": dict(
        severity=0.9,
        micro_outages_per_day=(5.0, 15.0),
        micro_outage_duration_s=(0.01, 0.5),
        long_outages_per_month=(6.0, 15.0),
        long_outage_duration_h=(1.0, 8.0),
        sag_events_per_day=(15.0, 40.0),
    ),
    # Zone semi-urbaine (Limbé, Bafoussam) : intermédiaire.
    "semi_urbain": dict(
        severity=0.6,
        micro_outages_per_day=(2.0, 10.0),
        micro_outage_duration_s=(0.001, 0.5),
        long_outages_per_month=(2.0, 8.0),
        long_outage_duration_h=(0.5, 6.0),
        sag_events_per_day=(5.0, 25.0),
    ),
    # Pire cas de référence pour le dimensionnement : on dimensionne sur lui.
    "worst_case": dict(
        severity=1.0,
        micro_outages_per_day=(10.0, 20.0),
        micro_outage_duration_s=(0.05, 0.5),
        long_outages_per_month=(10.0, 20.0),
        long_outage_duration_h=(2.0, 8.0),
        sag_events_per_day=(30.0, 60.0),
    ),
}


def get_scenario(name: str) -> EnoGridProfile:
    """Retourne un profil Eneo calibré sur le scénario demandé."""
    if name not in SCENARIOS:
        raise KeyError(f"scénario inconnu : {name!r} — disponibles : {list(SCENARIOS)}")
    return EnoGridProfile(**SCENARIOS[name])
