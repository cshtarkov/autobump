"""Provide functions that get configuration parameters.

Methods check these sources in succession and stop at the first one:

1. Environment variables.
2. Configuration file.
3. Defaults.
"""
import os
import configparser

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


git = make_get("git")
clojure = make_get("clojure")
java = make_get("java")
