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

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from threading import Thread
from fasta import FastaReader

class FastaExtractUI():
	input_file = None
	status = False

	def update_progress_cb(self, title, percent):
		self.progress_bar.set_text(title)
		if percent >= 0:
			self.progress_bar.set_fraction(percent)
		else:
			self.progress_bar.pulse()

	def update_state_cb(self, status, desc):
		if status == 1:
			self.status = True
			self.status_label.set_markup(f'<span foreground="green">{desc}</span>')
		elif status == 2:
			self.status = False
			self.status_label.set_markup(f'<span foreground="yellow">{desc}</span>')

	def init_btn_clicked(self, btn):
		if not self.input_file or (hasattr(self, 'reader') and not self.status):
			return

		self.status = False
		self.reader = FastaReader(self.input_file,
		                          { 'progress': self.update_progress_cb,
		                          	'state': self.update_state_cb },
		                          int(self.thread_count_entry.get_text()))

	def input_file_chose(self, chooser):
		self.input_file = chooser.get_filename()

	def script_file_chose(self, chooser):
		buf = self.source_view.get_buffer()
		with open(chooser.get_filename(), 'r') as f:
			buf.set_text(f.read())

	def outp_btn_clicked(self, btn):
		dialog = Gtk.FileChooserDialog(title="Please choose an output file",
                                       action=Gtk.FileChooserAction.SAVE)
		dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

		dialog.set_do_overwrite_confirmation(True)
		dialog.set_local_only(True)
		dialog.set_current_name('Untitled Gene.fasta')

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			self.output_file_entry.set_text(dialog.get_filename())
		dialog.destroy()

	def exec_btn_clicked(self, btn):
		if not self.status:
			return

		self.status = False
		self.status_label.set_markup(f'<span foreground="blue">Searching, Please wait</span>')

		t = Thread(target=self.reader.search, args=(self.source_view.get_buffer().get_text(),))
		t.start()

	def __init__(self):
		builder = Gtk.Builder()
		builder.add_from_file('res/fasta_extract.glade')

		self.view = builder.get_object('mainview')
		self.source_view = builder.get_object('source')
		self.output_file_entry = builder.get_object('output_file')
		self.thread_count_entry = builder.get_object('thread_count')
		self.status_label = builder.get_object('status_label')
		self.progress_bar = builder.get_object('progressbar')

		self.outp_btn = builder.get_object('save_file_btn')
		self.outp_btn.connect('clicked', self.outp_btn_clicked)
		self.init_btn = builder.get_object('init_btn')
		self.init_btn.connect('clicked', self.init_btn_clicked)
		self.exec_btn = builder.get_object('exec_btn')
		self.exec_btn.connect('clicked', self.exec_btn_clicked)
		self.input_file_chooser = builder.get_object('input_file')
		self.input_file_chooser.connect('file-set', self.input_file_chose)
		self.source_file_chooser = builder.get_object('source_file')
		self.source_file_chooser.connect('file-set', self.script_file_chose)

def sig_fasta_extract(notebook):
	ui = FastaExtractUI()
	page = notebook.append_page(ui.view, Gtk.Label(label='FASTA Extract'))
	notebook.set_current_page(page)

uihandlers = {
	'fasta_extract_activate': sig_fasta_extract
}