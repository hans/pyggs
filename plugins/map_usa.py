# -*- coding: utf-8 -*-
"""
    plugins/map_usa.py - Map of caches found in the United States.
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
        self.dependencies = ["stats", "myfinds", "cache"]
        self.about = _("Map of the United States from world66.com.")


    def run(self):
        print('hello')
        myFinds = self.myfinds.storage.getList()
        caches = self.cache.storage.getDetails(myFinds)
        caches = self.master.globalStorage.fetchAssoc(caches, "province,#")

        usa = {
            "Alabama": "AL",
            "Alaska": "AK",
            "American Samoa": "AS",
            "Arizona": "AZ",
            "Arkansas": "AR",
            "California": "CA",
            "Colorado": "CO",
            "Connecticut": "CT",
            "Delaware": "DE",
            "District of Columbia": "DC",
            "Federated States of Micronesia": "FM",
            "Florida": "FL",
            "Georgia": "GA",
            "Guam": "GU",
            "Hawaii": "HI",
            "Idaho": "ID",
            "Illinois": "IL",
            "Indiana": "IN",
            "Iowa": "IA",
            "Kansas": "KS",
            "Kentucky": "KY",
            "Louisiana": "LA",
            "Maine": "ME",
            "Marshall Islands": "MH",
            "Maryland": "MD",
            "Massachusetts": "MA",
            "Michigan": "MI",
            "Minnesota": "MN",
            "Mississippi": "MS",
            "Missouri": "MO",
            "Montana": "MT",
            "Nebraska": "NE",
            "Nevada": "NV",
            "New Hampshire": "NH",
            "New Jersey": "NJ",
            "New Mexico": "NM",
            "New York": "NY",
            "North Carolina": "NC",
            "North Dakota": "ND",
            "Northern Mariana Islands": "MP",
            "Ohio": "OH",
            "Oklahoma": "OK",
            "Oregon": "OR",
            "Palau": "PW",
            "Pennsylvania": "PA",
            "Puerto Rico": "PR",
            "Rhode Island": "RI",
            "South Carolina": "SC",
            "South Dakota": "SD",
            "Tennessee": "TN",
            "Texas": "TX",
            "Utah": "UT",
            "Vermont": "VT",
            "Virgin Islands": "VI",
            "Virginia": "VA",
            "Washington": "WA",
            "West Virginia": "WV",
            "Wisconsin": "WI",
            "Wyoming": "WY"
        }

        id = ""
        for state in list(caches.keys()):
            if state not in usa.keys():
                del(caches[state])
            else:
                id = id + usa[state]

        #if len(caches) > 0:
            total = {"states":len(caches), "caches":0}
            for state in caches:
                total["caches"] = total["caches"] + len(caches[state])
            templateData = {}
            templateData["total"] = total
            templateData["id"] = id
            self.stats.registerTemplate(":stats.map_usa", templateData)
