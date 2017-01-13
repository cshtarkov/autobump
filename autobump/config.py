"""Provide functions that get configuration parameters.

Methods check these sources in succession and stop at the first one:

1. Environment variables.
2. Configuration file.
3. Defaults.
"""
import os
import re
import configparser
from copy import deepcopy

CONFIG_FILE = "autobump.ini"
falsy = re.compile(r"^([Ff](alse)?|0+)$")
defaults = {
    "autobump": {
        "git": "git",
        "clojure": "clojure",
        "java": "java"
    },

    "python": {
        "use_structural_typing": True
    },

    "java": {
        "lazy_type_checking": False
    },

    "clojure": {
        "lazy_type_checking": True
    },
}


def get(category, name):
    """Get the value of a configuration parameter
    by checking several sources in succession."""
    value = None

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

    return value


def make_get(category, name):
    """Return a no-arguments function that
    gets the value of a parameter."""
    return lambda: get(category, name)


class config_overrides(object):
    """Context manager that temporary overrides
    the values of some parameters."""
    def __init__(self, overrides):
        self.overrides = overrides

    def __enter__(self):
        global defaults
        self.previous = deepcopy(defaults)
        defaults = {**defaults, **self.overrides}

    def __exit__(self, *args):
        global defaults
        defaults = deepcopy(self.previous)


def with_config_override(category, name, value):
    """Decorator that overrides the value of just
    one parameter."""
    def wrap(f):
        def wrapped(*args, **kwargs):
            with config_overrides({category: {name: value}}):
                f(*args, **kwargs)
        return wrapped
    return wrap


git = make_get("autobump", "git")
clojure = make_get("autobump", "clojure")
java = make_get("autobump", "java")

use_structural_typing = make_get("python", "use_structural_typing")

java_lazy_type_checking = make_get("java", "lazy_type_checking")

clojure_lazy_type_checking = make_get("clojure", "lazy_type_checking")
