"""Convert a Python codebase into a list of Units."""
import os
import ast
import multiprocessing
from autobump import common


# Type System
class _PythonType(common.Type):
    pass


class _Dynamic(_PythonType):
    pass


_dynamic = _Dynamic()

# Set of files to exclude when importing
_excluded_files = {
    "setup.py",
    "__main__.py",
    "run-tests.py"
}
_excluded_dirs = {
    "testsuite",
    "tests",
    "test",
    "scripts",
    "examples",
    "docs"
}


def _is_public(member_name):
    """Determine visibility of a member based on its name."""
    return not (member_name.startswith("_") and member_name != "__init__")


def _is_builtin(member_name):
    """Return True if this is a built-in member."""
    # TODO: This may not always be the case.
    return member_name.startswith("__")


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
        parameters.append(common.Parameter(arg.arg, _dynamic, default))
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


def _python_codebase_to_units(location, queue):
    """Returns a list of Units representing a Python codebase in 'location'.

    This function should not be called directly. Instead it should be
    run as a separate process, so that imports only apply for that
    Python process and pollute the namespace where autobump is running."""
    units = []
    for root, dirs, files in os.walk(location):
        print("dirs before excl: ", str(root), str(dirs))
        dirs[:] = [d for d in dirs if d not in _excluded_dirs]
        print("dirs after excl: ", str(root), str(dirs))
        pyfiles = [f for f in files if f.endswith(".py")]
        for pyfile in pyfiles:
            if pyfile in _excluded_files:
                continue
            pymodule = pyfile[:-3]  # Strip ".py"
            with open(os.path.join(root, pyfile), "r") as f:
                units.append(_module_to_unit(pymodule, ast.parse(''.join(list(f)))))

    queue.put(units)


def codebase_to_units(location):
    """Returns a list of Units representing a Python codebase in 'location'."""
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_python_codebase_to_units,
                                      args=(location, queue))
    process.start()
    units = queue.get()
    process.join()
    return units
