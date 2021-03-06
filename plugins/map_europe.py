# -*- coding: utf-8 -*-
"""
    plugins/map_europe.py - Map of caches found in Europe.
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

from . import base


class Plugin(base.Plugin):
    def __init__(self, master):
        base.Plugin.__init__(self, master)
        self.dependencies = ["stats", "myfinds", "cache", "gccz"]
        self.about = _("Map of Europe from geocaching.cz & world66.com.")


    def run(self):
        myFinds = self.myfinds.storage.getList()
        caches = self.cache.storage.getDetails(myFinds)
        caches = self.master.globalStorage.fetchAssoc(caches, "country,#")
        europe = {}
        europe["Albania"] = "AL"
        europe["Andorra"] = "AN"
        europe["Armenia"] = "AR"
        europe["Austria"] = "AU"
        europe["Azerbaijan"] = "AZ"
        europe["Belarus"] = "BL"
        europe["Belgium"] = "BE"
        europe["Bosnia and Herzegovina"] = "BH"
        europe["Bulgaria"] = "BU"
        europe["Croatia"] = "CR"
        europe["Cyprus"] = "CY"
        europe["Czech Republic"] = "CZ"
        europe["Denmark"] = "DK"
        europe["Estonia"] = "ES"
        europe["Finland"] = "FI"
        europe["France"] = "FR"
        europe["Georgia"] = "GG"
        europe["Germany"] = "GE"
        europe["Greece"] = "GR"
        europe["Hungary"] = "HU"
        europe["Iceland"] = "IC"
        europe["Ireland"] = "IENI"
        europe["Italy"] = "IT"
        europe["Latvia"] = "LE"
        europe["Liechtenstein"] = "LT"
        europe["Lithuania"] = "LI"
        europe["Luxembourg"] = "LU"
        europe["Macedonia"] = "MA"
        europe["Malta"] = "ML"
        europe["Moldovia"] = "MO"
        europe["Monaco"] = "MC"
        europe["Netherlands"] = "NL"
        europe["Norway"] = "NO"
        europe["Poland"] = "PO"
        europe["Portugal"] = "PT"
        europe["Romania"] = "RO"
        europe["Russia"] = "RU"
        europe["San Marino"] = "SA"
        europe["Serbia and Montenegro"] = "SM"
        europe["Slovenia"] = "SL"
        europe["Slovakia"] = "SV"
        europe["Spain"] = "SP"
        europe["Sweden"] = "SE"
        europe["Switzerland"] = "SW"
        europe["Turkey"] = "TU"
        europe["Ukraine"] = "UK"
        europe["United Kingdom"] = "ENSCWA"
        europe["Vatican City State"] = "VC"

        id = ""
        for country in list(caches.keys()):
            if country not in europe.keys():
                del(caches[country])
            else:
                id = id + europe[country]

        if len(caches) > 0:
            total = {"countries":len(caches), "caches":0}
            for country in caches:
                total["caches"] = total["caches"] + len(caches[country])
            templateData = {}
            templateData["total"] = total
            templateData["id"] = id
            templateData["uid"] = self.gccz.config["uid"]
            self.stats.registerTemplate(":stats.map_europe", templateData)
