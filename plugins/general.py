# -*- coding: utf-8 -*-
"""
    plugins/general.py - Prepare place to pug general statistics.
    Copyright (C) 2009 Petr Morávek

    This file is part of Pyggs.

    Pyggs is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Pyggs is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import logging

class general(object):
    def __init__(self, master):
        self.NS  = "plugin.general"
        self.log = logging.getLogger("Pyggs.%s" % self.NS)
        self.master = master

        self.dependencies = ["stats"]
        self.templateData = {"templates":{}}


    def setup(self):
        """Setup script"""
        pass


    def prepare(self):
        """Setup everything needed before actual run"""
        self.log.debug("Preparing...")

        self.master.plugins["stats"].registerTemplate(":stats.general", self.templateData)


    def run(self):
        """Run the plugin's code"""
        self.log.info("Running...")


    def registerTemplate(self, template, context):
        """Register template for rendering in General stats section"""
        self.templateData["templates"][template] = context
