"""Provide functions that get configuration parameters.

Methods check these sources in succession and stop at the first one:

1. Environment variables.
2. Configuration file.
3. Defaults.
"""
import os
import configparser
from copy import deepcopy

defaults = {
    "git": "git",
    "clojure": "clojure",
    "java": "java",
}


def get(name):
    """Get the value of a parameter
    by checking environment variables, the configuration
    file, and the defaults in succession."""
    # Check environment variables.
    env_name = "AB_" + name.upper()
    if env_name in os.environ:
        return os.environ[env_name]

    # Check configuration file.
    config = configparser.ConfigParser()
    config.read("autobump.ini")
    return config.get("autobump", name, fallback=defaults[name])


def make_get(name):
    """Return a no-arguments function that
    gets the value of a parameter."""
    def _get():
        return get(name)
    return _get
class config_overrides(object):

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
    def wrap(f):
        def wrapped(*args, **kwargs):
            with config_overrides({category: {name: value}}):
                f(*args, **kwargs)
        return wrapped
    return wrap


git = make_get("git")
clojure = make_get("clojure")
java = make_get("java")
