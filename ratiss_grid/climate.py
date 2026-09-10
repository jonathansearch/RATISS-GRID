"""Climat tropical camerounais : soleil, chaleur, humidité, poussière.

Sources des paramètres (voir MEMO_GRID.md) :
- Irradiation Yaoundé/Douala : GHI ≈ 4.0–4.8 kWh/m²/jour en moyenne annuelle
  (Global Solar Atlas, données Solargis/World Bank). On prend 4.2 (conservateur).
- Coefficient de température des cellules mono PERC : -0.35 %/°C (datasheets
  Jinko Tiger / Longi Hi-MO : -0.34 à -0.36 %/°C sur Pmax).
- Température de cellule : T_cell = T_amb + G/800 × (NOCT − 20), NOCT ≈ 45 °C.
- Pertes poussière/humidité (soiling) : 3–8 % sans nettoyage ; on prend 5 %
  avec nettoyage mensuel, 8 % en saison sèche (Harmattan poussiéreux).
"""

from __future__ import annotations

import numpy as np

GHI_KWH_M2_DAY = 4.2          # moyenne annuelle conservatrice Cameroun
TEMP_COEFF_PMAX = -0.0035     # /°C, mono PERC (datasheet)
NOCT_C = 45.0                 # °C, nominal operating cell temperature
SOILING_WET = 0.05            # pertes poussière saison des pluies
SOILING_DRY = 0.08            # pertes poussière saison sèche


def solar_power_w(pv_wp: float, t_s: np.ndarray, season: str = "wet",
                  t_amb_c: float = 30.0) -> np.ndarray:
    """Puissance PV (W) d'un champ de `pv_wp` watts-crête, pas de 1 s.

    Profil journalier : demi-sinus entre 6h et 18h, crête à midi solaire,
    modulé par un facteur de nébulosité aléatoire journalier (0.3–1.0)
    et par les pertes thermiques + poussière.
    """
    hours = (t_s / 3600.0) % 24.0
    day_index = (t_s / 86400.0).astype(int)
    rng = np.random.default_rng(1234)
    n_days = int(day_index.max()) + 1 if len(day_index) else 1
    cloud = rng.uniform(0.3, 1.0, n_days)
    cloud_factor = cloud[day_index]

    # Profil demi-sinusoïdal : P = Pmax · sin(π (h−6)/12) pour 6h < h < 18h
    day_frac = np.clip((hours - 6.0) / 12.0, 0.0, 1.0)
    shape = np.sin(np.pi * day_frac) ** 2
    shape[(hours < 6.0) | (hours > 18.0)] = 0.0

    # Puissance instantanée moyenne calée pour produire GHI_KWH_M2_DAY
    # par m² en moyenne : ∫ shape dt sur un jour ≈ 5.4 h équivalent plein soleil.
    # Irradiance instantanée moyenne ≈ 4.2 kWh / 5.4 h ≈ 780 W/m² crête moyenne.
    g_inst = 780.0 * shape * cloud_factor          # W/m²

    # Correction thermique : T_cell puis déclassement de Pmax
    t_cell = t_amb_c + g_inst / 800.0 * (NOCT_C - 20.0)
    thermal = 1.0 + TEMP_COEFF_PMAX * (t_cell - 25.0)

    soiling = SOILING_DRY if season == "dry" else SOILING_WET
    return pv_wp * (g_inst / 1000.0) * thermal * (1.0 - soiling)


def daily_energy_wh(pv_wp: float, days: int = 30, season: str = "wet",
                    seed: int = 1234) -> np.ndarray:
    """Énergie journalière (Wh) produite par le champ PV, jour par jour."""
    rng = np.random.default_rng(seed)
    t = np.arange(days * 86400, dtype=float)
    # Re-génération déterministe par jour via solar_power_w coûteuse →
    # approximation analytique : E = GHI_corr × P_wp × PR
    soiling = SOILING_DRY if season == "dry" else SOILING_WET
    pr = (1.0 - soiling) * 0.85   # performance ratio (onduleur, câbles, MPPT)
    cloud = rng.uniform(0.3, 1.0, days)
    return pv_wp * GHI_KWH_M2_DAY * cloud * pr * 1.0  # Wh/jour (GHI en kWh/m²)
