"""Signature topologique du réseau électrique — la marque RATISS.

Doctrine LCT appliquée à l'énergie : une série de tension saine (50 Hz
quasi-pur) plongée par délai (Takens, m=2) trace un ANNEAU dont l'aire est
grande et régulière. Un réseau dégradé (coupures, creux, THD élevé) écrase ou
fragmente cet anneau → l'aire s'effondre AVANT que la tension moyenne ne sorte
des tolérances. C'est l'équivalent du `edge` de Travaux : alerte précoce.

Détecteur : P_sig = aire signée normalisée du cycle de Takens (formule des
trapèzes, exacte en m=2), mesurée sur fenêtre glissante. Robuste, O(N),
mathématiquement transparent — pas de boîte noire.

On prétend mesurer la FORME du signal, pas sa vérité métier : la calibration
absolue se fera sur le prototype physique (MEMO_GRID.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def takens_embedding(signal: np.ndarray, m: int = 2, tau: int = 10) -> np.ndarray:
    """Plongement de Takens : x_i → (x_i, x_{i+τ}, ..., x_{i+(m-1)τ}).

    Retourne un nuage (N, m) avec N = len(signal) - (m-1)*tau.
    """
    signal = np.asarray(signal, dtype=float)
    n = len(signal) - (m - 1) * tau
    if n <= 0:
        raise ValueError("signal trop court pour le plongement demandé")
    return np.column_stack([signal[i * tau: i * tau + n] for i in range(m)])


def cycle_area(signal: np.ndarray, tau: int = 10) -> float:
    """Aire signée du cycle de Takens (m=2), normalisée par la variance.

    Pour un sinus pur de fréquence f échantillonné à fs, avec tau·fs ≈ 1/(4f),
    l'aire vaut ≈ π·A² — maximale et stable. Pour du bruit blanc, l'aire
    moyenne tend vers 0 (marche aléatoire non fermée). C'est le contraste.
    """
    cloud = takens_embedding(signal, m=2, tau=tau)
    x, y = cloud[:, 0], cloud[:, 1]
    area = 0.5 * float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))
    var = float(np.var(signal)) + 1e-12
    return abs(area) / (len(x) * var)


@dataclass
class TopologicalWatchdog:
    """Détecteur de fragilité du réseau par aire du cycle (fenêtre glissante).

    Usage : `update(v_pu_window)` avec une fenêtre de tension (par-unité,
    ~1–2 périodes du 50 Hz à fs connu). La première fenêtre saine calibre la
    référence ; ensuite le ratio P_sig/P_ref indique la santé structurelle.
    """

    tau: int = 5                       # ~1/4 période à fs=1 kHz pour 50 Hz
    psig_healthy_ref: float | None = None

    def psig(self, window: np.ndarray) -> float:
        return cycle_area(window, tau=self.tau)

    def update(self, window: np.ndarray) -> dict:
        p = self.psig(window)
        if self.psig_healthy_ref is None:
            self.psig_healthy_ref = p if p > 1e-6 else 1e-6
        ratio = p / self.psig_healthy_ref
        return {
            "p_sig": p,
            "p_sig_ratio": ratio,
            "healthy": bool(ratio > 0.5),
        }
