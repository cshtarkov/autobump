"""Provide functions that get configuration parameters.

Methods check these sources in succession and stop at the first one:

1. Environment variables.
2. Configuration file.
3. Defaults.
"""
import os
import re
import logging
import configparser
from copy import deepcopy

logger = logging.getLogger(__name__)

CONFIG_FILE = "autobump.ini"
falsy = re.compile(r"^([Ff](alse)?|0+)$")
defaults = {
    "autobump": {
        "git": "git",
        "hg": "hg",
        "clojure": "clojure",
        "java": "java"
    },

    "ignore": {
        "files": [],
        "files_re": [r"^[Tt]est",
                     r"^project"],
        "dirs": [],
        "dirs_re": [r"^[Tt]est",
                    r"^[Tt]ool",
                    r"^[Dd]oc",
                    r"^[Ss]cript",
                    r"^[Ee]xample",
                    r"^.git$",
                    r"^.hg$"]
    },

    "python": {
        "omit_on_error": False,
        "structural_typing": True,
        "type_hinting": True
    },

    "java_native": {
        "lazy_type_checking": False,
        "classpath": ""
    },

    "java_ast": {
        "error_on_external_types": True
    },

    "clojure": {
        "lazy_type_checking": True,
        "classpath": ""
    },
}
cached = dict()


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
        global cached
        self.previous = deepcopy(defaults)
        for category in self.overrides:
            defaults[category] = {**defaults.get(category, dict()), **self.overrides[category]}
        cached = dict()

    def __exit__(self, *args):
        global defaults
        global cached
        defaults = deepcopy(self.previous)
        cached = dict()


def config_override(category, name, value):
    """Decorator that overrides the value of just
    one parameter."""
    def wrap(f):
        def wrapped(*args, **kwargs):
            with config_overrides({category: {name: value}}):
                f(*args, **kwargs)
        return wrapped
    return wrap


def set(category, name, value):
    """Permanently override the value of an option."""
    global cached
    cached[(category, name)] = value


# autobump
git = make_get("autobump", "git")
hg = make_get("autobump", "hg")
clojure = make_get("autobump", "clojure")
java = make_get("autobump", "java")


# ignore
def ignored(what, name):
    """Check whether something should be ignored."""
    # TODO: this really suffers from the lack of caching
    ignored_lit = get("ignore", what)
    ignored_re = get("ignore", what + "_re")
    if isinstance(ignored_lit, str):
        ignored_lit = ignored_lit.splitlines()
    if isinstance(ignored_re, str):
        ignored_re = [r for r in get("ignore", what + "_re").splitlines()]
    if name in ignored_lit:
        return True
    for patt in ignored_re:
        if re.search(patt, name):
            return True
    return False


def file_ignored(name):
    """Check whether a file should be ignored."""
    return ignored("files", name)


def dir_ignored(name):
    """Check whether a directory should be ignored."""
    return ignored("dirs", name)


# python
python_omit_on_error = make_get("python", "omit_on_error")
structural_typing = make_get("python", "structural_typing")
type_hinting = make_get("python", "type_hinting")

# java_native
java_lazy_type_checking = make_get("java_native", "lazy_type_checking")


def classpath():
    # The classpath is special, because we need to append
    # the working directory so that Autobump's utilities like
    # the Inspector and TypeCompatibilityChecker work.
    value = get("java_native", "classpath")
    return (value + ":.:") if value != "" else ""

# java_ast
java_error_on_external_types = make_get("java_ast", "error_on_external_types")

# clojure
clojure_lazy_type_checking = make_get("clojure", "lazy_type_checking")
clojure_classpath = make_get("clojure", "classpath")
