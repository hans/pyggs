#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    pyggs.py - base script for Pyggs.
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

from collections import OrderedDict
import gettext
import logging
from optparse import OptionParser
import os
import sqlite3

from libs.gcparser import GCparser

from ColorConsole import ColorConsole
import Configurator
import plugins
from Templar import Templar

# Autodetect translations
localeDir = os.path.join(os.path.dirname(__file__), "translations")
langs = {}
for lang in os.listdir(localeDir):
    if os.path.isdir(os.path.join(localeDir, lang)):
        langs[lang] = gettext.translation("pyggs", localedir=localeDir, codeset="utf-8", languages=[lang])
gettext.install("pyggs", localedir=localeDir, codeset="utf-8")


class Pyggs(GCparser):
    def __init__(self):
        # Setup console output logging
        console = ColorConsole(fmt="%(levelname)-8s %(name)-30s %(message)s")
        rootlog = logging.getLogger("")
        rootlog.addHandler(console)
        rootlog.setLevel(logging.WARN)

        # Parse command line arguements
        optp = OptionParser()
        optp.add_option("-q","--quiet", help=_("set logging to ERROR"), action="store_const", dest="loglevel", const=logging.ERROR, default=logging.WARN)
        optp.add_option("-v","--verbose", help=_("set logging to INFO"), action="store_const", dest="loglevel", const=logging.INFO)
        optp.add_option("-d","--debug", help=_("set logging to DEBUG"), action="store_const", dest="loglevel", const=logging.DEBUG)
        optp.add_option("-D","--Debug", help=_("set logging to ALL"), action="store_const", dest="loglevel", const=0)
        optp.add_option("-w","--workdir", dest="workdir", default="~/.geocaching", help=_("set working directory, default is {0}").format("~/.geocaching"))
        optp.add_option("-p","--profile", dest="profile", help=_("choose profile"))
        self.opts,args = optp.parse_args()

        rootlog.setLevel(self.opts.loglevel)
        self.log = logging.getLogger("Pyggs")

        if self.opts.profile is None:
            self.log.error(_("You have to select a profile."))
            self.die()

        self.workDir = os.path.expanduser(self.opts.workdir)
        self.plugins = {}


    def setup(self):
        """Setup script"""
        # Setup working directory structure
        if not os.path.isdir(self.workDir):
            os.mkdir(self.workDir)
        if not os.path.isdir(self.workDir):
            self.log.critical(_("Unable to create working directory '{0}'.").format(self.workDir))
            self.die()

        parserDir = os.path.join(self.workDir, "parser")
        if not os.path.isdir(parserDir):
            os.mkdir(parserDir)
        pyggsDir = os.path.join(self.workDir, "pyggs")
        if not os.path.isdir(pyggsDir):
            os.mkdir(pyggsDir)
        if not os.path.isdir(parserDir) or not os.path.isdir(pyggsDir):
            self.log.critical(_("Unable to set up base directory structure in working directory '{0}'.").format(self.workDir))
            self.die()

        self.log.info("Working directory is '{0}'.".format(self.workDir))

        profileDir = os.path.join(pyggsDir, self.opts.profile)
        if not os.path.isdir(profileDir):
            os.mkdir(profileDir)
        if not os.path.isdir(profileDir):
            self.log.critical(_("Unable to create profile directory '{0}'.").format(profileDir))
            self.die()

        # Let's ask some questions and create config
        configFile = os.path.join(profileDir, "config.cfg")
        self.config = config = Configurator.Profile(configFile)
        langs = globals()["langs"]
        lang = config.get("general", "language")
        if lang:
            langs[lang].install()

        print(_("Let's setup your profile named '{0}'.").format(self.opts.profile))

        # General section
        config.assertSection("general")
        print()
        print("  {0}:".format(_("General options")))
        config.update("general", "language", _("Please, select user interface language"), validate=list(langs.keys()))
        langs[config.get("general", "language")].install()

        print("    {0}:\n".format(_("Enter your home coordinates in degrees as deciamal number (N means positive value, S negative; E means positive value, W negative)")))
        config.update("general", "homelat", _("Latitude"), validate=True)
        config.update("general", "homelon", _("Laongitude"), validate=True)

        # Geocaching.com section
        config.assertSection("geocaching.com")
        print()
        print("  Geocaching.com:")
        config.update("geocaching.com", "username", _("Username"), validate=True)
        config.update("geocaching.com", "password", _("Password"), validate=True)

        # Output section
        themesDir = templatesDir = [pyggsDir, os.path.dirname(__file__)]
        templates = self.detectTemplates(templatesDir)
        themes = self.detectThemes(themesDir)
        config.assertSection("output")
        print()
        print("  {0}:".format(_("Output")))
        print("    {0}:\n      * {1}".format(_("Templates are looked up in 'templates' subdirectory of these paths (consecutively)"), "\n      * ".join(templatesDir)))
        config.update("output", "template", _("Template"), validate=templates)
        print("    {0}:\n      * {1}".format(_("Themes are looked up in 'themes' subdirectory of these paths (consecutively)"), "\n      * ".join(themesDir)))
        config.update("output", "theme", _("Theme"), validate=themes)
        config.update("output", "directory", _("Directory"), validate=True)

        # Plugins section
        installedPlugins = self.detectPlugins()
        config.assertSection("plugins")
        print()
        print("  {0}:".format(_("Plugins")))
        for plugin in installedPlugins:
            self.loadPlugin(plugin)
            print("    Plugin {0}: {1}".format(plugin, self.plugins[plugin].about))
            config.update("plugins", plugin, _("Enable"), validate=["y", "n"])
        for plugin in config.options("plugins"):
            if plugin not in installedPlugins:
                logging.debug("Removing not installed plugin {0}.".format(plugin))
                config.remove_option("plugins", plugin)

        # Check plugins deps
        print()
        print("  Checking plugins dependency tree...")
        self.plugins = {}
        self.loadPlugins()

        # Plugin configuration section
        plugins = list(self.plugins.keys())
        plugins.sort()
        for plugin in plugins:
            if hasattr(self.plugins[plugin], "setup"):
                print()
                print("  {0}:".format(_("Configuration of '{0}' plugin").format(plugin)))
                self.plugins[plugin].setup()

        config.save()
        print()
        print(_("Note: You can always edit these setings by re-running setup.py script, or by hand in file {0}.").format(configFile))


    def run(self):
        """Run pyggs"""
        # Setup working directory structure
        parserDir = os.path.join(self.workDir, "parser")
        pyggsDir = os.path.join(self.workDir, "pyggs")
        profileDir = os.path.join(pyggsDir, self.opts.profile)
        if not os.path.isdir(self.workDir) or not os.path.isdir(parserDir) or not os.path.isdir(pyggsDir) or not os.path.isdir(profileDir):
            self.log.error(_("Working directory '{0}' is not set up properly, please run setup.py script.").format(self.workDir))
            self.die()

        self.log.info("Working directory is '{0}'.".format(self.workDir))

        configFile = os.path.join(profileDir, "config.cfg")
        if not os.path.isfile(configFile):
            self.log.error(_("Configuration file not found for profile '{0}', please run setup.py script.").format(self.opts.profile))
            self.die()
        self.config = config = Configurator.Profile(configFile)

        # Init GCparser, and redefine again self.log
        GCparser.__init__(self, username=config.get("geocaching.com", "username"), password=config.get("geocaching.com", "password"), dataDir=parserDir)
        self.log = logging.getLogger("Pyggs")

        self.globalStorage = Storage(os.path.join(pyggsDir, "storage.db"))
        self.profileStorage = Storage(os.path.join(profileDir, "storage.db"))

        self.handlers = {}
        self.pages = {}
        self.loadPlugins()
        self.makeDepTree()

        # Prepare plugins
        for plugin in self.plugins:
            if hasattr(self.plugins[plugin], "prepare"):
                self.log.info("Preparing plugin {0}...".format(plugin))
                self.plugins[plugin].prepare()

        # Run plugins
        for plugin in self.plugins:
            if hasattr(self.plugins[plugin], "run"):
                self.log.info("Running plugin {0}...".format(plugin))
                self.plugins[plugin].run()

        # Render output
        self.templar = Templar(self)
        self.templar.outputPages(self.pages)

        # Finish plugins
        for plugin in self.plugins:
            if hasattr(self.plugins[plugin], "finish"):
                self.log.info("Finishing plugin {0}...".format(plugin))
                self.plugins[plugin].finish()


    def registerPage(self, output, template, menutemplate, context, layout=True):
        """Register page for rendering"""
        self.pages[output] = {"template":template, "menu":menutemplate, "context":context, "layout":layout}


    def registerHandler(self, parsername, handler):
        """Register handler that gets Parser object, when parse() method is called"""
        try:
            self.handlers[parsername].append(handler)
        except KeyError:
            self.handlers[parsername] = []
            self.handlers[parsername].append(handler)


    def parse(self, name, *args, **kwargs):
        """Create parser and return it to every registered handler"""
        handlers = self.handlers.get(name)
        if handlers is not None:
            parser = GCparser.parse(self, name, *args, **kwargs)
            for handler in handlers:
                handler(parser)


    def loadPlugin(self, name):
        """ Load a plugin - name is the file and class name"""
        if name not in globals()["plugins"].__dict__:
            self.log.info("Loading plugin '{0}'.".format(name))
            __import__(self.pluginModule(name))
        self.plugins[name] = getattr(globals()["plugins"].__dict__[name], name)(self)
        return True


    def pluginModule(self, name):
        return "{0}.{1}".format(globals()["plugins"].__name__, name)


    def loadPlugins(self):
        """Loads all plugins and their dependencies"""
        for plugin in self.config.options("plugins"):
            if self.config.get("plugins", plugin) == "y":
                self.loadPlugin(plugin)

        for plugin in list(self.plugins.keys()):
            self.loadWithDeps(plugin)


    def loadWithDeps(self, name):
        """Load plugin and its dependencies"""
        if name not in self.plugins:
            self.loadPlugin(name)
            self.config.set("plugins", name, "y")
        for dep in self.plugins[name].dependencies:
            if dep not in self.plugins:
                self.log.warn("'{0}' plugin pulled in as dependency by '{1}'.".format(dep, name))
                self.loadWithDeps(dep)


    def makeDepTree(self):
        """Rearragne the order of self.plugins according to dependencies"""
        plugins = OrderedDict()
        fs = 0
        while len(self.plugins):
            fs = fs +1
            if fs > 100:
                self.log.warn("Cannot make plugin depedency tree for {0}. Possible circular dependencies.".format(",".join(list(self.plugins.keys()))))
                for plugin in list(self.plugins.keys()):
                    plugins[plugin] = self.plugins.pop(plugin)

            for plugin in list(self.plugins.keys()):
                if self.pluginDepsLoaded(list(plugins.keys()), self.plugins[plugin].dependencies):
                    plugins[plugin] = self.plugins.pop(plugin)

        self.plugins = plugins


    def pluginDepsLoaded(self, loaded, dependencies):
        """Are all required dependencies of plugin in loaded?"""
        ret = True
        for dep in dependencies:
            if dep not in loaded:
                ret = False
                break
        return ret


    def detectTemplates(self, dirs):
        """Search for available templates"""
        templates = []
        for dir in dirs:
            if os.path.isdir(os.path.join(dir, "templates")):
                for template in os.listdir(os.path.join(dir, "templates")):
                    if os.path.isdir(os.path.join(dir, "templates", template)):
                        templates.append(template)
        return templates


    def detectThemes(self, dirs):
        """Search for available themes"""
        themes = []
        for dir in dirs:
            if os.path.isdir(os.path.join(dir, "themes")):
                for theme in os.listdir(os.path.join(dir, "themes")):
                    if os.path.isfile(os.path.join(dir, "themes", theme)):
                        themes.append(theme.replace(".theme", ""))
        return themes


    def detectPlugins(self):
        """Search for available plugins"""
        plugins = []
        for plugin in os.listdir(os.path.join(os.path.dirname(__file__), "plugins")):
            if plugin.endswith(".py") and not plugin.startswith("__init__") and not plugin.startswith("example") and plugin[:-3] != "base":
                plugins.append(plugin[:-3])
        plugins.sort()
        return plugins



class Storage(object):
    def __init__(self, filename):
        self.log = logging.getLogger("Pyggs.Storage")
        self.filename = filename
        self.createEnvironment()


    def getDb(self):
        """Return a new DB connection"""
        con = sqlite3.connect(self.filename)
        con.row_factory = sqlite3.Row
        return con


    def fetchAssoc(self, result, format="#"):
        """Fetch result to a dictionary"""
        if format == "":
            format = "#"
        format = format.split(",")

        if len(result) == 0:
            if format[0] == "#":
                return []
            else:
                return OrderedDict()

        for field in format:
            if field != "#" and field not in result[0].keys():
                self.log.error("There is no field '{0}' in the result set.".format(field))
                return []

        # make associative tree
        data = OrderedDict()
        data["result"] = None
        for row in result:
            x = data
            i = "result"
            for field in format:
                if field == "#":
                    if x[i] is None:
                        x[i] = []
                    x[i].append(None)
                    x = x[i]
                    i = len(x)-1
                else:
                    if x[i] is None:
                        x[i] = OrderedDict()
                    if x[i].get(row[field]) is None:
                        x[i][row[field]] = None
                    x = x[i]
                    i = row[field]
            x[i] = dict(row)

        return data["result"]


    def createEnvironment(self):
        """If Environment table doesn't exist, create it"""
        db = self.getDb()
        db.execute("CREATE TABLE IF NOT EXISTS environment (variable VARCHAR(256) PRIMARY KEY, value VARCHAR(256))")
        db.close()


    def setEnv(self, variable, value):
        """insert or update env variale"""
        db = self.getDb()
        cur = db.cursor()
        cur.execute("SELECT * FROM environment WHERE variable=?", (variable,))
        if (len(cur.fetchall()) > 0):
            cur.execute("UPDATE environment SET value=? WHERE variable=?", (value, variable))
        else:
            cur.execute("INSERT INTO environment(variable, value) VALUES(?,?)", (variable, value))
        db.commit()
        db.close()


    def getEnv(self, variable):
        """get env variable"""
        db = self.getDb()
        cur = db.cursor()
        cur.execute("SELECT value FROM environment WHERE variable=? LIMIT 1", (variable,))
        value = cur.fetchone()
        db.close()
        if value is not None:
            value = value[0]
        return value


    def delEnv(self, variable):
        """delete env variale"""
        db = self.getDb()
        cur = db.cursor()
        cur.execute("DELETE FROM environment WHERE variable=? LIMIT 1", (variable,))
        db.commit()
        db.close()




if __name__ == "__main__":
    pyggs = Pyggs()
    pyggs.run()
