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

# app.py
import re
from enum import auto

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.scrolledtext import ScrolledText

from fasta import FastaReader, FastaSequence

def_readme = '''# README (`#' will start a line of comment)
# Single Gene Extract:
#   Unigene_1
# Chromosome Range Exract:
#   Chr0	100	200
# Chromosome Range Extract and Rename:
#   BabyChr	Chr0	200	100
'''

class FastaExtractUI():
	def run(self):
		"""Perform a fasta extraction."""
		if not self.confirmed:
			self.notice('Error: FastaReader is not initialized, please click `Confirm\'')
			return
		if self.fasta.running:
			self.notice('Error: FastaReader is initializing, please wait')
			return

		self.result = ''

		inpt = self.inpa2.get(1.0, "end-1c")
		for statm in inpt.split('\n'):
			# Skip the comment.
			if statm.startswith('#'):
				continue

			# Select a range of sequence of FASTA and rename it.
			match = re.findall(R'\s*(.*?)\s(.*?)\s([\d\.?]+)\s([\d\.?]+)\s*', statm)
			if match != []:
				match = match[0]
				seqs = self.fasta.find_seqs(match[1], self.header.get(), self.case.get())

				for seq in seqs:
					if len(seqs) > 1:
						seq.name = f'{match[0]}_{seqs.index(seq)}'
					else:
						seq.name = f'{match[0]}'
					seq.slice(int(match[2]), int(match[3]))
					if (int(match[2]) > int(match[3])):
						seq.complement()
					self.result += '\n'
					self.result += seq.build_text()
				continue

			# Select a range of sequence of FASTA.
			match = re.findall(R'\s*(.*?)\s([\d\.?]+)\s([\d\.?]+)\s*', statm)
			if match != []:
				match = match[0]
				seqs = self.fasta.find_seqs(match[0], self.header.get(), self.case.get())

				for seq in seqs:
					seq.slice(int(match[1]), int(match[2]))
					if (int(match[1]) > int(match[2])):
						seq.complement()
					self.result += '\n'
					self.result += seq.build_text()
				continue

			# Select a sequence
			if statm != '':
				seqs = self.fasta.find_seqs(statm, self.header.get(), self.case.get())
				for seq in seqs:
					self.result += '\n'
					self.result += seq.build_text()

		if self.dialog.get():
			infowin = tk.Tk()
			textview = ScrolledText(infowin, font='Monospace 13', width=82)
			textview.insert(tk.END, self.result)
			textview.config(state=tk.DISABLED)
			textview.pack()
			infowin.mainloop()
			return

		outp = self.inpa1.get()
		if outp != '':
			with open(outp, 'w') as f:
				f.write(self.result)
				return
		else:
			self.notice('Error: Invalid output file, aborted')
			return

	def notice(self, desc):
		"""Change the text on the center of the progress bar."""
		self.pbstyle.configure("LabeledProgressbar", text=desc)

	def progress_cb(self, desc, percent):
		"""Update the progress bar and change the text on it."""
		self.progress['value'] = percent
		self.notice(desc)
		self.parent.update_idletasks()
		self.parent.update()

	def init_btn_cb(self):
		"""The callback of the initialize button."""
		if hasattr(self, 'fasta') and self.fasta.running:
			return
		try:
			self.fasta = FastaReader(self.inpa0.get(), self.progress_cb)
			self.confirmed = True
		except Exception as e:
		 	self.notice(str(e))
		 	self.confirmed = False

	def selbtn_open_cb(self, t, where):
		def click_cmd():
			where.delete(0, tk.END)
			where.insert(0, fd.askopenfilename(title = t, filetypes = (("all files","*.*"),)))
		return click_cmd

	def selbtn_saveas_cb(self, t, where):
		def click_cmd():
			where.delete(0, tk.END)
			where.insert(0, fd.asksaveasfilename(title = t, filetypes = (("all files","*.*"),)))
		return click_cmd

	def selbtn_readf_cb(self, t, where):
		def click_cmd():
			fp = fd.askopenfilename(title = t, filetypes = (("all files","*.*"),))
			if fp == '':
				return
			try:
				with open(fp, 'r') as f:
					where.delete(1.0, tk.END)
					where.insert(tk.END, f.read())
			except:
				self.notice('Error: trying to open an invalid file')
				return
		return click_cmd

	def __init__(self):
		self.confirmed = False

		parent = tk.Tk()
		parent.resizable(width=False, height=False)
		parent.geometry("1020x600+200+50")
		parent.title("Fasta Extract (tkinter)")
		self.parent = parent

		title = tk.Label(parent, text="Fasta Extract", height=2, width=1024, relief=tk.GROOVE)
		title.pack()

		lf0 = tk.LabelFrame(parent, text='Set an Input Fasta File', height=60, width=1024)
		self.inpa0 = tk.Entry(lf0, width=120)
		self.inpa0.grid(column=1, row=1)
		selbtn = tk.Button(lf0, height=1, width=4, text="...",
		                   command=self.selbtn_open_cb('Set an Input Fasta File', self.inpa0))
		selbtn.grid(column=2, row=1)
		cfmbtn0 = tk.Button(lf0, height=1, width=12, text="Confirm",
		                    command=self.init_btn_cb)
		cfmbtn0.grid(column=3, row=1)
		lf0.pack(fill=tk.BOTH, padx=2, pady=2)

		lf2 = tk.LabelFrame(parent, text='Set an Output Fasta File', height=60, width=1024)
		self.inpa1 = tk.Entry(lf2, width=128)
		self.inpa1.grid(column=1, row=1)
		selbtn = tk.Button(lf2, height=1, width=12, text="...",
		                   command=self.selbtn_saveas_cb('Set an Output Fasta File', self.inpa1))
		selbtn.grid(column=2,row=1)
		lf2.pack(fill=tk.BOTH, padx=2, pady=2)

		sf = tk.Frame(parent,height=400, width=1024, bg="#FFF")
		lf1 = tk.LabelFrame(sf, text='Set Input ID List', height=90, width=1024)
		self.inpa2 = ScrolledText(lf1, width=80, height=20, font="Monospace 10")
		self.inpa2.insert(tk.END, def_readme)
		self.inpa2.grid(column=1, row=1, ipadx=75, ipady=0)
		selbtn = tk.Button(lf1, height=8, width=8, text="...",
		                   command=self.selbtn_readf_cb('Set Input ID List', self.inpa2))
		selbtn.grid(column=2, row=1, ipady=100, sticky=tk.N)
		lf1.grid(column=1, row=1, sticky=tk.NW, ipadx=2, ipady=2)

		self.dialog = tk.BooleanVar(); self.header = tk.BooleanVar(); self.case = tk.BooleanVar()
		lf1 = tk.LabelFrame(sf,text="Other Options")
		dialogbtn = tk.Checkbutton(lf1, text="Just Show in Dialog",
		                           onvalue=True, offvalue=False,
		                           variable=self.dialog)
		dialogbtn.pack(anchor=tk.W)
		headerbtn = tk.Checkbutton(lf1, text="Fasta Header Pattern Match",
		                           onvalue=True, offvalue=False,
		                           variable=self.header)
		headerbtn.pack(anchor=tk.W)
		casebtn = tk.Checkbutton(lf1, text="Case Insensitive",
		                         onvalue=True, offvalue=False,
		                         variable=self.case)
		casebtn.pack(anchor=tk.W)
		lf1.grid(column=2, row=1, sticky=tk.NE, ipady=142, ipadx=4)
		sf.pack(fill=tk.BOTH, padx=2, pady=2)

		self.pbstyle = ttk.Style(parent)
		self.pbstyle.layout("LabeledProgressbar",
		         [('LabeledProgressbar.trough',
		           {'children': [('LabeledProgressbar.pbar',
		                          {'side': 'left', 'sticky': 'ns'}),
		                         ("LabeledProgressbar.label",   # label inside the bar
		                          {"sticky": ""})],
		           'sticky': 'nswe'})])

		self.progress = ttk.Progressbar(self.parent, mode='determinate', length=990,
		                                style="LabeledProgressbar")
		self.progress.pack(anchor=tk.S, ipadx=8)
		self.notice("There is no work to be done. ¯\\_(ツ)_/¯")

		startbtn = tk.Button(self.parent, text="Start", bg="#ffff00", height=4, width=1024,
		                     command=self.run)
		startbtn.pack(anchor=tk.S)

	def show(self):
		self.parent.mainloop()

def cb_fasta_extract():
	FastaExtractUI().show()

if __name__ == '__main__':
	cb_fasta_extract()
