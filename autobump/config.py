# Copyright 2016-2017 Christian Shtarkov
#
# This file is part of Autobump.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
"""
Provide functions that get configuration parameters.

Methods check these sources in succession and stop at the first one:

1. Environment variables.
2. Configuration file.
3. Defaults.

Additionally, configuration may be overriden at runtime by using
the context manager and decorator defined here.
"""

import os
import re
import logging
import configparser
from io import StringIO
from copy import deepcopy

logger = logging.getLogger(__name__)

CONFIG_FILE = "autobump.ini"
falsy = re.compile(r"^([Ff](alse)?|0+)$")
defaults = {
    "autobump": {
        "git": "git",
        "hg": "hg",
        "clojure": "clojure",
        "java": "java",
        "javac": "javac"
    },

    "only_consider": {
        "files": [],
        "dirs": [],
        "entities": []
    },

    "ignore": {
        "files": ["project.clj", "setup.py", "setupegg.py"],
        "dirs": [".git", ".hg", "test", "tests", "doc", "docs"],
        "entities": [],
    },

    "python": {
        "omit_on_error": False,
        "structural_typing": True,
        "type_hinting": True
    },

    "java_native": {
        "classpath": ""
    },

    "java_ast": {
        "error_on_external_types": True,
        "omit_on_error": False
    },

    "clojure": {
        "classpath": ""
    },
}
cached = dict()


def _value_to_string(value):
    if isinstance(value, list):
        return '\n'.join(value)
    if isinstance(value, bool):
        return str(value)
    return value


def export_config():
    """Returns the contents of the current configuration
    as an INI file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    for category in defaults:
        for name in defaults[category]:
            if not config.has_section(category):
                config.add_section(category)
            config[category][name] = _value_to_string(get(category, name))
    ini = StringIO()
    config.write(ini)
    return ini.getvalue()


def get(category, name):
    """Get the value of a configuration parameter
    by checking several sources in succession."""
    value = cached.get((category, name), None)
    if value is not None:
        return value

    # Check environment variables.
    env_name = "AB_" + name.upper()
    if env_name in os.environ:
        value = os.environ[env_name]

    # Check configuration file.
    else:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        value = config.get(category, name, fallback=defaults[category][name])

    if falsy.match(str(value)):
        value = False

    logger.info("{}/{} is {}"
                .format(category, name, (value if value != "" else "not set")))

    cached[(category, name)] = value
    return value


def _make_get(category, name):
    """Return a no-arguments function that
    gets the value of a parameter."""
    return lambda: get(category, name)


class config_overrides(object):
    """Context manager that temporary overrides
    the values of some parameters."""
    def __init__(self, overrides):
        self.overrides = overrides

    def __enter__(self):
        global cached
        self.previous = deepcopy(cached)
        for category in self.overrides:
            for name in self.overrides[category]:
                set(category, name, self.overrides[category][name])

    def __exit__(self, *args):
        global cached
        cached = deepcopy(self.previous)


def config_override(category, name, value):
    """Decorator that overrides the value of just
    one parameter."""
    def wrap(f):
        def wrapped(*args, **kwargs):
            with config_overrides({category: {name: value}}):
                return f(*args, **kwargs)
        return wrapped
    return wrap


def set(category, name, value):
    """Permanently override the value of an option."""
    global cached
    cached[(category, name)] = value


# autobump
# TODO: move these to respective handlers
# or rename this to "executables"
git = _make_get("autobump", "git")
hg = _make_get("autobump", "hg")
clojure = _make_get("autobump", "clojure")
java = _make_get("autobump", "java")
javac = _make_get("autobump", "javac")


# ignore
def ignored(what, name):
    """Check whether something should be ignored."""
    only_consider_lit = get("only_consider", what)
    ignored_lit = get("ignore", what)
    if isinstance(only_consider_lit, str):
        only_consider_lit = only_consider_lit.splitlines()
    if isinstance(ignored_lit, str):
        ignored_lit = ignored_lit.splitlines()

    if len(only_consider_lit) > 0:
        return name not in only_consider_lit

    return name in ignored_lit


def file_ignored(name):
    """Check whether a file should be ignored."""
    return ignored("files", name)


def dir_ignored(name):
    """Check whether a directory should be ignored."""
    return ignored("dirs", name)


def entity_ignored(name):
    """Check whether an entity should be ignored."""
    return ignored("entities", name)


# python
python_omit_on_error = _make_get("python", "omit_on_error")
structural_typing = _make_get("python", "structural_typing")
type_hinting = _make_get("python", "type_hinting")


# java_native
def java_classpath():
    # The classpath is special, because we need to append
    # the working directory so that Autobump's utilities like
    # the Inspector and TypeCompatibilityChecker work.
    value = get("java_native", "classpath")
    return (value + ":.:") if value != "" else ""


# java_ast
java_error_on_external_types = _make_get("java_ast", "error_on_external_types")
java_omit_on_error = _make_get("java_ast", "omit_on_error")

# clojure
clojure_classpath = _make_get("clojure", "classpath")
