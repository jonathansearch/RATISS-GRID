"""Génère toutes les figures de RATISS-GRID — plans de conception + marque.

Produit des PNG dans docs/images/ :
1. Plan de conception électrique (schéma de puissance du CPA, annoté)
2. Plan de conception mécanique / layout d'assemblage (armoire, composants)
3. L'appareil une fois monté (rendu du coffre-fort énergétique)
4. Courbes de simulation (production PV, charge, SoC batterie, tension)
5. Détection topologique P_sig (emboîtement de Takens, aire du cycle)
6. Logo / marque RATIS Labs

Usage : PYTHONPATH=. python scripts/generate_figures.py
Les courbes de simulation proviennent du vrai simulateur (ratiss_grid), pas de
données inventées.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 11,
                     "axes.grid": True, "grid.alpha": 0.3})

# Palette RATIS Labs
RATIS_DARK = "#0b1f3a"
RATIS_GREEN = "#1f9d55"
RATIS_GOLD = "#e0a800"
RATIS_RED = "#c0392b"


def save(fig, name, facecolor="white"):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor=facecolor)
    plt.close(fig)
    print("généré :", name)


def _box(ax, x, y, w, h, text, fc, fs=9, tc="black"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                facecolor=fc, edgecolor=RATIS_DARK,
                                linewidth=1.6, zorder=2))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fs, zorder=3, fontweight="bold", color=tc)


def _wire(ax, p1, p2, color=RATIS_DARK, lw=2.0, label="", loff=(0, 0.12)):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=0, shrinkB=0))
    if label:
        mx, my = (p1[0]+p2[0])/2 + loff[0], (p1[1]+p2[1])/2 + loff[1]
        ax.text(mx, my, label, fontsize=8, ha="center", color=color,
                fontweight="bold")


# ======================================================== 1. PLAN ÉLECTRIQUE
def fig_plan_electrique():
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7.5); ax.axis("off")
    ax.set_title("PLAN DE CONCEPTION ÉLECTRIQUE — Conditionneur de Puissance Actif (CPA)\n"
                 "Chaîne de puissance : PV → MPPT → Bus DC → Onduleur → Charge critique",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    # Rangée principale (bus de puissance)
    _box(ax, 0.3, 5.2, 1.8, 1.0, "Panneaux PV\nmono 4500 Wc\n(10×450 W)", "#ffe9a8")
    _box(ax, 2.6, 5.2, 1.6, 1.0, "MPPT\nTracker\n(η≈98%)", "#ffd27f")
    _box(ax, 4.8, 5.2, 1.8, 1.0, "BUS DC\n48 V\n(batterie)", "#cfe0ff")
    _box(ax, 7.2, 5.2, 1.8, 1.0, "Onduleur\nsinus pur\n3 kVA", "#d3f4e0")
    _box(ax, 9.6, 5.2, 2.0, 1.0, "CHARGE\nCRITIQUE\n700 W garantis", "#ffc9c9")

    _wire(ax, (2.1, 5.7), (2.6, 5.7), label="DC", loff=(0, 0.15))
    _wire(ax, (4.2, 5.7), (4.8, 5.7), label="48 V DC")
    _wire(ax, (6.6, 5.7), (7.2, 5.7), label="48 V DC")
    _wire(ax, (9.0, 5.7), (9.6, 5.7), label="230 V AC 50 Hz", loff=(0, 0.18))

    # Stockage hybride (sous le bus DC)
    _box(ax, 4.2, 2.9, 2.6, 1.1, "BATTERIE LiFePO4\n14.3 kWh\n(16S 280 Ah)", "#bfe6bf")
    _box(ax, 4.2, 1.2, 2.6, 1.0, "SUPERCONDENSATEURS\n50 F — pont\nmicro-coupures", "#e0b3ff")
    _wire(ax, (5.5, 5.2), (5.5, 4.0), color=RATIS_DARK, label="charge/décharge", loff=(1.6, 0))
    _wire(ax, (5.5, 2.9), (5.5, 2.2), color=RATIS_DARK)

    # Réseau Eneo (appoint) + watchdog
    _box(ax, 10.0, 3.4, 2.2, 1.0, "Réseau ENEO\n(appoint seulement)", "#f0f0f0")
    _wire(ax, (10.6, 4.4), (10.6, 5.2), color=RATIS_RED, label="ATS / délestage", loff=(2.1, 0))

    _box(ax, 0.3, 2.9, 2.2, 1.1, "ESP32 Watchdog\nP_sig topologique\n(ZMPT101B+INA219)", "#fff3b0")
    _wire(ax, (2.5, 3.45), (7.2, 5.3), color=RATIS_GOLD, lw=1.5, label="surveillance 50 Hz")
    _wire(ax, (1.4, 4.0), (4.2, 3.45), color=RATIS_GOLD, lw=1.5)

    # Annotations de conception
    ax.text(0.3, 0.4,
            "CONCEPTION : les supercondensateurs absorbent les micro-coupures (<2 s) le temps que\n"
            "la batterie LiFePO4 prenne le relais → continuité de service. Eneo n'est qu'un appoint\n"
            "délesté automatiquement. Le watchdog topologique surveille la santé du réseau en continu.",
            fontsize=8.5, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor=RATIS_GOLD))
    save(fig, "01_plan_electrique.png")


# ======================================================== 2. PLAN MÉCANIQUE
def fig_plan_mecanique():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_title("PLAN DE CONCEPTION MÉCANIQUE — Armoire du coffre-fort énergétique\n"
                 "Layout d'assemblage (vue de face, porte ouverte) — cotes indicatives",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    # Armoire
    ax.add_patch(Rectangle((1.5, 0.5), 8, 6.8, facecolor="#eef2f6",
                           edgecolor=RATIS_DARK, linewidth=2.5, zorder=1))
    ax.text(5.5, 7.0, "Armoire IP54 ventilée ~800×600×1400 mm",
            ha="center", fontsize=9, style="italic", color=RATIS_DARK)

    # Étages
    _box(ax, 2.0, 5.4, 3.0, 1.4, "ÉTAGÈRE HAUTE\nMPPT + Onduleur\n(bien ventilé)", "#d3f4e0")
    _box(ax, 5.4, 5.4, 3.6, 1.4, "COFFRET AC/DC\ndisjoncteurs, ATS,\nparafoudre, borniers", "#ffe9a8")
    _box(ax, 2.0, 3.4, 3.4, 1.6, "BATTERIE LiFePO4\n16S 280 Ah\n(masse basse, BMS)", "#bfe6bf")
    _box(ax, 5.8, 3.4, 3.2, 1.6, "SUPERCONDENSATEURS\nrack 50 F\n(à côté du bus DC)", "#e0b3ff")
    _box(ax, 2.0, 1.6, 3.0, 1.4, "ESP32 Watchdog\n+ afficheur OLED\n+ capteurs", "#fff3b0")
    _box(ax, 5.4, 1.6, 3.6, 1.4, "VENTILATION basse\n+ passage de câbles\n(goulotte)", "#f0f0f0")

    # Flux thermique
    ax.annotate("", xy=(3.5, 6.6), xytext=(3.5, 1.8),
                arrowprops=dict(arrowstyle="->", color=RATIS_RED, lw=2, linestyle="--"))
    ax.text(3.65, 4.2, "air chaud ↑", rotation=90, fontsize=8, color=RATIS_RED)

    ax.text(1.0, 0.15,
            "RÈGLES DE MONTAGE : masse lourde (batterie) en BAS · électronique de puissance en HAUT "
            "et ventilée · supercaps près du bus DC (liaison courte, faible résistance) · "
            "watchdog ESP32 accessible en façade · presse-étoupes en bas pour les câbles.",
            fontsize=8.3, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor=RATIS_GOLD))
    save(fig, "02_plan_mecanique.png")


# ======================================================== 3. APPAREIL MONTÉ
def fig_appareil_monte():
    fig, ax = plt.subplots(figsize=(9, 10))
    ax.set_xlim(0, 9); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("RATISS-GRID — Le coffre-fort énergétique une fois monté",
                 fontsize=13, fontweight="bold", color=RATIS_DARK)

    # Corps de l'armoire (effet 3D simple)
    ax.add_patch(FancyBboxPatch((2.2, 1.0), 4.6, 7.5, boxstyle="round,pad=0.05",
                                facecolor=RATIS_DARK, edgecolor="black",
                                linewidth=2.5, zorder=1))
    ax.add_patch(Rectangle((6.8, 1.15), 0.5, 7.2, facecolor="#1a3350",
                           edgecolor="black", zorder=1))  # côté 3D

    # Porte / façade
    ax.add_patch(Rectangle((2.45, 1.25), 4.1, 7.0, facecolor="#2c4a6e",
                           edgecolor="#0a1526", linewidth=1.5, zorder=2))

    # Afficheur OLED
    ax.add_patch(Rectangle((3.2, 6.9), 2.6, 1.0, facecolor="#001a00",
                           edgecolor="lime", linewidth=2, zorder=3))
    ax.text(4.5, 7.55, "RATISS-GRID", ha="center", va="center", color="lime",
            fontsize=11, fontweight="bold", family="monospace", zorder=4)
    ax.text(4.5, 7.15, "SOC 87%  P_sig OK", ha="center", va="center", color="lime",
            fontsize=8, family="monospace", zorder=4)

    # Ventilateurs
    for cx in (3.3, 5.7):
        ax.add_patch(Circle((cx, 2.3), 0.45, facecolor="#12233a",
                            edgecolor="#0a1526", zorder=3))
        for ang in range(0, 360, 45):
            ax.plot([cx, cx+0.3*np.cos(np.radians(ang))],
                    [2.3, 2.3+0.3*np.sin(np.radians(ang))], color="#3a5a80",
                    lw=2, zorder=4)

    # Voyants
    for i, (c, lab) in enumerate([("lime", "PV"), ("gold", "BATT"),
                                   ("red", "GRID")]):
        ax.add_patch(Circle((3.3 + i*1.1, 6.3), 0.13, facecolor=c,
                            edgecolor="black", zorder=4))
        ax.text(3.3 + i*1.1, 5.95, lab, ha="center", fontsize=7.5,
                color="white", zorder=4, fontweight="bold")

    # Poignée + serrure
    ax.add_patch(Rectangle((6.15, 4.4), 0.25, 1.4, facecolor="#888",
                           edgecolor="black", zorder=5))
    ax.text(4.5, 0.55, "Alimentation pure · stable · ininterrompue",
            ha="center", fontsize=10, style="italic", color=RATIS_DARK)
    save(fig, "03_appareil_monte.png")


# ======================================================== 4. SIMULATION
def fig_simulation():
    from ratiss_grid.sizing import REFERENCE_CONFIGS, evaluate
    cfg = REFERENCE_CONFIGS["standard"]
    r = evaluate(cfg, days=7, scenario="worst_case", season="wet", seed=7)

    fig, axs = plt.subplots(2, 1, figsize=(11, 8), sharex=False)
    fig.suptitle("Simulation RATISS-GRID (config Standard, 7 jours, saison humide, "
                 "scénario Eneo dégradé)", fontsize=12.5, fontweight="bold",
                 color=RATIS_DARK)

    # Disponibilité par jour
    if r.per_day_availability:
        days = np.arange(1, len(r.per_day_availability) + 1)
        axs[0].bar(days, [100*a for a in r.per_day_availability],
                   color=RATIS_GREEN, alpha=0.85)
        axs[0].axhline(95, color=RATIS_RED, linestyle="--", label="objectif 95 %")
        axs[0].set_ylabel("Disponibilité (%)"); axs[0].set_ylim(0, 105)
        axs[0].set_title(f"Disponibilité par jour — globale {100*r.availability:.1f} %, "
                         f"{r.n_blackout_events} blackouts")
        axs[0].legend(); axs[0].set_xlabel("jour")

    # Répartition énergétique
    labels = ["PV solaire", "Eneo (appoint)", "Non servie"]
    vals = [r.energy_pv_wh, r.energy_eneo_wh, r.unserved_wh]
    colors = [RATIS_GOLD, RATIS_RED, "#888888"]
    axs[1].pie(vals, labels=labels, autopct="%1.1f%%", colors=colors,
               startangle=90, textprops={"fontsize": 10, "fontweight": "bold"})
    axs[1].set_title(f"Répartition énergétique — batterie {r.battery_cycles:.1f} cycles, "
                     f"durée de vie ≈ {r.battery_life_years:.1f} ans")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, "04_simulation.png")


# ======================================================== 5. P_SIG TOPOLOGIE
def fig_psig():
    from ratiss_grid.topology import takens_embedding
    rng = np.random.default_rng(0)
    t = np.linspace(0, 2*np.pi, 400)
    healthy = np.sin(t) + 0.015*rng.standard_normal(len(t))
    # signal dégradé : amplitude effondrée + distorsion → cycle qui se contracte
    degraded = 0.40*np.sin(t) + 0.10*np.sin(3*t)

    def aire_absolue(sig, tau=8):
        cloud = takens_embedding(sig, m=2, tau=tau)
        x, y = cloud[:, 0], cloud[:, 1]
        return abs(0.5*float(np.sum(x[:-1]*y[1:] - x[1:]*y[:-1])))

    a_h = aire_absolue(healthy)
    a_d = aire_absolue(degraded)

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Détection topologique P_sig — l'aire du cycle trahit la fragilité du réseau",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    axs[0].plot(healthy, lw=1.2, color=RATIS_GREEN, label="réseau sain")
    axs[0].plot(degraded, lw=1.2, color=RATIS_RED, label="réseau dégradé")
    axs[0].set_title("Tension réseau (signal temporel)")
    axs[0].set_xlabel("échantillon"); axs[0].set_ylabel("tension (u.a.)"); axs[0].legend()

    emb_h = takens_embedding(healthy, m=2, tau=8)
    emb_d = takens_embedding(degraded, m=2, tau=8)
    axs[1].plot(emb_h[:, 0], emb_h[:, 1], lw=1.2, color=RATIS_GREEN,
                label=f"sain : aire = {a_h:.1f}")
    axs[1].plot(emb_d[:, 0], emb_d[:, 1], lw=1.2, color=RATIS_RED,
                label=f"dégradé : aire = {a_d:.1f}")
    axs[1].set_title("Portrait de phase (emboîtement de Takens)\n"
                     f"→ effondrement de l'aire : ×{a_h/max(a_d,1e-9):.1f} "
                     "(signature P_sig)")
    axs[1].set_xlabel("x(t)"); axs[1].set_ylabel("x(t+τ)"); axs[1].legend(fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save(fig, "05_psig_topologie.png")


# ======================================================== 6. LOGO RATIS LABS
def fig_logo():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_facecolor(RATIS_DARK)
    fig.patch.set_facecolor(RATIS_DARK)

    # Anneau atomique stylisé
    for angle, col in [(0, RATIS_GREEN), (60, RATIS_GOLD), (120, "#4aa3df")]:
        th = np.linspace(0, 2*np.pi, 200)
        r_x, r_y = 3.2, 1.2
        x = r_x*np.cos(th); y = r_y*np.sin(th)
        # rotation
        a = np.radians(angle)
        xr = x*np.cos(a) - y*np.sin(a); yr = x*np.sin(a) + y*np.cos(a)
        ax.plot(5+xr, 5.6+yr, color=col, lw=3, alpha=0.9)
    # Noyau
    ax.add_patch(Circle((5, 5.6), 0.7, facecolor=RATIS_GOLD,
                        edgecolor="white", linewidth=2, zorder=5))

    ax.text(5, 3.4, "RATIS LABS", ha="center", va="center", fontsize=34,
            fontweight="bold", color="white", family="sans-serif")
    ax.text(5, 2.7, "Souveraineté technologique · Cameroun",
            ha="center", va="center", fontsize=12, color=RATIS_GOLD, style="italic")
    save(fig, "06_logo_ratis_labs.png", facecolor=RATIS_DARK)


if __name__ == "__main__":
    print("Génération des figures RATISS-GRID...")
    fig_plan_electrique()
    fig_plan_mecanique()
    fig_appareil_monte()
    fig_simulation()
    fig_psig()
    fig_logo()
    print("Toutes les figures sont dans docs/images/")
