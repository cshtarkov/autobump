"""Convert a Python codebase into a list of Units."""
import os
import sys
import imp
import inspect
import traceback
from uuid import uuid4
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
    "__main__.py"
}
_excluded_dirs = {
    "tests",
    "test",
    "scripts"
}


def _is_public(member_name):
    """Determine visibility of a member based on its name."""
    return not (member_name.startswith("_") and member_name != "__init__")


def _is_builtin(member_name):
    """Return True if this is a built-in member."""
    # TODO: This may not always be the case.
    return member_name.startswith("__")


def _get_parameters(function):
    """Return a list of Parameters to the function."""
    try:
        argspec = inspect.getfullargspec(function)
    except TypeError:
        # It could be that a method such as __dir__
        # is not implemented, which will result in a ValueError
        # when trying to get the argspec, even if the method
        # itself is there.
        # In that case just consider the parameter list empty.
        print("Failed to get argspec for {}".format(str(function)),
              file=sys.stderr)
        return []
    args = argspec.args if argspec.args is not None else []
    defaults = argspec.defaults if argspec.defaults is not None else []
    parameters = []
    i = 0
    while i < len(args) - len(defaults):
        parameters.append(common.Parameter(args[i], _dynamic))
        i += 1
    while i < len(args):
        default = defaults[i - (len(args) - len(defaults))]
        parameters.append(common.Parameter(args[i], _dynamic, default_value=default))
        i += 1
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


def python_codebase_to_units(location):
    """Returns a list of Units representing a Python codebase in 'location'."""
    sys.path.append(location)
    for root, dirs, files in os.walk(location):
        sys.path.append(root)
    units = []
    for root, dirs, files in os.walk(location):
        pyfiles = [f for f in files if f.endswith(".py")]
        for pyfile in pyfiles:
            if os.path.basename(root) in _excluded_dirs:
                continue
            if pyfile in _excluded_files:
                continue
            pymodule = pyfile[:-3]  # Strip ".py"
            # Need to generate a random name for the module,
            # otherwise all sorts of trouble can happen
            # with importing it twice, or even worse -
            # overriding functions used by this handler.
            importas = pymodule + str(uuid4())
            file, pathname, description = imp.find_module(pymodule, [root])
            try:
                units.append(_module_to_unit(pymodule, imp.load_module(importas, file, pathname, description)))
            except ImportError:
                print("Failed to import {} from {}!".format(pymodule, pathname),
                      file=sys.stderr)
                traceback.print_exc()
                print("PYTHONPATH was: {}".format(os.environ["PYTHONPATH"]),
                      file=sys.stderr)
            finally:
                if file is not None:
                    file.close()
    return units

codebase_to_units = python_codebase_to_units
