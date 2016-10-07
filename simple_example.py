#!/usr/bin/env python

from pcbnew import *

import sys
import pcbmerge

# Load the power board
mypcb = LoadBoard("example_power/power.kicad_pcb")

# Merge the power board with the led board
pcbmerge.merge(pcb = mypcb, base_anchor = "OUTPUT", addon_anchor = "IN", filename = "example_led/led.kicad_pcb")

# Save output
SaveBoard("simple.kicad_pcb", mypcb)

