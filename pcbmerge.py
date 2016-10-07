# KiCad_PCBmerge
# A python library for merging multiple KiCad PCBs
#
# Author: Florian Kauer <florian.kauer@koalo.de>
#
# Do not start this directly, instead use a merge script, for example
# 
# from pcbnew import *
# import pcbmerge
#
# mypcb = LoadBoard("main/main.kicad_pcb")
# pcbmerge.merge(pcb = mypcb, 
#                base_anchor = "MATCH_1", 
#                addon_anchor = "MATCH", 
#                filename = "addon/addon.kicad_pcb")
# SaveBoard("output.kicad_pcb", mypcb)
#
#########################################################################
#
# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <http://unlicense.org>

from collections import namedtuple
from pcbnew import *
import inspect
import tempfile
import os
from contextlib import contextmanager

def find_module_by_value(pcb, value):
    modules = filter(lambda m: m.GetValue() == value, pcb.GetModules())
    assert len(modules) > 0, "%s not found" % value
    assert len(modules) == 1, "%s is not unique" % value
    return modules[0]

Displacement = namedtuple("Displacement", "delta anchor rot")

def calculate_displacement(a, b):
    return Displacement(
            delta = a.GetPosition() - b.GetPosition(),
            anchor = a.GetPosition(),
            rot = a.GetOrientation() - b.GetOrientation())

def move(element, displacement):
    element.Move(displacement.delta)
    element.Rotate(displacement.anchor, displacement.rot)

@contextmanager
def tempfilename():
    f = tempfile.NamedTemporaryFile(delete=False)
    try:
        f.close()
        yield f.name
    finally:
        try:
            os.unlink(f.name)
        except OSError:
            pass

def merge(pcb, base_anchor, addon_anchor, filename):
    base_anchor_module = find_module_by_value(pcb, base_anchor)

    pcb_tmp = LoadBoard(filename)
    addon_anchor_module = find_module_by_value(pcb_tmp, addon_anchor)

    displacement = calculate_displacement(base_anchor_module, addon_anchor_module)

    # Remember existing elements in base
    for t in pcb.GetTracks():
        t.SetFlags(FLAG0)
    module = pcb.GetModules().GetLast()
    drawing = pcb.GetDrawings().GetLast()
    zonescount = pcb.GetAreaCount()

    # Determine new net names
    new_netnames = {}
    for i in range(1, pcb_tmp.GetNetCount()): # 0 is unconnected net
        name = pcb_tmp.FindNet(i).GetNetname()
        new_netnames[name] = name+"-"+base_anchor
    
    for (a,b) in zip(base_anchor_module.Pads(), addon_anchor_module.Pads()):
        new_netnames[b.GetNet().GetNetname()] = a.GetNet().GetNetname()

    # Remove anchor
    pcb_tmp.Remove(addon_anchor_module)

    with tempfilename() as fname:
        # Write addon to temporary file
        SaveBoard(fname, pcb_tmp)

        # Replace net names in file
        pcbtext = None
        with open(fname) as fp:
            pcbtext = fp.read()

        for (old,new) in new_netnames.iteritems():
            pcbtext = pcbtext.replace(old,new)
        
        with open(fname,'w') as fp:
            fp.write(pcbtext)

        # Append new board file with modified net names
        plugin = IO_MGR.PluginFind(IO_MGR.KICAD)
        plugin.Load(fname, pcb)

    # Move
    for t in pcb.GetTracks():
        if t.GetFlags() & FLAG0:
            t.ClearFlags(FLAG0)
            continue
        move(t, displacement)
        
    if module:
        module = module.Next()
    else:
        module = pcb.GetModules().GetFirst()

    while module:
        move(module, displacement)
        module = module.Next()

    if drawing:
        drawing = drawing.Next()
    else:
        drawing = pcb.GetDrawings().GetFirst()

    while drawing:
        move(drawing, displacement)
        drawing = drawing.Next()

    for i in range(zonescount, pcb.GetAreaCount()):
        move(pcb.GetArea(i), displacement)
