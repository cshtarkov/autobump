"""Tool for automatically suggesting the next version of a project according
to semantic versioning."""
import os
import argparse
from enum import Enum
from autobump import core
from autobump.handlers import git
from autobump.handlers import python


class _Repository(object):
    """Represents a repository at a location."""
    class VCS(Enum):
        none = 0
        git = 1
        svn = 2

    def __init__(self, location):
        self.location = location

    def get_vcs(self):
        try:
            if os.path.isdir(os.path.join(self.location, ".git")):
                return self.VCS.git
            if os.path.isdir(os.path.join(self.location, ".svn")):
                return self.VCS.svn
            return self.VCS.none
        except IOError:
            return self.VCS.none


class NotImplementedException(Exception):
    pass


class _Semver(object):
    """Minimal representation of a semantic version."""
    def __init__(self, major, minor, patch):
        self.major, self.minor, self.patch = major, minor, patch

    @classmethod
    def from_string(semver, version):
        major, minor, patch = [int(c) for c in version.split(".")]
        return semver(major, minor, patch)

    @classmethod
    def from_tuple(semver, version):
        major, minor, patch = version
        return semver(major, minor, patch)

    def bump(self, bump):
        """Bump version using a Bump enum.

        Returns a new _Semver object."""
        assert type(bump) is core.Bump, "Bump should be an Enum"
        if bump is core.Bump.patch:
            return _Semver(self.major, self.minor, self.patch + 1)
        if bump is core.Bump.minor:
            return _Semver(self.major, self.minor + 1, self.patch)
        if bump is core.Bump.major:
            return _Semver(self.major + 1, self.minor, self.patch)
        # No bump
        return _Semver(self.major, self.minor, self.patch)

    def __str__(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch)


def autobump():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Determine semantic version of one commit, given the version of a previous commit.")
    parser.add_argument("repo", type=str, help="Repository location")
    parser.add_argument("language", type=str, help="Repository location")
    parser.add_argument("c1", type=str, help="Earlier commit ID")
    parser.add_argument("c1version", type=str, help="Earlier commit version")
    parser.add_argument("c2", type=str, help="Later commit ID")
    args = parser.parse_args()

    # Identify VCS
    repo = _Repository(args.repo)
    repo_vcs = repo.get_vcs()
    vcs_map = {
        _Repository.VCS.git: git.commit_to_units
    }
    try:
        commit_to_units = vcs_map[repo_vcs]
    except KeyError:
        def commit_to_units(repo, commit, transformator):
            raise NotImplementedException("No VCS identified!")

    # Identify language
    repo_language = args.language
    language_map = {
        "py": python.codebase_to_units,
        "python": python.codebase_to_units
    }
    try:
        codebase_to_units = language_map[repo_language]
    except KeyError:
        def codebase_to_units(location):
            raise NotImplementedException("No language identified!")

    # Determine bump
    a_units = commit_to_units(args.repo, args.c1, codebase_to_units)
    b_units = commit_to_units(args.repo, args.c2, codebase_to_units)
    bump = core.compare_codebases(a_units, b_units)

    # Determine version
    a_version = _Semver.from_string(args.c1version)
    b_version = a_version.bump(bump)
    print(b_version)


def main(_):
    # Do not run anything if the module is just imported.
    pass
