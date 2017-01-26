"""Common classes and functions used by the core logic and the handlers."""
import re
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

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.major == other.major and \
               self.minor == other.minor and \
               self.patch == other.patch

    def __ne__(self, other):
        return not self.__eq__(other)

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
