"""Convert a Python codebase into a list of Units."""
import os
import re
import ast
from autobump import common


# Type System
class _PythonType(common.Type):
    pass


class _Dynamic(_PythonType):
    pass


class _StructuralType(_PythonType):
    def __init__(self, method_set):
        self.name = str(method_set)
        self.method_set = method_set

    def is_compatible(self, other):
        return self.method_set.issubset(other.method_set)


_dynamic = _Dynamic()

# Set of files to exclude when importing
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
    method_set = set()
    for call in [n for n in ast.walk(function)
                 if
                 isinstance(n, ast.Call) and
                 isinstance(n.func, ast.Attribute) and
                 isinstance(n.func.value, ast.Name)]:
        # TODO: This also counts variables which have the same
        # name as the parameter, e.g. in inner functions.
        name = call.func.value.id
        method = call.func.attr
        if name == parameter:
            # TODO: Also consider method signature.
            method_set.add(method)

    return _StructuralType(method_set)


def _get_parameters(function):
    """Return a list of Parameters to a function AST node."""
    parameters = []
    args = function.args.args
    defaults = [None] * (len(args) - len(function.args.defaults)) + function.args.defaults
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
    return parameters


def _container_to_unit(name, container):
    """Convert a Python AST module or class to a Unit."""
    fields = []
    functions = []
    units = []
    for node in container.body:
        if hasattr(node, "name") and not _is_public(node.name):
            # Completely ignore any private things -
            # they are irrelevant to the API.
            continue
        if isinstance(node, ast.ClassDef):
            units.append(_container_to_unit(node.name, node))
        elif isinstance(node, ast.FunctionDef):
            functions.append(common.Function(node.name, _dynamic, common.Signature(_get_parameters(node))))
        elif isinstance(node, ast.Assign):
            # TODO: Handle other forms of assignment.
            for target in [t for t in node.targets if isinstance(t, ast.Name) and _is_public(t.id)]:
                fields.append(common.Field(target.id, _dynamic))
    return common.Unit(name, fields, functions, units)


def _module_to_unit(name, module):
    """Convert a Python AST module to a Unit."""
    return _container_to_unit(name, module)


def python_codebase_to_units(location):
    """Returns a list of Units representing a Python codebase in 'location'."""
    units = []
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if not any(r.match(d) for r in _excluded_dirs)]
        pyfiles = [f for f in files if f.endswith(".py") and not any(r.match(f) for r in _excluded_files)]
        for pyfile in pyfiles:
            pymodule = pyfile[:-3]  # Strip ".py"
            with open(os.path.join(root, pyfile), "r") as f:
                units.append(_module_to_unit(pymodule, ast.parse(''.join(list(f)))))
    return units

codebase_to_units = python_codebase_to_units
