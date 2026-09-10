"""CLI : python -m ratiss_grid.size_my_grid --load 2000 --days 30 [--monte-carlo 100]"""

from __future__ import annotations

import argparse
import json

from .sizing import (REFERENCE_CONFIGS, GridConfig, evaluate, hard_constraints_ok,
                     monte_carlo)


def main() -> None:
    ap = argparse.ArgumentParser(description="Dimensionnement RATISS-GRID")
    ap.add_argument("--load", type=float, default=2000.0,
                    help="charge critique moyenne (W)")
    ap.add_argument("--days", type=float, default=30.0)
    ap.add_argument("--config", choices=list(REFERENCE_CONFIGS), default="standard")
    ap.add_argument("--custom", action="store_true",
                    help="construire une config custom à partir de --load")
    ap.add_argument("--scenario", default="worst_case",
                    choices=["yaounde_pluies", "douala_seche", "semi_urbain", "worst_case"])
    ap.add_argument("--season", default="wet", choices=["wet", "dry"])
    ap.add_argument("--monte-carlo", type=int, default=0, metavar="N",
                    help="N tirages Monte Carlo (distribution de disponibilité)")
    args = ap.parse_args()

    if args.custom:
        # Règle de dimensionnement : PV = 1.5× load en Wc, batterie = 1 jour
        # d'autonomie × 1.25 (DoD 80 %), supercaps dimensionnés pour 2 s à pleine
        # charge : C = 2 P t / (Vmax² − Vmin²)
        load = args.load
        cfg = GridConfig(
            name=f"Custom {load:.0f} W",
            load_w=load,
            pv_wp=1.5 * load,
            battery_kwh=load * 0.7 * 24 / 1000.0 * 1.25,
            supercap_f=max(50.0, 2 * load * 2.0 / (48.0 ** 2 - 24.0 ** 2)),
        )
    else:
        cfg = REFERENCE_CONFIGS[args.config]
        cfg.load_w = args.load if args.load != 2000.0 else cfg.load_w

    print(f"== RATISS-GRID — config « {cfg.name} » ==")
    print(f"PV {cfg.pv_wp:.0f} Wc · batterie {cfg.battery_kwh:.1f} kWh · "
          f"supercaps {cfg.supercap_f:.0f} F · charge {cfg.load_w:.0f} W")

    hc = hard_constraints_ok(cfg)
    print(f"\nContraintes dures :")
    print(f"  autonomie supercaps : {hc['supercap_autonomy_s']:.1f} s "
          f"(min 2.0 s) → {'OK' if hc['supercap_ok'] else 'INSUFFISANT'}")
    print(f"  ratio PV/charge     : {hc['pv_load_ratio']:.2f} "
          f"(min 1.30) → {'OK' if hc['pv_ok'] else 'INSUFFISANT'}")

    r = evaluate(cfg, days=args.days, scenario=args.scenario, season=args.season)
    print(f"\nSimulation {args.days:.0f} jours ({args.scenario}, saison {args.season}) :")
    print(f"  énergie demandée    : {r.energy_load_wh/1000:.1f} kWh")
    print(f"  énergie PV utilisée : {r.energy_pv_wh/1000:.1f} kWh")
    print(f"  appoint Eneo        : {r.energy_eneo_wh/1000:.2f} kWh")
    print(f"  non servi           : {r.unserved_wh/1000:.3f} kWh")
    print(f"  disponibilité       : {100*r.availability:.3f} %")
    print(f"  black-outs          : {r.n_blackout_events}")
    print(f"  cycles batterie     : {r.battery_cycles:.1f} eq. complets")
    print(f"  durée de vie batt.  : {r.battery_life_years:.1f} ans (35 °C)")

    if args.monte_carlo > 0:
        mc = monte_carlo(cfg, days=args.days, n=args.monte_carlo,
                         scenario=args.scenario, season=args.season)
        print(f"\nMonte Carlo ({mc['n']} tirages) :")
        print(f"  disponibilité moyenne : {100*mc['availability_mean']:.3f} %")
        print(f"  percentile 5 %        : {100*mc['availability_p05']:.3f} %")
        print(f"  pire cas              : {100*mc['availability_min']:.3f} %")
        print(f"  objectif 99.9 % tenu à P5 : {'OUI' if mc['target_met_p05'] else 'NON'}")

    print("\n" + json.dumps({"config": cfg.name, "availability": r.availability,
                             "unserved_kwh": r.unserved_wh/1000.0}, indent=2))


if __name__ == "__main__":
    main()
