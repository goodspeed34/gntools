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

import gettext
import locale
from os.path import abspath, dirname, join, realpath

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GtkSource, GObject

# Register GtkSourceView
GObject.type_register(GtkSource.View)

handlers = {}
from fastaui import uihandlers
handlers |= uihandlers

# Initialize localization
where_am_i = abspath(dirname(realpath(__file__)))
local_dir = join(where_am_i, 'locales')
locale.setlocale(locale.LC_ALL, '')
try:
    locale.bindtextdomain('GNtools', local_dir)
except:
    pass # Windows Specfic
gettext.bindtextdomain('GNtools', local_dir)
gettext.textdomain('GNtools')
_ = gettext.gettext

def open_about_dialog(menu_item):
    builder = Gtk.Builder()
    builder.set_translation_domain('GNtools')
    builder.add_from_file('res/about.glade')
    dialog = builder.get_object('dialog')
    dialog.run()
    dialog.destroy()

class Launcher():
    def __init__(self):
        builder = Gtk.Builder()
        builder.set_translation_domain('GNtools')
        builder.add_from_file('res/main.glade')
        builder.connect_signals(handlers)

        self.window = builder.get_object('mainwin')

        self.fasta_extract_btn = builder.get_object('')

        self.about_btn = builder.get_object('about_btn')
        self.about_btn.connect('activate', open_about_dialog)

    def show(self):
        self.window.show()
    

launcher = Launcher()
launcher.window.connect('destroy', Gtk.main_quit)
launcher.show()
Gtk.main()