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
Common classes and functions used throughout Autobump.
"""

import re
import logging
import subprocess

from autobump import diff

logger = logging.getLogger(__name__)


class VersionControlException(Exception):
    pass


class Semver(object):
    """Minimal representation of a semantic version."""

    class NotAVersionNumber(Exception):
        pass

    def __init__(self, major, minor, patch, label=""):
        assert type(major) is int
        assert type(minor) is int
        assert type(patch) is int
        assert type(label) is str
        self.major, self.minor, self.patch, self.label = major, minor, patch, label

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.major == other.major and \
               self.minor == other.minor and \
               self.patch == other.patch and \
               self.label == other.label

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_string(semver, version):
        if "-" in version:
            numeric = version[:version.find("-")]
            try:
                label = version[version.find("-") + 1:]
            except IndexError:
                raise semver.NotAVersionNumber()
        else:
            numeric = version
            label = ""
        major, minor, patch = [int(c) for c in numeric.split(".")]
        return semver(major, minor, patch, label)

    @classmethod
    def from_tuple(semver, version):
        return semver(*version)

    @classmethod
    def guess_from_string(semver, string):
        """Guess a version number from a tag name. """
        match = re.match(r"[A-Za-z_-]*-?(v|ver|version)?-?(\d+)\.?(\d+)?\.?(\d+)?-?(.*)$", string)
        if match:
            major = int(match.group(2))
            minor = int(match.group(3) or 0)
            patch = int(match.group(4) or 0)
            label = str(match.group(5) or "")
            guess = semver(major, minor, patch, label)
            logger.warning("Guessing version from string '{}': {}"
                           .format(string, guess))
            return guess
        else:
            raise semver.NotAVersionNumber("Cannot reliable guess version number from {}".format(string))

    def bump(self, bump):
        """Bump version using a Bump enum."""
        assert type(bump) is diff.Bump, "Bump should be an Enum"
        if bump is diff.Bump.patch:
            return Semver(self.major, self.minor, self.patch + 1, "")
        if bump is diff.Bump.minor:
            return Semver(self.major, self.minor + 1, 0, "")
        if bump is diff.Bump.major:
            return Semver(self.major + 1, 0, 0, "")
        # No bump
        return Semver(self.major, self.minor, self.patch, self.label)

    def drop_label(self):
        """Return a new semver with the label gone."""
        return Semver(self.major, self.minor, self.patch, "")

    def __str__(self):
        return "{}.{}.{}{}".format(self.major,
                                   self.minor,
                                   self.patch,
                                   "" if self.label == "" else "-" + self.label)


def popen(args, cwd="."):
    """Thinly wrap subprocess.Popen.

    Always pipes stdout and stderr so that nothing is seen by
    the end user unless explicitly printed.
    """
    child = subprocess.Popen(args,
                             cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout_data, stderr_data = child.communicate()
    return (child.returncode,
            stdout_data.decode("ascii").strip(),
            stderr_data.decode("ascii").strip())
