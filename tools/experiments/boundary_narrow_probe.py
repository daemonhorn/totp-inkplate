"""Narrows the row-transmission truncation boundary found by
column_map_probe.py / full_black_probe.py (see this project's memory /
commit history: 9 wide-spaced columns showed x=750 dead, x=900 alive; a
full-panel black fill's left ~2/3 came back statistically identical to
the sparse-column run despite totally different framebuffer content --
confirming that region's row transmission just never happens, rather than
rendering some intermediate value).

Draws 8px columns tightly spaced through the suspected boundary zone
(x=770..890, every 20px) on white, full refresh. Read the result with a
band-brightness comparison (crop to panel interior, average brightness
per column region), NOT by eye -- eyeballing a related photo from this
same investigation already produced one wrong conclusion (see
totp-inkplate-workflow memory).

Once the exact boundary x is known, bytes_dropped = (1200 - x_boundary)
/ 4 (row_buf's front holds high-x content, 4 pixels/output byte -- see
build_mono_row/board_config_row_bytes in epd_i2s.c/board_config.h) tells
us whether this is a fixed byte-count loss (FIFO drain/out_total_eof
timing in epd_i2s_wait_row) or a clean-ratio config mismatch
(fifo_conf/conf2/conf_chan settings in epd_i2s_init).

Run with `mpremote run tools/experiments/boundary_narrow_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()

COL_W = 8
XS = [770, 790, 810, 830, 850, 870, 890]
for x in XS:
    d.fill_rect(x, 0, COL_W, d.height(), d.BLACK)

d.display()

print("[probe] drew %d columns (%dpx wide) at x=%s on white, full height/refresh" % (
    len(XS), COL_W, XS))
print("[probe] photograph the panel and compare band brightness (don't eyeball) to find")
print("[probe] which of these columns survive -- that pins the truncation boundary.")
