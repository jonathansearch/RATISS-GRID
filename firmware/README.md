# 🔌 Firmware RATISS-GRID — Supervision ESP32

MicroPython sur ESP32-WROOM-32. Fait tourner le **TopologicalWatchdog** (P_sig)
en temps réel sur le réseau physique, avec délestage automatique du circuit confort.

## Matériel
- ESP32-WROOM-32
- ZMPT101B (tension AC 230 V, isolé) → GPIO34 (ADC1)
- INA219 (courant/tension bus DC 48 V) → I2C (SDA 21, SCL 22)
- SSD1306 (écran OLED) → I2C (même bus)
- Relais de délestage confort → GPIO26

## Flash
```bash
pip install esptool adafruit-ampy
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 write_flash 0x1000 esp32-micropython.bin
ampy --port /dev/ttyUSB0 put main.py
# + bibliothèques : micropython-ina219, ssd1306
```

## Calibration (OBLIGATOIRE avant confiance)
1. Mesurer la tension secteur réelle au **multimètre true-RMS**.
2. Comparer à la valeur affichée → ajuster `AC_CALIBRATION` dans `main.py`.
3. Laisser tourner 24 h, noter le P_sig de référence sur réseau sain.
4. Valider que chaque alerte P_sig correspond à un événement réel (multimètre).
   Tant que cette validation n'est pas faite, les alertes sont INDICATIVES.

## ⚠️ Règle RATISS
Ce firmware **mesure**, il ne prétend pas. Tant que la campagne de calibration
du prototype n'est pas faite, le P_sig affiché est une indication, pas une
certification. Voir MEMO_GRID.md → Phase 0.5.
