# Copyright 2016-2017 Christian Shtarkov
#
# This file is part of Autobump.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
"""
Common API Representation (CAPIR)

This is a sufficiently abstract representation that models public
APIs found in most languages.
All language handlers eventually convert the public API
they found of a library to this representation.
This is the only thing that the diffing algorithm (diff.py)
can operate on.
"""

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

    Language handlers are expected to use this type or derive from it.
    Most importantly, they should implement the 'is_compatible' method
    appropriately so that types can be compared to other types.
    """

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
    """Top-level accessible field.

    This can be used to model module constants,
    class fields, and other similar public pieces of data."""

    def __init__(self, name, type):
        self.name = name
        self.type = type


class Parameter(Entity):
    """Parameter to a function.

    Has a type and default value, where the exact value of the
    default value is irrelevant: it only matters whether there is one.
    """

    def __init__(self, name, type, default_value=None):
        self.name = name
        self.type = type
        self.default_value = default_value

    def __hash__(self):
        return hash((self.name, self.type))

    def __str__(self):
        return "<{} {}>".format(self.type, self.name)

    def __repr__(self):
        return self.__str__()


class Signature(Entity):
    """Signature of a function.

    Essentially a collection of parameters. Functions can have
    multiple signatures to model things like overloading.
    """

    def __init__(self, parameters=None):
        if parameters is None:
            parameters = []
        self.parameters = parameters

    def __hash__(self):
        return hash(tuple(self.parameters))

    def __str__(self):
        return str(self.parameters)

    def __repr__(self):
        return self.__str__()


class Function(Entity):
    """Top-level function.

    Can be used to represent any callable piece of code,
    like functions, macros, methods and so on.
    """

    def __init__(self, name, type, signatures=None):
        self.name = name
        self.type = type
        self.signatures = signatures
        if self.signatures is None:
            self.signatures = []


class Unit(Entity):
    """Generic unit of code containing fields and functions.

    Could be a Java class, a Python module, a C translation unit and so on.
    """

    def __init__(self, name, fields, functions, units):
        self.name = name
        self.fields = fields
        self.functions = functions
        self.units = units
