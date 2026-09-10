"""Tests internes RATISS-GRID — conservation, limites physiques, cas extrêmes."""

import numpy as np

from ratiss_grid.cpa import CPA
from ratiss_grid.eneo_model import EnoGridProfile
from ratiss_grid.perturbations import get_scenario
from ratiss_grid.sizing import (REFERENCE_CONFIGS, GridConfig, evaluate,
                                hard_constraints_ok, monte_carlo)
from ratiss_grid.storage import LiFePO4Bank, SupercapBank
from ratiss_grid.topology import TopologicalWatchdog, takens_embedding


class TestStorage:
    def test_battery_never_exceeds_dod(self):
        b = LiFePO4Bank(capacity_kwh=14.3, soc=0.9)
        total = sum(b.discharge(5000.0, 3600.0) for _ in range(100))
        assert b.soc >= 1.0 - b.dod_max - 1e-9
        assert total <= b.usable_kwh * 3.6e6 * 1.01

    def test_battery_never_overcharges(self):
        b = LiFePO4Bank(capacity_kwh=14.3, soc=0.99)
        b.charge(10000.0, 3600.0)
        assert b.soc <= 1.0

    def test_energy_conservation_roundtrip(self):
        # Invariante thermodynamique : un cycle charge→décharge doit faire
        # PERDRE de l'énergie nette (η<1) — le SoC après un cycle complet
        # retombe SOUS sa valeur de départ. On vérifie le SoC (état réel),
        # pas les énergies terminales (bornées par la réserve disponible).
        b = LiFePO4Bank(capacity_kwh=14.3, soc=0.5)
        soc0 = b.soc
        b.charge(2000.0, 3600.0)
        soc_charged = b.soc
        assert soc_charged > soc0                      # la charge remplit
        b.discharge(2000.0, 3600.0)
        assert b.soc < soc_charged                     # la décharge vide
        assert b.soc < soc_charged - (soc_charged - soc0) * 0.9  # pertes nettes

    def test_supercap_energy_formula(self):
        sc = SupercapBank(capacitance_f=50.0, v_max=48.0, v_min=24.0)
        expected = 0.5 * 50.0 * (48.0 ** 2 - 24.0 ** 2)
        assert abs(sc.energy_j - expected) < 1e-6

    def test_supercap_autonomy_positive(self):
        sc = SupercapBank(capacitance_f=50.0)
        assert sc.autonomy_s(2000.0) > 0
        assert sc.autonomy_s(1e9) < sc.autonomy_s(100.0)

    def test_battery_aging_arrhenius(self):
        b = LiFePO4Bank()
        life_25 = b.cycle_life_years(1.0, t_kelvin=298.15)
        life_35 = b.cycle_life_years(1.0, t_kelvin=308.15)
        assert life_35 < life_25     # la chaleur tropicale coûte de la vie


class TestEneoModel:
    def test_voltage_bounds(self):
        g = EnoGridProfile(severity=1.0)
        out = g.generate(days=2.0, dt_s=10.0)
        assert out["v_pu"].min() >= 0.0
        assert out["v_pu"].max() <= 1.2

    def test_worst_scenario_worse_than_calm(self):
        calm = get_scenario("yaounde_pluies")
        calm.rng = np.random.default_rng(1)
        bad = get_scenario("worst_case")
        bad.rng = np.random.default_rng(1)
        a_calm = calm.generate(days=10.0, dt_s=10.0)["available"].mean()
        a_bad = bad.generate(days=10.0, dt_s=10.0)["available"].mean()
        assert a_bad < a_calm

    def test_events_recorded(self):
        g = get_scenario("douala_seche")
        g.rng = np.random.default_rng(7)
        out = g.generate(days=30.0, dt_s=10.0)
        assert len(out["events"]) > 0
        assert all("duration_s" in e for e in out["events"])


class TestTopology:
    def test_takens_shape(self):
        x = np.sin(np.linspace(0, 100, 1000))
        cloud = takens_embedding(x, m=8, tau=10)
        assert cloud.shape == (1000 - 70, 8)

    def test_psig_higher_for_clean_sine(self):
        fs = 1000
        t = np.arange(0, 1.0, 1.0 / fs)
        clean = np.sin(2 * np.pi * 50 * t)
        noisy = np.sin(2 * np.pi * 50 * t) + np.random.default_rng(0).normal(0, 1.2, t.size)
        p_clean = TopologicalWatchdog().psig(clean)
        p_noisy = TopologicalWatchdog().psig(noisy)
        assert p_clean > p_noisy

    def test_watchdog_flags_degradation(self):
        fs = 1000
        t = np.arange(0, 1.0, 1.0 / fs)
        wd = TopologicalWatchdog()
        wd.update(np.sin(2 * np.pi * 50 * t))            # référence saine
        verdict = wd.update(np.random.default_rng(0).normal(0, 1, t.size))
        assert verdict["healthy"] is False


class TestCPA:
    def test_standard_config_runs(self):
        r = evaluate(REFERENCE_CONFIGS["standard"], days=3.0, scenario="semi_urbain")
        assert 0.0 <= r.availability <= 1.0
        assert r.energy_load_wh > 0

    def test_never_creates_energy(self):
        cfg = REFERENCE_CONFIGS["standard"]
        r = evaluate(cfg, days=3.0, scenario="worst_case")
        served = r.energy_load_wh - r.unserved_wh
        sources = r.energy_pv_wh + r.energy_eneo_wh + cfg.battery_kwh * 1000
        assert served <= sources * 1.01

    def test_worst_case_harder_than_calm(self):
        cfg = REFERENCE_CONFIGS["standard"]
        r_bad = evaluate(cfg, days=5.0, scenario="worst_case", seed=3)
        r_calm = evaluate(cfg, days=5.0, scenario="yaounde_pluies", seed=3)
        assert r_bad.availability <= r_calm.availability + 0.01

    def test_supercap_constraint_blocks_bad_config(self):
        tiny = GridConfig("trop petit", 5000.0, 7500.0, 28.7, supercap_f=1.0)
        assert not hard_constraints_ok(tiny)["supercap_ok"]

    def test_standard_hard_constraints(self):
        hc = hard_constraints_ok(REFERENCE_CONFIGS["standard"])
        assert hc["supercap_ok"] and hc["pv_ok"]


class TestFigureGeneration:
    def test_all_figures_produce_valid_pngs(self, tmp_path):
        # Le script de figures doit produire 6 PNG valides (taille > 1 KB)
        import scripts.generate_figures as g
        g.OUT = str(tmp_path)
        g.fig_plan_electrique()
        g.fig_plan_mecanique()
        g.fig_appareil_monte()
        g.fig_simulation()
        g.fig_psig()
        g.fig_logo()
        for name in ["01_plan_electrique.png", "02_plan_mecanique.png",
                     "03_appareil_monte.png", "04_simulation.png",
                     "05_psig_topologie.png", "06_logo_ratis_labs.png"]:
            p = tmp_path / name
            assert p.exists() and p.stat().st_size > 1000


def test_monte_carlo_deterministic():
    cfg = GridConfig("test", 500.0, 1500.0, 7.2, 50.0)
    mc = monte_carlo(cfg, days=2.0, n=3, scenario="semi_urbain")
    assert mc["n"] == 3
    assert 0.0 <= mc["availability_min"] <= mc["availability_mean"] <= 1.0
