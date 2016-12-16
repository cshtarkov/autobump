"""Convert a Python codebase into a list of Units."""
import os
import re
import ast

from autobump import common
from autobump import config

_source_file_ext = ".py"
_excluded_files = [
    re.compile(r"^test_"),
    re.compile(r"^tests.py$"),
    re.compile(r".*_test.py$"),
    re.compile(r"^setup.py$"),
    re.compile(r"^__main__.py$"),
    re.compile(r"^run-tests.py$")
]
_excluded_dirs = [
    re.compile(r"^test"),
    re.compile(r"^script"),
    re.compile(r"^example"),
    re.compile(r"^doc"),
    re.compile(r"^.git$"),
    re.compile(r"^.svn$")
]


class _PythonType(common.Type):
    pass


class _Dynamic(_PythonType):
    pass


class _StructuralType(_PythonType):
    def __init__(self, attr_set):
        self.name = str(attr_set)
        self.attr_set = attr_set

    def is_compatible(self, other):
        return self.attr_set.issubset(other.attr_set)

    def __str__(self):
        return str(self.attr_set)


_dynamic = _Dynamic()


def _is_public(member_name):
    """Determine visibility of a member based on its name."""
    return not (member_name.startswith("_") and member_name != "__init__")


def _is_builtin(member_name):
    """Return True if this is a built-in member."""
    # TODO: This may not always be the case.
    return member_name.startswith("__")


def _get_type_of_parameter(function, parameter):
    """Return the type of a parameter used in a function AST node.

    In this case, 'type' means structural instead of nominal type.
    Because Python is dynamically typed, it would be very hard to guess
    what type a parameter is without looking at usage. Instead of doing that,
    this walks the AST node describing the function and considers the type to be
    the set of all methods called on the parameter."""
    assert isinstance(function, ast.FunctionDef), "Tried to get usage of parameter in a non-function."

    if not config.use_structural_typing():
        return _dynamic

    # TODO: Don't completely ommit 'self' in class methods,
    # it can be used to identify addition or removal of fields.
    if parameter == "self":
        return _StructuralType(set())

    # Generators to filter out AST
    def gen_no_inner_definitions(node):
        """Recursively yield all descendant nodes
        without walking any function or class definitions."""
        yield node
        for n in ast.iter_child_nodes(node):
            if isinstance(n, ast.FunctionDef) or \
               isinstance(n, ast.ClassDef):
                continue
            yield from gen_no_inner_definitions(n)

    def gen_only_attributes(node):
        """Yield only descendant nodes that represent attribute access,
        without traversing any function or class definitions."""
        for n in gen_no_inner_definitions(node):
            if isinstance(n, ast.Attribute) and \
               isinstance(n.value, ast.Name):
                yield n

    # Find the set of attributes for that parameter
    attr_set = set()
    for attr in gen_only_attributes(function):
        name = attr.value.id
        method = attr.attr
        if name == parameter:
            # TODO: Also consider method signature.
            attr_set.add(method)

    # Convert set of attribytes to structural type
    return _StructuralType(attr_set)


def _get_signature(function):
    """Return the signature of a function AST node."""
    parameters = []
    args = function.args.args

    # Map all None parameters to a "TrueNone" object
    # because None indicates the absense of a default value.
    class TrueNone(object):
        pass
    defaults = [TrueNone
                if isinstance(a, ast.NameConstant) and a.value is None
                else a
                for a in function.args.defaults]
    # Prepend no default values.
    defaults = [None] * (len(args) - len(defaults)) + defaults

    args_with_defaults = list(zip(args, defaults))
    for arg_with_default in args_with_defaults:
        arg, default = arg_with_default
        if isinstance(default, ast.Name):
            # TODO: This does not differentiate between
            # "abc" and abc.
            default = default.id
        elif isinstance(default, ast.NameConstant):
            default = default.value
        elif isinstance(default, ast.Num):
            default = default.n
        elif isinstance(default, ast.Str):
            default = default.s
        type = _get_type_of_parameter(function, arg.arg)
        parameters.append(common.Parameter(arg.arg, type, default))
    # Note: we need to return a list with the signature inside
    # because the common representation allows for overloading,
    # which Python doesn't.
    return [common.Signature(parameters)]


def _container_to_unit(name, container):
    """Convert a Python AST module or class to a Unit."""
    fields = dict()
    functions = dict()
    units = dict()
    for node in container.body:
        if hasattr(node, "name") and not _is_public(node.name):
            # Completely ignore any private things -
            # they are irrelevant to the API.
            continue
        if isinstance(node, ast.ClassDef):
            units[node.name] = _container_to_unit(node.name, node)
        elif isinstance(node, ast.FunctionDef):
            functions[node.name] = common.Function(node.name, _dynamic, _get_signature(node))
        elif isinstance(node, ast.Assign):
            # TODO: Handle other forms of assignment.
            for target in [t for t in node.targets if isinstance(t, ast.Name) and _is_public(t.id)]:
                fields[target.id] = common.Field(target.id, _dynamic)
    return common.Unit(name, fields, functions, units)


def _module_to_unit(name, module):
    """Convert a Python AST module to a Unit."""
    return _container_to_unit(name, module)


def python_codebase_to_units(location):
    """Returns a list of Units representing a Python codebase in 'location'."""
    units = dict()
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if not any(r.search(d) for r in _excluded_dirs)]
        pyfiles = [f for f in files if f.endswith(_source_file_ext) and not any(r.search(f) for r in _excluded_files)]
        for pyfile in pyfiles:
            pymodule = pyfile[:-(len(_source_file_ext))]  # Strip extension
            with open(os.path.join(root, pyfile), "r") as f:
                units[pymodule] = _module_to_unit(pymodule, ast.parse(''.join(list(f))))
    return units

build_required = False
codebase_to_units = python_codebase_to_units
