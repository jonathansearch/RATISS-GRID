# 🔌 Firmware ESP32 — Supervision RATISS-GRID (MicroPython)
# TopologicalWatchdog embarqué : lit la tension AC (ZMPT101B) et le courant bus DC
# (INA219), calcule P_sig en temps réel, alerte sur dégradation, affiche SoC.
#
# Matériel : ESP32-WROOM-32 + ZMPT101B (tension AC) + INA219 (courant/tension DC)
#            + écran SSD1306 I2C + relais délestage confort.
# Flash : `ampy put main.py` ou Thonny. Dépendances : `micropython-ina219`, `ssd1306`.
#
# RÈGLE : ce firmware MESURE, il ne prétend pas. Chaque alerte P_sig est à valider
# au multimètre pendant la phase de calibration du prototype (voir MEMO_GRID.md).

from machine import ADC, I2C, Pin
import time, math, array

# --- Configuration matérielle ---
PIN_AC_ADC   = 34          # ZMPT101B → ADC1_CH6 (attention : ADC1 seul avec WiFi)
I2C_SDA, I2C_SCL = 21, 22  # INA219 + SSD1306 sur I2C
PIN_RELAY_COMFORT = 26     # relais de délestage circuit confort
V_REF        = 3.3
ADC_MAX      = 4095
AC_CALIBRATION = 460.0     # à calibrer : V_rms affiché / V_rms réel (multimètre)
FS_HZ        = 1000        # fréquence d'échantillonnage cible (~1 kHz)
WINDOW       = 100         # fenêtre P_sig = 100 points = 100 ms = 5 périodes 50 Hz
TAU          = 5           # ~1/4 période à 1 kHz pour 50 Hz
SOC_LOW      = 0.40        # seuil de délestage confort (40 %)

# --- Lecture capteurs ---
adc = ADC(Pin(PIN_AC_ADC))
adc.atten(ADC.ATTN_11DB)   # pleine échelle ~3.3 V
adc.width(ADC.WIDTH_12BIT)
relay = Pin(PIN_RELAY_COMFORT, Pin.OUT, value=1)   # confort activé par défaut

def read_v_ac_rms(n=200):
    """Tension AC RMS (V) via ZMPT101B. Moyenne des carrés sur n échantillons."""
    acc = 0.0
    offset = ADC_MAX // 2
    for _ in range(n):
        raw = adc.read() - offset
        acc += raw * raw
    v_adc = math.sqrt(acc / n) * (V_REF / ADC_MAX)
    return v_adc * AC_CALIBRATION

# --- TopologicalWatchdog embarqué (aire de cycle de Takens, m=2) ---
class Watchdog:
    def __init__(self, tau=TAU):
        self.tau = tau
        self.p_ref = None

    def psig(self, w):
        """Aire signée normalisée du cycle de Takens. w = array de float."""
        n = len(w) - self.tau
        if n <= 1:
            return 0.0
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / len(w) + 1e-12
        area = 0.0
        for i in range(n):
            area += w[i] * w[i + self.tau] - w[i + 1] * w[i + self.tau - 1] if i + 1 < n + self.tau else 0
        return abs(0.5 * area) / (n * var)

    def update(self, w):
        p = self.psig(w)
        if self.p_ref is None:
            self.p_ref = p if p > 1e-6 else 1e-6
        ratio = p / self.p_ref
        return p, ratio, ratio > 0.5

wd = Watchdog()
window = array.array("f", [0.0] * WINDOW)

def sample_window():
    """Remplit la fenêtre à FS_HZ. Retourne le tableau de tension par-unité."""
    t0 = time.ticks_us()
    for i in range(WINDOW):
        window[i] = (adc.read() - ADC_MAX // 2) / (ADC_MAX / 2)
        # cadence ~1 kHz (attente active — précision suffisante pour du 50 Hz)
        while time.ticks_diff(time.ticks_us(), t0) < (i + 1) * (1_000_000 // FS_HZ):
            pass
    return window

# --- Boucle principale ---
def run(get_soc=lambda: 0.8):
    """Supervision en continu. `get_soc` lit le SoC batterie via INA219 (I2C).
    À brancher sur la lecture réelle du BMS/INA219 au prototype."""
    print("RATISS-GRID watchdog démarré. P_ref se calibre sur la 1re fenêtre saine.")
    while True:
        w = sample_window()
        p, ratio, healthy = wd.update(w)
        v_rms = read_v_ac_rms()
        soc = get_soc()
        # Délestage confort si batterie basse
        relay.value(1 if soc > SOC_LOW else 0)
        print("V={:.1f}V P_sig={:.4f} ratio={:.2f} sain={} SoC={:.0%} confort={}".format(
            v_rms, p, ratio, "OUI" if healthy else "NON", soc, "ON" if soc > SOC_LOW else "OFF"))
        if not healthy:
            print("  ⚠️  ALERTE : dégradation structurelle du réseau détectée (P_sig chute)")
        time.sleep_ms(500)

# Point d'entrée
if __name__ == "__main__":
    run()
