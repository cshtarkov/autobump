"""Tool for automatically suggesting the next version of a project according
to semantic versioning."""
import re
import os
import sys
import logging
import argparse
import subprocess
from subprocess import PIPE
from enum import Enum
from autobump import core
from autobump import common
from autobump.handlers import git
from autobump.handlers import python

logger = logging.getLogger(__name__)


class NotImplementedException(Exception):
    pass


class _Repository(object):
    """Represents a repository at a location."""
    class VCS(Enum):
        none = 0
        git = 1
        svn = 2

    def __init__(self, location):
        self.location = location
        try:
            if os.path.isdir(os.path.join(self.location, ".git")):
                self.vcs = self.VCS.git
            elif os.path.isdir(os.path.join(self.location, ".svn")):
                self.vcs = self.VCS.svn
            else:
                self.vcs = self.VCS.none
        except IOError:
            self.vcs = self.VCS.none

    def last_tag(self):
        """Return name of most recently made tag."""
        if self.vcs is self.VCS.git:
            child = subprocess.Popen(["git", "describe", "--tags", "--abbrev=0"], cwd=self.location, stdout=PIPE)
            stdout_data, stderr_data = child.communicate()
            if child.returncode != 0:
                raise common.VersionControlException("Failed to get last tag of Git repository {}".format(self.location))
            return stdout_data.decode("ascii").strip()
        else:
            raise NotImplementedException("Cannot get last tag for repository type {}".format(self.vcs))

    def last_commit(self):
        """Return identifier of most recently made commit."""
        if self.vcs is self.VCS.git:
            child = subprocess.Popen(["git", "log", "-1", "--oneline"], cwd=self.location, stdout=PIPE)
            stdout_data, stderr_data = child.communicate()
            if child.returncode != 0:
                raise common.VersionControlException("Failed to get last commit of Git repository {}".format(self.location))
            return stdout_data.decode("ascii").strip().split()[0]
        else:
            raise NotImplementedException("Cannot get last commit for repository type {}".format(self.vcs))


class _Semver(object):
    """Minimal representation of a semantic version."""

    class NotAVersionNumber(Exception):
        pass

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
        logger.warn("Guessing version from string {}".format(string))
        match = re.match(r"(v|ver|version)?-?(\d)\.?(\d)?\.?(\d)?", string)
        if match:
            major = int(match.group(2))
            minor = int(match.group(3)) if match.group(3) is not None else 0
            patch = int(match.group(4)) if match.group(4) is not None else 0
            return semver(major, minor, patch)
        else:
            raise semver.NotAVersionNumber("Cannot reliable guess version number from {}".format(string))

    def bump(self, bump):
        """Bump version using a Bump enum.

        Returns a new _Semver object."""
        assert type(bump) is core.Bump, "Bump should be an Enum"
        if bump is core.Bump.patch:
            return _Semver(self.major, self.minor, self.patch + 1)
        if bump is core.Bump.minor:
            return _Semver(self.major, self.minor + 1, 0)
        if bump is core.Bump.major:
            return _Semver(self.major + 1, 0, 0)
        # No bump
        return _Semver(self.major, self.minor, self.patch)

    def __str__(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch)


def autobump():
    """Main entry point."""
    description = """
Determine change of semantic version of code in a repository.

Example usage:

{0} python

  Shows what version the last commit should be, by guessing the
  previous version from the last tag.
  The tool will only look at Python files found in the repository.

{0} python --from milestone-foo --from-version 1.1.0

  Shows what version the last commit should be, if the previous
  release was `milestone-foo` at version 1.1.0.
  `milestone-foo` can be a tag name or commit identifier.
  The tool will only look at Python files found in the repository.

{0} java --from milestone-foo --from-version 1.1.0 --to milestone-bar

  Shows what version `milestone-bar` should be, if the previous
  release was `milestone-foo` at version 1.1.0.
  The tool will only look at Java files found in the repository.
""".format(os.path.basename(sys.argv[0]))
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=description)
    parser.add_argument("-c", "--changelog", help="generate changelog", action="store_true")
    parser.add_argument("-d", "--debug", help="print debugging information to stderr (implies `--info`)", action="store_true")
    parser.add_argument("-i", "--info", help="print progress information to stderr", action="store_true")
    parser.add_argument("-r", "--repo", help="repository location, will use working directory if not specified", type=str)
    parser.add_argument("-f", "--from", type=str, help="identifier of earlier revision, will use last tag if not specified")
    parser.add_argument("-fv", "--from-version", type=str, help="version of earlier revision, will try to guess if not specified!")
    parser.add_argument("-t", "--to", type=str, help="identifier of later revision, will use last commit if not specified")
    parser.add_argument("language", type=str, help="repository language {python}")

    args = parser.parse_args()
    args.f = getattr(args, "from")  # Syntax doesn't allow `args.from`.

    # Set appropriate log level
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format=log_format)
    elif args.info:
        logging.basicConfig(level=logging.INFO,
                            format=log_format)

    # Identify VCS
    repo = _Repository(args.repo if args.repo is not None else os.getcwd())
    vcs_map = {
        _Repository.VCS.git: git.commit_to_units
    }
    try:
        commit_to_units = vcs_map[repo.vcs]
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

    # Identify revisions
    a_revision = args.f if args.f is not None else repo.last_tag()
    logging.debug("Earlier revision is {}".format(a_revision))
    b_revision = args.to if args.to is not None else repo.last_commit()
    logging.debug("Later revision is {}".format(b_revision))

    # Determine bump
    a_units = commit_to_units(repo.location, a_revision, codebase_to_units)
    b_units = commit_to_units(repo.location, b_revision, codebase_to_units)
    bump = core.compare_codebases(a_units, b_units)
    logging.debug("Bump found to be {}".format(bump))

    # Determine version
    a_version = _Semver.from_string(args.from_version) if args.from_version is not None else _Semver.guess_from_string(a_revision)
    logging.debug("Earlier version is {}".format(a_version))
    b_version = a_version.bump(bump)
    logging.debug("Later version is {}".format(b_version))
    print(b_version)


def main(_):
    # Do not run anything if the module is just imported.
    pass
