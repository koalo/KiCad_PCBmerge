#!/usr/bin/env python

from pcbnew import *
import pcbmerge

# Load the power board
mypcb = LoadBoard("example_power/power.kicad_pcb")

# Merge several times and use a newly added element as anchor for the next board
anchor = "OUTPUT"
for i in range(0, 16):
    pcbmerge.merge(pcb = mypcb,
                   base_anchor = anchor,
                   addon_anchor = "IN",
                   filename = "example_led/led.kicad_pcb",
                   postfix = "-LED-"+str(i))

    anchor = "OUT_"+str(i)
    pcbmerge.find_module_by_value(mypcb, "OUT").SetValue(anchor)


# Combine and refill areas
pcbmerge.combine_all_areas(mypcb)
pcbmerge.fill_all_areas(mypcb)

# Save output
SaveBoard("recursive.kicad_pcb", mypcb)

