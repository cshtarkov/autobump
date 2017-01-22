"""Common classes and functions used by the core logic and the handlers."""
import re
import uuid
import logging

from autobump import diff

logger = logging.getLogger(__name__)


class VersionControlException(Exception):
    pass


class Semver(object):
    """Minimal representation of a semantic version."""

    class NotAVersionNumber(Exception):
        pass

    def __init__(self, major, minor, patch):
        assert type(major) is int
        assert type(minor) is int
        assert type(patch) is int
        self.major, self.minor, self.patch = major, minor, patch

    @classmethod
    def from_string(semver, version):
        major, minor, patch = [int(c) for c in version.split(".")]
        return semver(major, minor, patch)

    @classmethod
    def from_tuple(semver, version):
        major, minor, patch = version
        return semver(major, minor, patch)

    @classmethod
    def guess_from_string(semver, string):
        """Guess a version number from a tag name.

        Example recognized patterns:
        "1.2.3" -> "1.2.3"
        "1.2" -> "1.2.0"
        "1" -> "1.0.0"
        "v1.2.3" -> "1.2.3"
        "v1.2" -> "1.2.0"
        "v1" -> "1.0.0"
        """
        logger.warning("Guessing version from string {}".format(string))
        match = re.match(r"(v|ver|version)?-?(\d)\.?(\d)?\.?(\d)?", string)
        if match:
            major = int(match.group(2))
            minor = int(match.group(3) or 0)
            patch = int(match.group(4) or 0)
            return semver(major, minor, patch)
        else:
            raise semver.NotAVersionNumber("Cannot reliable guess version number from {}".format(string))

    def bump(self, bump):
        """Bump version using a Bump enum.

        Returns a new Semver object."""
        assert type(bump) is diff.Bump, "Bump should be an Enum"
        if bump is diff.Bump.patch:
            return Semver(self.major, self.minor, self.patch + 1)
        if bump is diff.Bump.minor:
            return Semver(self.major, self.minor + 1, 0)
        if bump is diff.Bump.major:
            return Semver(self.major + 1, 0, 0)
        # No bump
        return Semver(self.major, self.minor, self.patch)

    def __str__(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch)


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
