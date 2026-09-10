"""Campagne de mesure Eneo — recalibrer le modèle sur données RÉELLES.

Phase 0.5 : remplacer les ordres de grandeur documentés par des mesures terrain.
On enregistre la tension secteur pendant 30 jours, on détecte les événements,
et on ré-estime les paramètres de `EnoGridProfile` par maximum de vraisemblance
simple (comptages + distributions empiriques).

Usage :
    python -m scripts.eneo_field_campaign --record 30 --out data/eneo_log.csv
    python -m scripts.eneo_field_campaign --fit data/eneo_log.csv

Sortie : un dict JSON de paramètres prêt à injecter dans EnoGridProfile.
RÈGLE RATISS : seuls les paramètres MESURÉS remplacent les valeurs documentées.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np


def record(days: float, out: str, fs_hz: float = 1.0) -> None:
    """Enregistre la tension (V) à `fs_hz` pendant `days` jours dans `out`.

    Format CSV : timestamp_unix, v_rms. En l'absence de capteur, ce script est
    un CANEVAS : brancher la lecture réelle du ZMPT101B/ESP32 (via port série
    ou MQTT) à la place du simulateur placeholder ci-dessous.
    """
    print(f"[MESURE] Démarrage campagne {days} j à {fs_hz} Hz → {out}")
    print("[MESURE] ATTENTION : remplacer _read_voltage() par la lecture capteur réelle.")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    t_end = time.time() + days * 86400.0
    with open(out, "w") as f:
        f.write("timestamp_unix,v_rms\n")
        while time.time() < t_end:
            v = _read_voltage()
            f.write(f"{time.time():.3f},{v:.2f}\n")
            f.flush()
            time.sleep(1.0 / fs_hz)


def _read_voltage() -> float:
    """PLACEHOLDER — à remplacer par la lecture réelle (ZMPT101B via série/MQTT).
    Lève une erreur pour ne jamais faire croire à une mesure réelle."""
    raise NotImplementedError(
        "Brancher la lecture réelle du capteur de tension. "
        "Ne jamais enregistrer de fausses données."
    )


def fit(csv_path: str) -> dict:
    """Estime les paramètres EnoGridProfile à partir du log de tension.

    Détection d'événements : coupure = V < 20 % nominal ; creux = 20–90 % ;
    micro vs longue selon la durée (seuil 1 s). Retourne le dict de paramètres.
    """
    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    v = data["v_rms"]
    t = data["timestamp_unix"]
    days = (t[-1] - t[0]) / 86400.0
    v_nom = float(np.median(v[v > 100]))  # tension saine = médiane des lectures valides

    down = v < 0.20 * v_nom          # coupure
    sag = (v >= 0.20 * v_nom) & (v < 0.90 * v_nom)  # creux

    def events(mask):
        d = np.diff(mask.astype(int))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0]
        n = min(len(starts), len(ends))
        return [(t[ends[i]] - t[starts[i]]) for i in range(n)]

    outages = events(down)
    sags = events(sag)
    micro = [d for d in outages if d < 1.0]
    longs = [d for d in outages if d >= 1.0]

    params = {
        "days_observed": round(float(days), 2),
        "v_nominal_measured": round(v_nom, 1),
        "availability_measured": round(float((~down).mean()), 4),
        "micro_outages_per_day": round(len(micro) / max(days, 1e-9), 2),
        "long_outages_per_month": round(len(longs) / max(days, 1e-9) * 30.0, 2),
        "long_outage_duration_h_mean": round(float(np.mean(longs) / 3600.0), 2) if longs else 0.0,
        "sag_events_per_day": round(len(sags) / max(days, 1e-9), 2),
        "_source": "MESURÉ sur site — remplace les ordres de grandeur documentés",
    }
    print(json.dumps(params, indent=2, ensure_ascii=False))
    return params


def main() -> None:
    ap = argparse.ArgumentParser(description="Campagne de mesure Eneo (Phase 0.5)")
    ap.add_argument("--record", type=float, metavar="DAYS", help="enregistrer DAYS jours")
    ap.add_argument("--out", default="data/eneo_log.csv")
    ap.add_argument("--fit", metavar="CSV", help="estimer les paramètres depuis un log")
    args = ap.parse_args()
    if args.record:
        record(args.record, args.out)
    elif args.fit:
        fit(args.fit)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
