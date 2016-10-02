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


def _module_to_unit(name, module):
    """Convert a Python module to a Unit."""
    fields = []
    functions = []
    units = []
    for member_name in dir(module):
        visibility = _determine_visibility(member_name)
        member = getattr(module, member_name)
        if inspect.isclass(member):
            units.append(_class_to_unit(member_name, member))
        elif callable(member):
            functions.append(common.Function(member_name, visibility, []))
        else:
            fields.append(common.Field(member_name, visibility))
    return common.Unit(name, fields, functions, units)


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
