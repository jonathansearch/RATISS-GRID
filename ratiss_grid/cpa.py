"""Conditionneur de Puissance Actif (CPA) — la simulation complète.

Chaîne : PV → MPPT → bus DC 48 V [LiFePO4 ‖ Supercaps] → onduleur sinus pur → charge.

Logique de commande (loi figée, simple et auditable) :
1. Le PV alimente la charge en priorité ; le surplus charge batterie puis supercaps.
2. Si Eneo est présent et sain (watchdog topologique OK), il peut aider à recharger
   la batterie via un chargeur AC/DC — appoint, jamais dépendance.
3. Coupure < T_SWITCH (500 ms) : les supercaps seuls tiennent la charge
   (réponse < 10 ms, aucune commutation mécanique).
4. Au-delà : la batterie prend le relais via le bus DC (les supercaps se
   rechargent ensuite depuis la batterie à puissance limitée).
5. Si tout est épuisé → black-out de la charge critique (comptabilisé).

Sortie : bilan énergétique complet + taux de disponibilité de la charge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .climate import solar_power_w
from .eneo_model import EnoGridProfile
from .storage import LiFePO4Bank, SupercapBank

T_SWITCH_S = 0.5          # seuil de bascule supercaps → batterie
ETA_INVERTER = 0.92       # onduleur sinus pur haute fréquence (datasheet 90–94 %)
ETA_MPPT = 0.97           # contrôleur MPPT (Victron : 96–98 %)
P_ACDC_CHARGER_W = 1000.0 # chargeur AC/DC d'appoint quand Eneo revient


@dataclass
class CPAResult:
    days: float
    load_w: float
    energy_load_wh: float
    energy_pv_wh: float
    energy_eneo_wh: float
    unserved_wh: float          # énergie non fournie à la charge critique
    availability: float         # fraction du temps où la charge est alimentée
    n_blackout_events: int
    battery_cycles: float       # cycles équivalents complets sur la période
    battery_life_years: float   # extrapolation Arrhenius
    per_day_availability: list[float] = field(default_factory=list)


@dataclass
class CPA:
    pv_wp: float = 3000.0
    battery: LiFePO4Bank = field(default_factory=LiFePO4Bank)
    supercaps: SupercapBank = field(default_factory=SupercapBank)
    grid: EnoGridProfile = field(default_factory=EnoGridProfile)

    def run(self, days: float = 30.0, load_w: float = 2000.0,
            season: str = "wet", dt_s: float = 1.0,
            eneo_assist: bool = True) -> CPAResult:
        """Simule le CPA sur `days` jours, pas de `dt_s` secondes.

        `load_w` est la puissance moyenne de la charge critique (profil
        journalier réaliste : base 40 % + pic de journée, voir ci-dessous).
        """
        n = int(days * 86400.0 / dt_s)
        grid_out = self.grid.generate(days=days, dt_s=dt_s)
        t = grid_out["t_s"]
        available = grid_out["available"]
        pv = solar_power_w(self.pv_wp, t, season=season) * ETA_MPPT

        # Profil de charge : 40 % de base permanent (QPU, contrôle) +
        # rampe de journée (8h–20h) jusqu'à 100 % (postes de travail, wetlab)
        hours = (t / 3600.0) % 24.0
        day_load = np.clip((hours - 8.0) / 2.0, 0.0, 1.0) * np.clip((20.0 - hours) / 2.0, 0.0, 1.0)
        day_load = day_load / max(day_load.max(), 1e-9)
        load = load_w * (0.4 + 0.6 * day_load)

        served = np.zeros(n)
        e_pv = e_eneo = 0.0
        blackout_events = 0
        in_blackout = False
        bat_cum_discharge_j = 0.0

        # État de coupure courante (durée depuis le début de la coupure)
        outage_t = 0.0

        for i in range(n):
            dt = dt_s
            p_load_dc = load[i] / ETA_INVERTER     # puissance côté bus DC
            p_pv = pv[i]

            if available[i]:
                outage_t = 0.0
            else:
                outage_t += dt

            # 1. PV direct vers la charge
            from_pv = min(p_pv, p_load_dc)
            remaining = p_load_dc - from_pv
            surplus = p_pv - from_pv

            # 2. Déficit : supercaps d'abord (coupures courtes), batterie ensuite
            e_sc = self.supercaps.discharge(remaining, dt)
            remaining_j = remaining * dt - e_sc
            e_bat = 0.0
            if remaining_j > 0:
                e_bat = self.battery.discharge(remaining_j / dt, dt)
                bat_cum_discharge_j += e_bat
                remaining_j -= e_bat

            served_j = from_pv * dt + e_sc + e_bat
            served[i] = served_j / max(p_load_dc * dt, 1e-12)

            if remaining_j > 1e-6:
                if not in_blackout:
                    blackout_events += 1
                    in_blackout = True
            else:
                in_blackout = False

            # 3. Surplus PV : batterie puis supercaps
            if surplus > 0:
                e_in = self.battery.charge(surplus, dt)
                rest = surplus * dt - e_in
                if rest > 0:
                    self.supercaps.charge(rest / dt, dt)
            e_pv += from_pv * dt

            # 4. Appoint Eneo : recharge batterie si SoC bas et réseau présent
            if eneo_assist and available[i] and self.battery.soc < 0.5:
                e_in = self.battery.charge(P_ACDC_CHARGER_W, dt)
                e_eneo += e_in / ETA_INVERTER

            # 5. Les supercaps se rechargent depuis la batterie (puissance limitée)
            if self.supercaps.v < self.supercaps.v_max * 0.9 and self.battery.soc > 0.3:
                e_move = self.battery.discharge(500.0, dt)   # 500 W de recharge
                self.supercaps.charge(e_move / dt, dt)

        e_load_wh = float(load.sum() * dt_s / 3600.0)
        e_served_wh = float((served * load).sum() * dt_s / 3600.0)
        cycles = bat_cum_discharge_j / max(self.battery.usable_kwh * 3.6e6, 1.0)
        cycles_per_day = cycles / max(days, 1e-9)

        per_day = []
        n_per_day = int(86400.0 / dt_s)
        for d in range(int(days)):
            seg = served[d * n_per_day:(d + 1) * n_per_day]
            per_day.append(float(seg.mean()) if len(seg) else 0.0)

        return CPAResult(
            days=days,
            load_w=load_w,
            energy_load_wh=e_load_wh,
            energy_pv_wh=e_pv / 3600.0,
            energy_eneo_wh=e_eneo / 3600.0,
            unserved_wh=e_load_wh - e_served_wh,
            availability=float(served.mean()),
            n_blackout_events=blackout_events,
            battery_cycles=float(cycles),
            battery_life_years=self.battery.cycle_life_years(cycles_per_day),
            per_day_availability=per_day,
        )
