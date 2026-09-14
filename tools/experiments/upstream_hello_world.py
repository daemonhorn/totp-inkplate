"""Byte-for-byte copy of upstream's own canonical demo, unmodified:
https://github.com/SolderedElectronics/Inkplate-micropython/blob/2.0.0/examples/inkplate10/hello_world.py

Every probe so far has gone through our own vendored driver, but always
called from a *script we wrote*. Reflashing the firmware fresh didn't
change the corruption (row_edge_probe.py showed the same distortion after
a clean erase-flash + write-flash), which rules out a stale/mismatched
firmware image. This is the next elimination: run upstream's own example,
completely unmodified, to see whether the exact same distortion shows up
even here. If it does, this is either a genuine bug in this specific
`2.0.0` release or a hardware issue with this board -- not anything in our
vendoring, our app, or how we're calling the driver -- and worth reporting
upstream rather than debugging further on our side.

Run with `mpremote run tools/experiments/upstream_hello_world.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate  # Include the Inkplate module

inkplate = Inkplate(Inkplate.INKPLATE_1BIT)  # Create a display instance (8-level grayscale)

inkplate.begin()  # Initialize the display

inkplate.set_text_size(2)  # Scale up the font size

inkplate.set_cursor(450, 350)  # Set the cursor from where the text will be written

inkplate.print("Hello world!")  # Print to the display buffer

inkplate.display()  # Display what is drawn to the buffer

print("[probe] look at the panel: does 'Hello world!' render fully and correctly")
print("[probe] at roughly the middle of the screen, or is it distorted/cut off?")
