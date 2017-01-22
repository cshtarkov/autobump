"""Common API representation."""
import uuid


class Entity(object):
    """Generic entity."""
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        raise TypeError("Comparing entity to something else.")

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name


class Type(Entity):
    """Generic representation of a type.

    Handlers are expected to inherit this class
    once for every time in the language's type system.
    They should also implement the is_compatible() method
    so that it does something sensible in that context."""
    def __init__(self):
        self.name = str(uuid.uuid4())

    def is_compatible(self, other):
        """Checks whether 'self' can substitute 'other'."""
        return isinstance(self, type(other))

    def __eq__(self, other):
        return self.is_compatible(other) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Field(Entity):
    """Class field or constant."""
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Parameter(Entity):
    """Parameter to a function."""
    def __init__(self, name, type, default_value=None):
        self.name = name
        self.type = type
        self.default_value = default_value

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.name, self.type))

    def __str__(self):
        return "<{} {}>".format(self.type, self.name)

    def __repr__(self):
        return self.__str__()


class Signature(Entity):
    """Signature of a function."""
    def __init__(self, parameters=None):
        if parameters is None:
            parameters = []
        self.parameters = parameters

    def add_parameter(self, param):
        self.parameters.append(param)

    def parameter(self, param):
        self.add_parameter(param)
        return self

    def __lt__(self, other):
        return self.parameters < other.parameters

    def __hash__(self):
        return hash(tuple(self.parameters))

    def __str__(self):
        return str(self.parameters)

    def __repr__(self):
        return self.__str__()


class Function(Entity):
    """Top-level function or class method."""
    def __init__(self, name, type, signatures=None):
        self.name = name
        self.type = type
        self.signatures = signatures
        if self.signatures is None:
            self.signatures = []


class Unit(Entity):
    """Generic unit of code containing fields and functions.

    Could be a Java class, a Python module, a C translation unit and so on. """
    def __init__(self, name, fields, functions, units):
        self.name = name
        self.fields = fields
        self.functions = functions
        self.units = units
