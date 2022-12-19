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
from gi.repository import Gtk, Gdk

import tempfile
from threading import Thread
from fasta import FastaReader

from gettext import gettext as _

def_readme = _('''# README (`#' will start a line of comment)
# Single Gene Extract:
#   Unigene_1
# Chromosome Range Exract:
#   Chr0	100	200
# Chromosome Range Extract and Rename:
#   BabyChr	Chr0	200	100
''')

class FastaExtractUI():
	input_file = None
	status = False

	def error_out(self, title, message):
		dialog = Gtk.MessageDialog(flags=0,
		                           transient_for=self.parent,
		                           message_type=Gtk.MessageType.ERROR,
		                           buttons=Gtk.ButtonsType.CANCEL,
		                           text=title)
		dialog.format_secondary_text(message)
		dialog.run()
		dialog.destroy()

	def update_progress_cb(self, title, percent):
		self.progress_bar.set_text(title)
		if percent >= 0:
			self.progress_bar.set_fraction(percent)
			if percent == 1 and self.execin:
				self.execin = False
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
		dialog = Gtk.FileChooserDialog(title=_("Please choose an output file"),
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

	def exec_finish_cb(self):
		self.status = True
		self.status_label.set_markup(f'<span foreground="green">OK</span>')

		if self.show_dialog.get_active():
			self.out_f.seek(0)
			builder = Gtk.Builder()
			builder.set_translation_domain('GNtools')
			builder.add_from_file('res/result_dialog.glade')

			dialog = builder.get_object('result_dialog')
			dialog.set_transient_for(self.parent)
			
			srcv = builder.get_object('src')
			buf = Gtk.TextBuffer()
			buf.set_text(self.out_f.read())
			srcv.set_buffer(buf)

			def exit(_):
				dialog.destroy()
			okbtn = builder.get_object('okbtn')
			okbtn.connect('clicked', exit)

			dialog.run()
			dialog.destroy()

		self.out_f.close()

	def exec_btn_clicked(self, btn):
		if not self.status:
			self.error_out(_("ERROR: Cannot perform the FASTA extract!"),
			               _("You must initialize first and wait until it completes."))
			return
		if self.output_file_entry.get_text() == '':
			if not self.show_dialog.get_active():
				self.error_out(_("ERROR: Cannot perform the FASTA extract!"),
				               _("You must either specify an output file or toggle Just Show In Dialog."))
				return

		self.execin = True
		self.status = False
		self.status_label.set_markup(_(f'<span foreground="blue">Searching, Please wait</span>'))

		if self.show_dialog.get_active():
			self.out_f = tempfile.TemporaryFile(mode='w+', encoding='utf-8')
		else:
			self.out_f = open(self.output_file_entry.get_text(), 'w+', encoding='utf-8')

		script_buf = self.source_view.get_buffer()
		t = Thread(target=self.reader.search,
		           args=(script_buf.get_text(script_buf.get_start_iter(),
		                                     script_buf.get_end_iter(),
		                                     False),
						 self.out_f,
		                 self.match_desc.get_active(),
		                 self.ignore_case.get_active()))
		t.start()

		sb = False
		while not sb:
			while Gtk.events_pending():
				Gtk.main_iteration()
				if self.execin == False:
					self.exec_finish_cb()
					sb = True
					break

	def __init__(self, parent):
		self.parent = parent
		builder = Gtk.Builder()
		builder.set_translation_domain('GNtools')
		builder.add_from_file('res/fasta_extract.glade')

		self.view = builder.get_object('mainview')
		self.source_view = builder.get_object('source')
		self.output_file_entry = builder.get_object('output_file')
		self.thread_count_entry = builder.get_object('thread_count')
		self.status_label = builder.get_object('status_label')
		self.progress_bar = builder.get_object('progressbar')

		self.source_view.get_buffer().set_text(def_readme)

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

		self.show_dialog = builder.get_object('show_in_dialog')
		self.ignore_case = builder.get_object('ignore_case')
		self.match_desc = builder.get_object('match_desc')

		self.execin = False

class FastaStatsUI():
	def __init__(self, parent):
		self.parent = parent
		builder = Gtk.Builder()
		builder.set_translation_domain('GNtools')
		builder.add_from_file('res/fasta_stats.glade')

		self.view = builder.get_object('mainview')


def ui_appender(klass, label):
	def x(notebook):
		ui = klass(notebook.get_toplevel())
		page = notebook.append_page(ui.view, Gtk.Label(label=label))
		notebook.set_current_page(page)
	return x

uihandlers = {
	'fasta_extract_activate': ui_appender(FastaExtractUI, _('FASTA Extract')),
	'fasta_stats_activate': ui_appender(FastaStatsUI, _('FASTA Stats')),
}