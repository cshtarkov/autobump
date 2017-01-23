"""Convert a Clojure codebase into a list of Units."""
import os
import string
import logging
import subprocess
from subprocess import PIPE

from autobump import config
from autobump.capir import Type, Field, Parameter, Signature, Function, Unit

logger = logging.getLogger(__name__)
libexec = os.path.join(os.path.dirname(__file__), "..", "libexec")
inspector_clj = os.path.join(libexec, "evalinspector.clj")
_source_file_ext = ".clj"


class _ClojureType(Type):
    def __init__(self, name):
        self.name = name

    def is_compatible(self, other):
        if self.name == "nil":
            return True
        if config.clojure_lazy_type_checking():
            return self.name == other.name
        else:
            raise NotImplemented("Non-lazy type checking")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<ClojureType {}>".format(self.name)


class _ClojureUtilityException(Exception):
    pass


class _SexpReadException(Exception):
    pass


def _run_inspector(files, repo):
    """Runs the utility program inspector.clj with a list of files, with
    the working directory set to 'repo'."""
    arglist = [config.clojure(), inspector_clj] + files
    logger.debug("Running inspector as follows: " + ' '.join(arglist))
    child = subprocess.Popen(arglist, cwd=repo, stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = child.communicate()
    if child.returncode != 0:
        raise _ClojureUtilityException(stderr_data.decode("ascii").strip())
    return stdout_data.decode("ascii").strip()


def _lookup_type(name):
    # TODO: Properly lookup types.
    return _ClojureType(name)


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

    def read_signature(lst):
        verify_tag("signature", lst)
        tag, positional, optional = lst
        parameters = [Parameter(name, _lookup_type(type_name))
                      for name, type_name
                      in positional]
        # TODO: Properly handle default values (:or idiom).
        parameters += [Parameter(name, _lookup_type(type_name), default_value=True)
                       for name, type_name
                       in optional]
        return Signature(parameters)

    def read_function(lst):
        verify_tag("function", lst)
        tag, name, signatures = lst
        return Function(name, _lookup_type("nil"), [read_signature(s) for s in signatures])

    def read_field(lst):
        verify_tag("field", lst)
        tag, name, type_name = lst
        return Field(name, _lookup_type(type_name))

    def read_file(lst):
        verify_tag("file", lst)
        tag, ns, fields, functions = lst
        fields_dict = {}
        functions_dict = {}
        for f in fields:
            field = read_field(f)
            fields_dict[field.name] = field
        for f in functions:
            function = read_function(f)
            functions_dict[function.name] = function
        return Unit(ns,
                    fields_dict,
                    functions_dict,
                    dict())

    # TODO: Why [0]?
    units = dict()
    lst = sexp_to_list(tokenize(s))
    if len(lst) > 1:
        raise _SexpReadException("Sexp contains more than one top-level form")
    files = lst[0]
    for f in files:
        unit = read_file(f)
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

    return _sexp_read(_run_inspector(cljfiles, location))

build_required = False
codebase_to_units = clojure_codebase_to_units
