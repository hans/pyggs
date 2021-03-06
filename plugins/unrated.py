# -*- coding: utf-8 -*-
"""
    plugins/unrated.py - Generates list with found but unrated caches.
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
        self.dependencies = ["myfinds", "gccz_myratings", "cache"]
        self.about = _("Generates page with the list of found but unrated caches by user.")


    def run(self):
        templateData = {"unrated":self.getUnrated()}
        self.master.registerPage("unrated.html", ":unrated", ":menu.unrated", templateData)


    def getUnrated(self):
        fetchAssoc = self.master.globalStorage.fetchAssoc

        myFinds = self.myfinds.storage.select()
        myFinds = fetchAssoc(myFinds, "guid")

        caches = self.cache.storage.getDetails(myFinds.keys())
        for cache in caches:
            cache.update(myFinds[cache["guid"]])
        caches = fetchAssoc(caches, "waypoint")

        myratings = self.gccz_myratings.storage.getRatings(caches.keys())
        myratings = list(fetchAssoc(myratings, "waypoint").keys())

        unrated = []
        for wpt in caches:
            if caches[wpt]["waypoint"] not in myratings:
                unrated.append(caches[wpt])
        return unrated
