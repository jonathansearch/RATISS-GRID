"""Modèle du réseau public Eneo (Cameroun) comme source de perturbations.

Paramètres réalistes (documentés dans MEMO_GRID.md) :
- tension nominale 230 V / 50 Hz (norme camerounaise, héritage CEI)
- micro-coupures : 1 ms – 500 ms, plusieurs par jour en zone urbaine
- coupures longues (délestage) : 0.5 h – 8 h, fréquence accrue en saison sèche
- creux de tension : ±20 % autour du nominal (tolérance CEI ±10 % souvent dépassée)
- bruit harmonique THD : 5 – 15 % sur réseau chargé urbain

Toutes les grandeurs sont en unités SI : volt, seconde, watt, joule.
Le modèle est volontairement pessimiste (pire cas documenté) — règle RATISS :
mieux vaut surdimensionner en simulation que sous-dimensionner en cuivre.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

V_NOMINAL = 230.0          # V, tension nominale simple Cameroun
F_NOMINAL = 50.0           # Hz
TOL_CE_VOLTAGE = 0.10      # tolérance CEI ±10 % (souvent dépassée en pratique)
SAG_DEPTH_MAX = 0.20       # creux de tension jusqu'à -20 %
THD_URBAN_RANGE = (0.05, 0.15)  # distorsion harmonique totale, réseau urbain chargé


@dataclass
class EnoGridProfile:
    """Profil statistique d'un site raccordé Eneo.

    Attributs calibrés sur les ordres de grandeur documentés pour Yaoundé/Douala
    (voir MEMO_GRID.md). `severity` ∈ [0, 1] module la fréquence des défauts :
    0.3 = quartier résidentiel stable, 0.6 = zone urbaine moyenne,
    1.0 = zone très perturbée / délestage fréquent.
    """

    severity: float = 0.6
    micro_outages_per_day: tuple[float, float] = (2.0, 12.0)   # loi uniforme
    micro_outage_duration_s: tuple[float, float] = (0.001, 0.5)
    long_outages_per_month: tuple[float, float] = (2.0, 10.0)
    long_outage_duration_h: tuple[float, float] = (0.5, 8.0)
    sag_events_per_day: tuple[float, float] = (5.0, 30.0)
    rng: np.random.Generator = field(
        default_factory=lambda: np.random.default_rng(42), repr=False
    )

    def _uniform(self, bounds: tuple[float, float]) -> float:
        return float(self.rng.uniform(*bounds))

    def _count(self, per_day_bounds: tuple[float, float], days: float) -> int:
        """Nombre d'événements sur `days` jours (Poisson sur la moyenne)."""
        lam = np.mean(per_day_bounds) * self.severity * days
        return int(self.rng.poisson(lam))

    def generate(self, days: float = 30.0, dt_s: float = 1.0) -> dict:
        """Génère une série temporelle de tension Eneo sur `days` jours.

        Retourne un dict :
          t_s         : temps (s)
          v_pu        : tension en par-unité (1.0 = 230 V, 0.0 = coupure)
          available   : booléen, réseau présent (True) ou coupé (False)
          events      : liste des événements {type, t_start_s, duration_s, depth}
        """
        n = int(days * 86400.0 / dt_s)
        t = np.arange(n) * dt_s
        v_pu = np.ones(n)
        available = np.ones(n, dtype=bool)
        events: list[dict] = []

        # Bruit de fond : fluctuations lentes ±5 % + bruit rapide ±1 %
        slow = 0.05 * np.sin(2 * np.pi * t / 86400.0 + self.rng.uniform(0, 2 * np.pi))
        fast = self.rng.normal(0.0, 0.01, n)
        v_pu += slow + fast

        # Micro-coupures
        for _ in range(self._count(self.micro_outages_per_day, days)):
            i0 = int(self.rng.uniform(0, n - 1))
            dur = self._uniform(self.micro_outage_duration_s)
            k = max(1, int(dur / dt_s))
            i1 = min(n, i0 + k)
            v_pu[i0:i1] = 0.0
            available[i0:i1] = False
            events.append({"type": "micro_outage", "t_start_s": float(t[i0]),
                           "duration_s": dur, "depth": 1.0})

        # Coupures longues (délestage) — fréquence mensuelle → ramenée au jour
        n_long = self._count(tuple(b / 30.0 for b in self.long_outages_per_month), days)
        for _ in range(n_long):
            i0 = int(self.rng.uniform(0, n - 1))
            dur = self._uniform(self.long_outage_duration_h) * 3600.0
            k = max(1, int(dur / dt_s))
            i1 = min(n, i0 + k)
            v_pu[i0:i1] = 0.0
            available[i0:i1] = False
            events.append({"type": "long_outage", "t_start_s": float(t[i0]),
                           "duration_s": dur, "depth": 1.0})

        # Creux de tension (réseau présent mais dégradé)
        for _ in range(self._count(self.sag_events_per_day, days)):
            i0 = int(self.rng.uniform(0, n - 1))
            dur = self._uniform((0.02, 2.0))
            depth = self._uniform((TOL_CE_VOLTAGE, SAG_DEPTH_MAX))
            k = max(1, int(dur / dt_s))
            i1 = min(n, i0 + k)
            v_pu[i0:i1] -= depth
            events.append({"type": "sag", "t_start_s": float(t[i0]),
                           "duration_s": dur, "depth": depth})

        v_pu = np.clip(v_pu, 0.0, 1.2)
        return {"t_s": t, "v_pu": v_pu, "available": available, "events": events}

    def availability(self, days: float = 30.0, samples: int = 20) -> tuple[float, float]:
        """Disponibilité moyenne ± écart-type sur `samples` tirages (fraction)."""
        vals = []
        for _ in range(samples):
            out = self.generate(days=days, dt_s=10.0)
            vals.append(float(out["available"].mean()))
        return float(np.mean(vals)), float(np.std(vals))
