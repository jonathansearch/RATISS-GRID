"""Dynamique de stockage : LiFePO4 + supercondensateurs (physique réelle).

Sources des paramètres (voir docs/BOM.md) :
- Cellule LiFePO4 EVE LF280K : 3.2 V nominal, 280 Ah, ~6000 cycles à 80 % DoD,
  rendement faradique ≈ 0.97, résistance interne ≤ 0.25 mΩ (datasheet EVE).
- Supercondensateur Maxwell BCAP0310 (2.7 V, 310 F) ou module 48 V :
  ESR ~2.2 mΩ/cellule, rendement ≥ 0.95, durée de vie > 10^6 cycles,
  temps de réponse < 10 ms — c'est lui qui absorbe les micro-coupures.

Modèles :
- Batterie : intégrateur d'énergie + loi d'Arrhenius de vieillissement
  accéléré par la chaleur (climat tropical, climate.py).
- Supercaps : circuit RC série équivalent, énergie E = ½ C V².

Unités SI partout : joule, watt, seconde, volt, kelvin.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

R_GAS = 8.314            # J/(mol·K), constante des gaz parfaits
T_REF = 298.15           # K (25 °C), température de référence datasheet


@dataclass
class LiFePO4Bank:
    """Banc batterie LiFePO4 (ex : 16 cellules EVE LF280K en série = 51.2 V).

    capacity_kwh : capacité nominale totale du banc (kWh)
    dod_max      : profondeur de décharge maximale autorisée (0.8 = 80 %)
    eta_roundtrip: rendement aller-retour (0.95 typique avec BMS + câblage)
    """

    capacity_kwh: float = 14.3      # 16S × 280 Ah × 3.2 V = 14.336 kWh
    dod_max: float = 0.80
    eta_roundtrip: float = 0.95
    soc: float = 0.8                # état de charge initial (fraction)

    @property
    def usable_kwh(self) -> float:
        return self.capacity_kwh * self.dod_max

    @property
    def energy_j(self) -> float:
        """Énergie actuellement disponible au-dessus du plancher DoD."""
        floor = 1.0 - self.dod_max
        return max(0.0, (self.soc - floor)) * self.capacity_kwh * 3.6e6

    def discharge(self, power_w: float, dt_s: float) -> float:
        """Décharge à `power_w` moyen pendant `dt_s`. Retourne l'énergie (J)
        réellement délivrée DANS CE PAS — bornée par power_w × dt_s et par la
        réserve DoD. Zéro si la réserve est épuisée (jamais de magie)."""
        if power_w <= 0:
            return 0.0
        eta = self.eta_roundtrip            # pertes à la décharge
        e_deliverable = self.energy_j * eta
        e_out = min(power_w * dt_s, e_deliverable)
        self.soc -= (e_out / eta) / (self.capacity_kwh * 3.6e6)
        return float(e_out)

    def charge(self, power_w: float, dt_s: float) -> float:
        """Charge à `power_w` moyen pendant `dt_s`. Retourne l'énergie (J)
        réellement stockée DANS CE PAS — bornée par power_w × dt_s et par la
        place restante jusqu'à 100 % SoC."""
        if power_w <= 0 or self.soc >= 1.0:
            return 0.0
        eta = self.eta_roundtrip            # pertes à la charge
        headroom_j = (1.0 - self.soc) * self.capacity_kwh * 3.6e6
        e_in = min(power_w * dt_s * eta, headroom_j)
        self.soc += e_in / (self.capacity_kwh * 3.6e6)
        return float(e_in)

    def cycle_life_years(self, cycles_per_day: float, t_kelvin: float = 308.15,
                         cycles_ref: int = 6000) -> float:
        """Durée de vie estimée en années (Arrhenius, Ea ≈ 25 kJ/mol).

        À 35 °C (308 K) vs 25 °C de référence datasheet, le facteur
        d'accélération est ≈ 1.5 — la chaleur tropicale coûte ~1/3 de la vie.
        """
        ea = 25_000.0
        accel = np.exp(ea / R_GAS * (1.0 / T_REF - 1.0 / t_kelvin))
        cycles_available = cycles_ref / accel
        if cycles_per_day <= 0:
            return float("inf")
        return float(cycles_available / (cycles_per_day * 365.25))


@dataclass
class SupercapBank:
    """Banc supercondensateurs (ex : module 48 V à base de Maxwell BCAP).

    capacitance_f : capacité équivalente du banc (F)
    v_max, v_min  : plage de tension utile (l'énergie récupérable est
                    ½ C (Vmax² − Vmin²) — on ne descend pas sous Vmin car
                    le convertisseur DC/DC exige une tension d'entrée minimale)
    """

    capacitance_f: float = 50.0     # banc 48 V ≈ 50 F (ex : 18× BCAP0310 série)
    v_max: float = 48.0
    v_min: float = 24.0             # seuil bas du DC/DC
    eta: float = 0.95
    v: float = 48.0

    @property
    def energy_j(self) -> float:
        return 0.5 * self.capacitance_f * max(0.0, self.v ** 2 - self.v_min ** 2)

    @property
    def energy_max_j(self) -> float:
        return 0.5 * self.capacitance_f * (self.v_max ** 2 - self.v_min ** 2)

    def discharge(self, power_w: float, dt_s: float) -> float:
        """Fournit `power_w` pendant `dt_s` (réponse < 10 ms, pas de limite
        chimique). Retourne l'énergie réellement fournie (J)."""
        if power_w <= 0:
            return 0.0
        e_req = power_w * dt_s / self.eta
        e_out = min(e_req, self.energy_j)
        v2 = self.v ** 2 - 2.0 * e_out / self.capacitance_f
        self.v = float(np.sqrt(max(self.v_min ** 2, v2)))
        return float(e_out * self.eta)

    def charge(self, power_w: float, dt_s: float) -> float:
        if power_w <= 0 or self.v >= self.v_max:
            return 0.0
        e_in = min(power_w * dt_s * self.eta, self.energy_max_j - self.energy_j)
        v2 = self.v ** 2 + 2.0 * e_in / self.capacitance_f
        self.v = float(min(self.v_max, np.sqrt(v2)))
        return float(e_in)

    def autonomy_s(self, power_w: float) -> float:
        """Autonomie en secondes à puissance constante — c'est LE chiffre qui
        doit dépasser la plus longue micro-coupure (500 ms) avec marge."""
        return float(self.energy_j * self.eta / max(power_w, 1e-9))
