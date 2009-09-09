# -*- coding: utf-8 -*-
"""
    plugins/gcczUpdater.py - Updates MyFinds database at geocaching.cz.
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

from .base import base
import urllib
from hashlib import md5

class gcczUpdater(base):
    def __init__(self, master):
        base.__init__(self, master)
        self.dependencies = ["myFinds", "cache", "gccz"]
        self.about        = _("Updates user's finds in geocaching.cz database.")


    def setup(self):
        config = self.master.config

        config.assertSection(self.NS)
        config.defaults[self.NS] = {}
        config.defaults[self.NS]["force"] = "n"
        config.update(self.NS, "force", _("Force my finds update on every run"), validate=["y","n"])


    def finish(self):
        finds = ""
        for row in self.myFinds.storage.select("SELECT date, guid FROM myFinds"):
            if len(finds):
                finds = "%s|" %finds
            details = self.cache.storage.select([row["guid"]])[0]
            finds = "%s%s;%s;%s;%s" % (finds,details["waypoint"], row["date"], details["lat"], details["lon"])
        config = self.master.config

        hash = "%s" % finds
        hash = md5(hash.encode()).hexdigest()
        if config.get(self.NS, "force") != "y":
            hash_old = self.master.profileStorage.getEnv("%s.hash" % self.NS)
            if hash == hash_old:
                self.log.info("Geocaching.cz database seems already up to date, skipping update.")
                return

        data = {"a":"nalezy","u":config.get(self.gccz.NS, "username"),"p":config.get(self.gccz.NS, "password"),"d":finds}
        result = urllib.request.urlopen("http://www.geocaching.cz/api.php", urllib.parse.urlencode(data))
        result = result.read().decode().splitlines()

        succ   = False
        for row in result:
            row = row.split(":")
            if row[0] == "info" and row[1] == "ok":
                succ = True
                break

        if succ is False:
            self.log.error("Unable to update Geocaching.cz database.")
            self.log.debug("Response: %s" % result)
        else:
            self.master.profileStorage.setEnv("%s.hash" % self.NS, hash)
            self.log.info("Geocaching.cz database successfully updated.")
