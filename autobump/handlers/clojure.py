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
Convert a Clojure codebase into a list of Units.

The Clojure handler invokes a script which is inspected
to run in the same environment as the project. This is best achieved
by configuring the Clojure executable to be 'lein exec' or something similar.
"""

import os
import string
import logging

from autobump import config
from autobump.capir import Type, Field, Parameter, Signature, Function, Unit
from autobump.common import popen

logger = logging.getLogger(__name__)
libexec = os.path.join(os.path.dirname(__file__), "..", "libexec")
inspector_clj = os.path.join(libexec, "evalinspector.clj")
_source_file_ext = ".clj"


class _ClojureType(Type):
    def __init__(self, name, supers):
        self.name = name
        self.supers = supers

    def is_compatible(self, other):
        if self.name == "nil":
            return True
        if self.name == other.name:
            return True
        return self.name in other.supers

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<ClojureType {}>".format(self.name)


_clojure_nil = _ClojureType("nil", set())


class _ClojureUtilityException(Exception):
    pass


class _SexpReadException(Exception):
    pass


def _run_inspector(file, repo):
    """Runs the utility program inspector.clj for a file, with
    the working directory set to 'repo'."""
    arglist = [config.clojure(), inspector_clj, file]
    logger.debug("Running inspector as follows: " + ' '.join(arglist))
    return_code, stdout, stderr = popen(arglist, cwd=repo)
    if return_code != 0:
        raise _ClojureUtilityException(stderr)
    return stdout


def _sexp_read(s):
    """Reads in a sexp describing a Clojure codebase
    and convert it into the common representation."""
    def tokenize(s):
        delimiters = string.whitespace + "()"
        token = ""
        for char in s:
            if char in delimiters:
                if token != "":
                    yield token
                if char in "()":
                    yield char
                token = ""
            else:
                token = token + char
        if token != "":
            yield token

    def sexp_to_list(gen):
        lst = []
        for token in gen:
            if token == "(":
                lst.append(sexp_to_list(gen))
            elif token == ")":
                return lst
            else:
                lst.append(token)
        return lst

    def verify_tag(tag, lst):
        if lst[0] != tag:
            raise _SexpReadException("Expected {}, got {}".format(tag, lst[0]))

    def _read_type(lst):
        verify_tag("type", lst)
        tag, name, supers = lst
        return _ClojureType(name, set(supers))

    def read_signature(lst):
        verify_tag("signature", lst)
        tag, positional, optional = lst
        parameters = [Parameter(name, _read_type(type))
                      for name, type
                      in positional]
        # TODO: Properly handle default values (:or idiom).
        parameters += [Parameter(name, _read_type(type), default_value=True)
                       for name, type
                       in optional]
        return Signature(parameters)

    def read_function(lst):
        verify_tag("function", lst)
        tag, name, signatures = lst
        return Function(name, _clojure_nil, [read_signature(s) for s in signatures])

    def read_field(lst):
        verify_tag("field", lst)
        tag, name, type = lst
        return Field(name, _read_type(type))

    def read_unit(lst):
        verify_tag("unit", lst)
        tag, name, fields, functions, units = lst
        fields_dict = {}
        functions_dict = {}
        units_dict = {}
        for f in fields:
            field = read_field(f)
            fields_dict[field.name] = field
        for f in functions:
            function = read_function(f)
            functions_dict[function.name] = function
        for u in units:
            unit = read_unit(u)
            units_dict[unit.name] = unit
        return Unit(name,
                    fields_dict,
                    functions_dict,
                    units_dict)

    # TODO: Why [0]?
    units = dict()
    lst = sexp_to_list(tokenize(s))
    if len(lst) > 1:
        raise _SexpReadException("Sexp contains more than one top-level form")
    files = lst[0]
    for f in files:
        unit = read_unit(f)
        units[unit.name] = unit
    return units


def clojure_codebase_to_units(location):
    """Returns a list of Units representing a Clojure codebase in 'location'."""
    # Resolve classpath
    if "CLASSPATH" in os.environ:
        logger.debug("CLASSPATH variable set (it's not guaranteed Clojure will it)")
    if config.clojure_classpath() != "":
        logger.debug("clojure/classpath set, setting that as CLASSPATH (it's not guaranteed Clojure will use it")
        os.environ["CLASSPATH"] = config.clojure_classpath()
    if "CLASSPATH" not in os.environ:
        logger.warning("No CLASSPATH set")
    else:
        logger.info("CLASSPATH is:\n\t{}".format(os.environ["CLASSPATH"]))

    # Inspect .clj files
    cljfiles = []
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if not config.dir_ignored(d)]
        cljfiles += [os.path.join(root, f)
                     for f in files
                     if f.endswith(_source_file_ext) and not config.file_ignored(f)]

    units = dict()
    for cljfile in cljfiles:
        units.update(_sexp_read(_run_inspector(cljfile, location)))
    return units


build_required = False
codebase_to_units = clojure_codebase_to_units
