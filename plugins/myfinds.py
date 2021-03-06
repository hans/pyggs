# -*- coding: utf-8 -*-
"""
    plugins/myfinds.py - handles myFinds database for each profile.
    Copyright (C) 2009-2011 Petr Morávek

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
import time

from . import base


class Plugin(base.Plugin):
    def __init__(self, master):
        base.Plugin.__init__(self, master)
        self.about = _("Storage for My Finds data from geocaching.com profile.")


    def setup(self):
        config = self.master.config

        config.assertSection(self.NS)
        config.defaults[self.NS] = {}
        config.defaults[self.NS]["timeout"] = "24"
        config.update(self.NS, "timeout", _("My Finds data timeout in hours:"), validate=lambda val: None if val.isdigit() else _("Use only digits, please."))


    def onPyggsUpgrade(self, oldVersion):
        # Force update of myFinds database
        self.log.warn(_("New version of Pyggs: forcing database update."))
        self.storage.delEnv("lastcheck")
        return True


    def prepare(self):
        self.storage = Storage(self.master.profileStorage.filename, self)
        base.Plugin.prepare(self)
        self.config["timeout"] = int(self.config["timeout"])
        self.master.registerHandler("myFinds", self.parseMyFinds)


    def parseMyFinds(self, myFinds):
        """Update MyFinds database"""
        self.log.info(_("Updating MyFinds database."))
        myFinds = list(myFinds)
        if len(myFinds) == 0:
            if self.storage.query("SELECT COUNT(*) FROM myfinds")[0][0] == 0:
                self.log.critical(_("Got zero myFinds records (bug?) and local databse is empty too."))
            else:
                self.log.error(_("Got zero myFinds records (bug?), leaving old database in place."))
        else:
            self.storage.update(myFinds)



class Storage(base.Storage):
    def __init__(self, filename, plugin):
        base.Storage.__init__(self, filename, plugin)
        self.valid = None


    def createTables(self):
        """Create necessary tables"""
        base.Storage.createTables(self)
        self.query("""CREATE TABLE IF NOT EXISTS myfinds (
                guid varchar(36) NOT NULL,
                sequence int(4) NOT NULL,
                date date NOT NULL,
                luid VARCHAR(36) NOT NULL,
                PRIMARY KEY (guid,sequence))""")


    def checkValidity(self):
        """Checks, if the database data are not out of date"""
        if self.valid is not None:
            return self.valid

        lastCheck = self.getEnv("lastcheck")
        timeout = self.plugin.config["timeout"]*3600
        if lastCheck is not None and float(lastCheck)+timeout >= int(time.time()) and self.query("SELECT COUNT(*) FROM myfinds")[0][0] > 0:
            self.valid = True
        else:
            self.log.info(_("MyFinds database out of date, initiating refresh."))
            self.plugin.master.parse("myFinds")

        return self.valid


    def update(self, data):
        """Update MyFinds database by data"""
        self.query("DROP TABLE myfinds")
        self.createTables()
        db = self.getDb()
        cur = db.cursor()
        for i in range(len(data)):
            cur.execute("INSERT INTO myfinds(guid, sequence, date, luid) VALUES(?,?,?,?)", (data[i].cache["guid"], i+1, data[i].date, data[i].luid))
        db.commit()
        db.close()
        self.setEnv("lastcheck", int(time.time()))
        self.valid = True


    def select(self, query="SELECT * FROM myfinds"):
        """Selects data from database, performs update if neccessary"""
        self.checkValidity()
        return self.query(query)


    def getList(self):
        """Get list of guids of MyFinds"""
        result = self.select("SELECT guid FROM myfinds")
        myFinds = []
        for row in result:
            myFinds.append(row["guid"])
        return myFinds
