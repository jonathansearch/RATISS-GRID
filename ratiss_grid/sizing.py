"""Solveur de dimensionnement RATISS-GRID.

Étant donnés : une charge critique moyenne (W), une durée de simulation (jours),
un scénario Eneo et une saison, trouve la configuration (PV, batterie, supercaps)
la moins chère atteignant l'objectif de disponibilité.

Contraintes physiques dures (jamais violées) :
- autonomie supercaps > 3× la plus longue micro-coupure (500 ms → on exige 2 s
  à pleine charge : marge de sécurité 4×, non négociable pour un QPU)
- DoD batterie ≤ 80 % (durée de vie LiFePO4)
- énergie journalière PV moyenne ≥ 1.3 × consommation journalière (marge
  nuages + dégradation)

Configurations de référence (docs/BOM.md) : Minimal 500 W, Standard 2 kW,
Labo 5 kW.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cpa import CPA, CPAResult
from .eneo_model import EnoGridProfile
from .perturbations import get_scenario
from .storage import LiFePO4Bank, SupercapBank

AVAILABILITY_TARGET = 0.999        # 99.9 % de continuité pour la charge critique
SUPERCAP_MIN_AUTONOMY_S = 2.0      # à pleine charge (4× la micro-coupure max)


@dataclass
class GridConfig:
    """Configuration du coffre-fort.

    load_w : puissance PIC de la charge critique (W). La charge moyenne
    journalière vaut ≈ 0.55 × load_w (base continue + pics de journée).
    critical_load_w : fraction de load_w garantie en autonomie solaire pure ;
    le reste (confort : postes de travail) est délestable sur Eneo. C'est la
    séparation critique/confort qui rend l'autonomie abordable — dimensionner
    2 kW en continu solaire pur exigerait ~15 kWc (irréaliste au budget).
    """
    name: str
    load_w: float
    pv_wp: float
    battery_kwh: float
    supercap_f: float
    budget_fcfa: int = 0
    critical_load_w: float = 0.0   # 0 → = load_w (tout est critique)


# Standard : pic 2 kW, mais seuls 700 W (QPU 500 + incubateur 150 + contrôle 50)
# sont garantis solaires 99.9 % ; les 1.3 kW de confort sont délestables.
# PV 4500 Wc → 4500 × 4.2 × 0.80 = 15.1 kWh/j ≥ 1.3 × (700×0.55×24 = 12.9 kWh). OK.
REFERENCE_CONFIGS = {
    "minimal":  GridConfig("Minimal",  500.0,  1500.0,  7.2, 50.0, 2_500_000),
    "standard": GridConfig("Standard", 2000.0, 4500.0, 14.3, 50.0, 6_500_000,
                           critical_load_w=700.0),
    "labo":     GridConfig("Labo complet", 5000.0, 9000.0, 28.7, 100.0, 13_000_000,
                           critical_load_w=1500.0),
}


def build_cpa(cfg: GridConfig, scenario: str = "worst_case") -> CPA:
    grid = get_scenario(scenario)
    return CPA(
        pv_wp=cfg.pv_wp,
        battery=LiFePO4Bank(capacity_kwh=cfg.battery_kwh),
        supercaps=SupercapBank(capacitance_f=cfg.supercap_f),
        grid=grid,
    )


def hard_constraints_ok(cfg: GridConfig) -> dict:
    """Vérifie les contraintes dures avant toute simulation (rapide, exact).

    Le dimensionnement PV porte sur la charge CRITIQUE garantie (pas le pic
    total) : c'est elle qui doit être autonome à 99.9 % en solaire pur.
    """
    sc = SupercapBank(capacitance_f=cfg.supercap_f)
    autonomy = sc.autonomy_s(cfg.load_w)
    crit = cfg.critical_load_w or cfg.load_w
    pv_daily_wh = cfg.pv_wp * 4.2 * 0.80       # GHI conservateur × PR
    load_daily_wh = crit * 0.55 * 24           # profil 40 % base + pics
    return {
        "supercap_autonomy_s": autonomy,
        "supercap_ok": autonomy >= SUPERCAP_MIN_AUTONOMY_S,
        "pv_load_ratio": pv_daily_wh / load_daily_wh,
        "pv_ok": pv_daily_wh >= 1.3 * load_daily_wh,
    }


def evaluate(cfg: GridConfig, days: float = 30.0, scenario: str = "worst_case",
             season: str = "wet", seed: int | None = None) -> CPAResult:
    cpa = build_cpa(cfg, scenario)
    if seed is not None:
        cpa.grid.rng = np.random.default_rng(seed)
    return cpa.run(days=days, load_w=cfg.load_w, season=season)


def monte_carlo(cfg: GridConfig, days: float = 30.0, n: int = 100,
                scenario: str = "worst_case", season: str = "wet",
                base_seed: int = 1000) -> dict:
    """N tirages Monte Carlo → distribution du taux de disponibilité."""
    avail = np.empty(n)
    blackouts = np.empty(n)
    for k in range(n):
        r = evaluate(cfg, days=days, scenario=scenario, season=season,
                     seed=base_seed + k)
        avail[k] = r.availability
        blackouts[k] = r.n_blackout_events
    return {
        "n": n,
        "availability_mean": float(avail.mean()),
        "availability_p05": float(np.percentile(avail, 5)),
        "availability_min": float(avail.min()),
        "target": AVAILABILITY_TARGET,
        "target_met_p05": bool(np.percentile(avail, 5) >= AVAILABILITY_TARGET),
        "blackout_events_mean": float(blackouts.mean()),
    }
