"""Common classes and functions used by the core logic and the handlers."""
from enum import Enum


class VersionControlException(Exception):
    pass


class Visibility(Enum):
    unit = 0
    package = 1
    public = 2


class CodeProperty(object):
    """Generic code property."""
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        raise TypeError("Comparing code property to something else.")

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name


class Field(CodeProperty):
    """Class field or constant."""
    def __init__(self, name, visibility, default_value=None):
        self.name = name
        self.visibility = visibility
        self.default_value = default_value


class Parameter(CodeProperty):
    """Parameter to a function."""
    def __init__(self, name, default_value=None):
        self.name = name
        self.default_value = default_value


class Function(CodeProperty):
    """Top-level function or class method."""
    def __init__(self, name, visibility, parameters=[]):
        self.name = name
        self.visibility = visibility
        self.parameters = parameters


class Unit(CodeProperty):
    """Generic unit of code containing fields and functions.

    Could be a Java class, a Python module, a C translation unit and so on. """
    def __init__(self, name, visibility, fields, functions, units):
        self.name = name
        self.visibility = visibility
        self.fields = fields
        self.functions = functions
        self.units = units
