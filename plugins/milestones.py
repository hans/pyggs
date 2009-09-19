# -*- coding: utf-8 -*-
"""
    plugins/milestones.py - Table of accomplished milestones.
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

import re

from . import base


class Plugin(base.Plugin):
    def __init__(self, master):
        base.Plugin.__init__(self, master)
        self.dependencies = ["stats", "cache", "myfinds"]
        self.about = _("List of accomplished milestones.")


    def setup(self):
        config = self.master.config

        config.assertSection(self.NS)
        config.defaults[self.NS] = {}
        config.defaults[self.NS]["milestones"] = "1,50,[0-9]+00,LAST"
        print("    {0}:".format(_("Please specify milestones as coma separeted list. You can also use regular expressions, e.g. '[0-9]+00' matches 100, 200, 300, ... and magic word LAST means the last found cache.")))
        config.update(self.NS, "milestones", _("Milestones"), validate=True)


    def run(self):
        templateData = {"milestones":self.getMilestones()}
        self.stats.registerTemplate(":stats.milestones", templateData)


    def getMilestones(self):
        result = []
        myFinds = self.myfinds.storage.select("SELECT * FROM myFinds ORDER BY date ASC, sequence ASC")
        milestones = self.master.config.get(self.NS, "milestones").split(",")
        for i in range(0, len(milestones)):
            if milestones[i] == "LAST":
                milestones[i] = "^{0:d}$".format(len(myFinds))
            else:
                milestones[i] = "^{0}$".format(milestones[i].strip())
        for cache in myFinds:
            for milestone in milestones:
                match = re.match(milestone, str(cache["sequence"]))
                if match is not None:
                    self.log.debug("Cache {0} matches expr {1}.".format(cache["sequence"], milestone))
                    row = dict(cache)
                    row.update(self.cache.storage.select([cache["guid"]])[0])
                    result.append(row)
        return result
