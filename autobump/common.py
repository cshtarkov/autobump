"""Common classes and functions used by the core logic and the handlers."""


class VersionControlException(Exception):
    pass


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


class Type(CodeProperty):
    """Generic representation of a type.

    Handlers are expected to inherit this class
    once for every time in the language's type system.
    They should also implement the is_compatible() method
    so that it does something sensible in that context."""
    def is_compatible(self, other):
        return isinstance(other, type(self))


class Field(CodeProperty):
    """Class field or constant."""
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Parameter(CodeProperty):
    """Parameter to a function."""
    def __init__(self, name, type, default_value=None):
        self.name = name
        self.type = type
        self.default_value = default_value


class Signature(CodeProperty):
    """Signature of a function."""
    def __init__(self, parameters=[]):
        self.parameters = parameters

    def add_parameter(self, param):
        self.parameters.append(param)

    def parameter(self, param):
        self.add_parameter(param)
        return self


class Function(CodeProperty):
    """Top-level function or class method."""
    def __init__(self, name, type, signature=None):
        self.name = name
        self.type = type
        self.signature = signature
        if self.signature is None:
            self.signature = Signature()


class Unit(CodeProperty):
    """Generic unit of code containing fields and functions.

    Could be a Java class, a Python module, a C translation unit and so on. """
    def __init__(self, name, fields, functions, units):
        self.name = name
        self.fields = fields
        self.functions = functions
        self.units = units
