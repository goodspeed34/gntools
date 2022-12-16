# Copyright (C) 2022 William Goodspeed (龚志乐)
# This file is part of GNtools.
#
# GNtools is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# GNtools is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNtools. If not, see <https://www.gnu.org/licenses/>.

import logging

import tkinter as tk
from tkinter import ttk

from aboutui import cb_authors, cb_warranty, cb_gpl
from fastaui import cb_fasta_extract

from fasta import FastaReader

# logging.basicConfig(level=logging.DEBUG)
# fastar = FastaReader('/home/goodspeed/Bio/asm/ncbi-genomes-2022-12-14/GCF_000001405.40_GRCh38.p14_genomic.fna.gz')
# seq = fastar.find_seq('NW_009646206.1')
# seq.slice(100, 1)
# seq.complement()
# print(seq.build_text())

class LabelSeparator (tk.Frame):
    def __init__ (self, parent, text="", width="", font="Monospace 10", *args):
        tk.Frame.__init__ (self, parent, *args)

        self.separator = ttk.Separator(self, orient = tk.HORIZONTAL)
        self.separator.grid (row = 0, column = 0, sticky = "ew")

        self.label = ttk.Label(self, text = text)
        self.label.configure(font=font)
        self.label.grid(row = 0, column = 0, padx = width)

def append_text(fm, text, font="Monospace 20"):
	label = tk.Label(fm, text=text)
	label.configure(font=font)
	label.pack()

def blank_line(fm):
	append_text(fm, "", "Monospace 10")

root = tk.Tk()
root.geometry('350x500')

frame = tk.Frame(root)

# The Banner
append_text(frame, "Welcome to GNtools!", "Monospace 20")
append_text(frame, """This is free software: you are free to change
and redistribute it. There is NO WARRANTY, to
the extent permitted by law.""", "Monospace 10")
blank_line(frame)

# SEQUENCE TOOLKIT
LabelSeparator(frame, text="Sequence Toolkit", width=70, font="Monospace 13").pack()
tk.Button(frame, text="Fasta Extract", command=cb_fasta_extract).pack()

# COPYRIGHT
LabelSeparator(frame, text="About", width=70, font="Monospace 13").pack()

append_text(frame, "GNtools is written by its authors.", "Monospace 10")
tk.Button(frame, text="Authors of GNtools", command=cb_authors).pack()

append_text(frame, "GNtools comes with ABSOLUTELY NO WARRANTY.", "Monospace 10")
tk.Button(frame, text="Disclamier of Warranty", command=cb_warranty).pack()

append_text(frame, """GNtools is free software, and you are welcome
redistribute it under terms of:""", "Monospace 10")
tk.Button(frame, text="GNU General Public License", command=cb_gpl).pack()

frame.pack()
root.mainloop()