"""Convert a Python codebase into a list of Units."""
import os
import sys
import imp
import inspect
from autobump import common


def _determine_visibility(member_name):
    """Determine visibility of a member based on its name."""
    if member_name.startswith("_"):
        return common.Visibility.unit
    return common.Visibility.public


def _class_to_unit(name, classdef):
    """Convert a Python class definition to a Unit."""
    return common.Unit(name, [], [], [])


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
        parameters.append(common.Parameter(args[i]))
        i += 1
    while i < len(args):
        default = defaults[i - (len(args) - len(defaults))]
        parameters.append(common.Parameter(args[i], default_value=default))
        i += 1
    return parameters


def _container_to_unit(name, module, already_converted):
    """Convert a Python module or class to a Unit."""
    fields = []
    functions = []
    units = []
    for member_name, member in inspect.getmembers(module):
        if id(member) in already_converted:
            continue
        already_converted.add(id(member))
        visibility = _determine_visibility(member_name)
        if inspect.isclass(member):
            units.append(_container_to_unit(member_name, member, already_converted))
        elif callable(member):
            functions.append(common.Function(member_name, visibility, _get_parameters(member)))
        else:
            fields.append(common.Field(member_name, visibility))
    return common.Unit(name, _determine_visibility(name), fields, functions, units)


def _module_to_unit(name, module):
    """Convert a Python module to a Unit."""
    return _container_to_unit(name, module, set())


def python_codebase_to_units(location):
    """Returns a list of Units representing a Python codebase in 'location'."""
    units = []
    for root, dirs, files in os.walk(location):
        pyfiles = [f for f in files if f.endswith(".py")]
        for pyfile in pyfiles:
            pymodule = pyfile[:-3]  # Strip ".py"
            file, pathname, description = imp.find_module(pymodule, [root])
            try:
                units.append(_module_to_unit(pymodule, imp.load_module(pymodule, file, pathname, description)))
                units[-1].visibility = common.Visibility.public  # HACK!
            except ImportError as e:
                print("Failed to import {} from {}!".format(pymodule, pathname),
                      file=sys.stderr)
            finally:
                if file is not None:
                    file.close()
    return units

codebase_to_units = python_codebase_to_units
