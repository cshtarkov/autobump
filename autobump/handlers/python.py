"""Convert a Python codebase into a list of Units."""
import os
import sys
import imp
import traceback
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
        elif isinstance(default, ast.Num):
            default = default.n
        elif isinstance(default, ast.Str):
            default = default.s
        parameters.append(common.Parameter(arg.arg, _dynamic, default))
    return parameters


def _container_to_unit(name, container, already_converted):
    """Convert a Python module or class to a Unit."""
    fields = []
    functions = []
    units = []
    for member_name, member in inspect.getmembers(container):
        if _is_builtin(member_name) and member_name != "__init__":
            continue
        if not _is_public(member_name):
            # Completely ignore any private things -
            # they are irrelevant to the API.
            continue
        # Handle possible circular references.
        if inspect.isclass(member):
            if hash((member_name, id(member))) in already_converted:
                continue
            already_converted.add(hash((member_name, id(member))))
        if inspect.isclass(member):
            units.append(_container_to_unit(member_name, member, already_converted))
        elif callable(member):
            functions.append(common.Function(member_name, _dynamic, common.Signature(_get_parameters(member))))
        else:
            fields.append(common.Field(member_name, _dynamic))
    return common.Unit(name, fields, functions, units)


def _module_to_unit(name, module):
    """Convert a Python module to a Unit."""
    return _container_to_unit(name, module, set())


def _python_codebase_to_units(location, queue):
    """Returns a list of Units representing a Python codebase in 'location'.

    This function should not be called directly. Instead it should be
    run as a separate process, so that imports only apply for that
    Python process and pollute the namespace where autobump is running."""
    sys.path.append(location)
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if d not in _excluded_dirs]
        sys.path.append(root)
    units = []
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if d not in _excluded_dirs]
        pyfiles = [f for f in files if f.endswith(".py")]
        for pyfile in pyfiles:
            if pyfile in _excluded_files:
                continue
            pymodule = pyfile[:-3]  # Strip ".py"
            file, pathname, description = imp.find_module(pymodule, [root])
            try:
                units.append(_module_to_unit(pymodule, imp.load_module(pymodule, file, pathname, description)))
            except ImportError:
                print("Failed to import {} from {}!".format(pymodule, pathname),
                      file=sys.stderr)
                traceback.print_exc()
            finally:
                if file is not None:
                    file.close()

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
