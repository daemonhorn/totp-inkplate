"""Byte-for-byte copy of upstream's own hardware-revision probe, unmodified:
https://github.com/SolderedElectronics/Inkplate-micropython/blob/2.0.0/examples/inkplate10/detect_variant.py

Confirms which Inkplate10 hardware revision (classic v1 vs V2) this board's
auto-detect logic picks, before it ever calls begin()/select_board().
Both variants map to an identical 1200x825 board_config_t in the firmware
(checked directly against
firmware/usermods/inkplate/display/board_config.c at this tag), so a wrong
variant pick wouldn't explain a width/geometry-shaped distortion on its
own -- but it's a cheap, definitive check worth ruling out explicitly
rather than assuming.

Run with `mpremote run tools/experiments/upstream_detect_variant.py` --
transient, never saved to the board.
"""

from machine import I2C, Pin

from inkplate10 import _PROBE_ADDR, _PROBE_REG, _detect_variant

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
detected = i2c.scan()
print("I2C scan:", ["{:#x}".format(a) for a in detected])

if _PROBE_ADDR not in detected:
    print("ERROR: no device at {:#x} -- can't probe".format(_PROBE_ADDR))
else:
    val = i2c.readfrom_mem(_PROBE_ADDR, _PROBE_REG, 1)[0]
    print("Register {:#x} @ {:#x} = {:#x}".format(_PROBE_REG, _PROBE_ADDR, val))
    variant = _detect_variant(i2c)
    print("Detected variant:", variant)
