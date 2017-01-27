"""Tool for automatically suggesting the next version of a project according
to semantic versioning."""
import os
import sys
import enum
import logging
import argparse

from autobump import diff
from autobump.common import Semver, VersionControlException
from autobump.handlers import hg
from autobump.handlers import git
from autobump.handlers import python
from autobump.handlers import java_ast
from autobump.handlers import java_native
from autobump.handlers import clojure

logger = logging.getLogger(__name__)


class _Repository(object):
    """Represents a repository at a location."""
    class VCS(enum.Enum):
        git = 0
        hg = 1

    def __init__(self, location):
        self.location = location
        try:
            # TODO: This will not work with bare repositories.
            if os.path.isdir(os.path.join(self.location, ".git")):
                self.vcs = self.VCS.git
            elif os.path.isdir(os.path.join(self.location, ".hg")):
                self.vcs = self.VCS.hg
            else:
                self.vcs = None
        except IOError:
            logger.error("IO error occured while trying to get VCS")
        self.handler = self._match_handler(self.vcs)

    def _match_handler(self, vcs):
        """Return the handler responsible for the VCS of this type."""
        handlers = {
            self.VCS.git: git,
            self.VCS.hg: hg
        }
        return handlers.get(vcs, None)

    def get_commit(self, commit):
        assert self.handler is not None
        return self.handler.get_commit(self.location, commit)

    def all_tags(self):
        """Return a list of all tags in chronological order."""
        if self.handler is not None:
            return self.handler.all_tags(self.location)
        else:
            raise NotImplemented("Cannot get all tags for repository type {}".format(self.vcs))

    def last_tag(self):
        """Return name of most recently made tag."""
        if self.handler is not None:
            return self.handler.last_tag(self.location)
        else:
            raise NotImplemented("Cannot get last tag for repository type {}".format(self.vcs))

    def last_commit(self):
        """Return identifier of most recently made commit."""
        if self.handler is not None:
            return self.handler.last_commit(self.location)
        else:
            raise NotImplemented("Cannot get last tag for repository type {}".format(self.vcs))


def _patch_types_with_location(units, location):
    """Walk all types found in a dictionary of units and set their location property."""
    for unit in units.values():
        for field in unit.fields.values():
            field.type.location = location
        for function in unit.functions.values():
            function.type.location = location
            for signature in function.signatures:
                for parameter in signature.parameters:
                    parameter.type.location = location
        _patch_types_with_location(unit.units, location)


def autobump(**kwargs):
    """Main entry point."""
    description = """
Determine change of semantic version of code in a repository.

Example usage:

$ {0} python

    Shows what version the last commit should be, by guessing the
    previous version from the last tag.
    The tool will only look at Python files found in the repository.

$ {0} python --changelog changelog.txt

    Shows what version the last commit should be, by guessing the
    previous version from the last tag.
    Also, it records found changes to `changelog.txt`.
    The tool will only look at Python files found in the repository.

$ {0} python --from milestone-foo --from-version 1.1.0

    Shows what version the last commit should be, if the previous
    release was `milestone-foo` at version 1.1.0.
    `milestone-foo` can be a tag name or commit identifier.
    The tool will only look at Python files found in the repository.

$ {0} java --from milestone-foo --from-version 1.1.0 --to milestone-bar

    Shows what version `milestone-bar` should be, if the previous
    release was `milestone-foo` at version 1.1.0.
    The tool will only look at Java files found in the repository.
""".format(os.path.basename(sys.argv[0]))
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=description)
    parser.add_argument("handler",
                        type=str,
                        help="what language handler to use {python, java_ast, java_native, clojure}")
    parser.add_argument("-c", "--changelog",
                        type=str,
                        help="generate changelog and write it to a file")
    parser.add_argument("-cstdout", "--changelog-stdout",
                        action="store_true",
                        help="write changelog to stdout (incompatible with `--changelog`)")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="print debugging information to stderr (implies `--info`)")
    parser.add_argument("-i", "--info",
                        action="store_true",
                        help="print progress information to stderr")
    parser.add_argument("-r", "--repo",
                        type=str,
                        help="repository location, will use working directory if not specified")
    parser.add_argument("-f", "--from",
                        type=str,
                        help="identifier of earlier revision, will use last tag if not specified")
    parser.add_argument("-fv", "--from-version",
                        type=str,
                        help="version of earlier revision, will try to guess if not specified!")
    parser.add_argument("-t", "--to",
                        type=str,
                        help="identifier of later revision, will use last commit if not specified")
    parser.add_argument("-bc", "--build-command",
                        type=str,
                        help="what shell command to run so that the project is built")
    parser.add_argument("-br", "--build-root",
                        type=str,
                        help="where the artifacts get placed after the project is built (relative to checkout location)")
    parser.add_argument("-e", "--evaluate",
                        action="store_true",
                        help="run in evaluation mode, measure quality of tags")

    # Parse command-line arguments only if not passed to the function.
    args = kwargs.get("args", parser.parse_args())
    args.f = getattr(args, "from")  # Syntax doesn't allow `args.from`.

    # Set appropriate log level
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format=log_format)
    elif args.info:
        logging.basicConfig(level=logging.INFO,
                            format=log_format)
    else:
        logging.basicConfig(format=log_format)
    logger.info("Logging enabled")

    # Identify VCS
    repo = _Repository(args.repo or os.getcwd())
    if repo.vcs is None:
        logger.error("Failed to identify VCS! Are you running Autobump in the root of the repository?")
        exit(1)
    logger.info("VCS identified as {}".format(repo.vcs))

    # Identify language
    repo_handler = args.handler
    handler_map = {
        "py": python,
        "python": python,
        "java_ast": java_ast,
        "java_native": java_native,
        "clojure": clojure
    }
    try:
        codebase_to_units = handler_map[repo_handler].codebase_to_units
        build_required = handler_map[repo_handler].build_required
    except KeyError:
        logger.error("Invalid handler {} specified!".format(repo_handler))
        exit(1)
    logger.info("Language identified as {}".format(repo_handler))

    # Check for evaluation mode
    # TODO: move this, and maybe other things, to another function
    # this is getting ridiculous
    if args.evaluate:
        if not args.f or not args.to:
            logger.error("Evaluation mode requires supplying a range")
            exit(1)
        args.evaluate = False
        first_revision = args.f
        last_revision = args.to
        logger.info("Running in evaluation mode between {} and {}"
                    .format(args.f, args.to))
        all_revisions = repo.all_tags()
        if first_revision not in all_revisions or last_revision not in all_revisions:
            logger.error("Invalid range, one or more tags not found!")
            exit(1)
        mismatched = []
        for rev_i in range(all_revisions.index(first_revision),
                           all_revisions.index(last_revision) - 1):
            a_revision = all_revisions[rev_i]
            b_revision = all_revisions[rev_i + 1]
            logger.debug("Evaluating revisions {}...{}"
                         .format(a_revision, b_revision))
            setattr(args, "from", a_revision)
            args.to = b_revision
            b_version_expected = Semver.guess_from_string(b_revision)
            b_version_actual = autobump(args=args)
            if b_version_expected != b_version_actual:
                logger.debug("Version found differs from name of tag:\n\tReported: {}\n\tFrom tag: {}"
                             .format(b_version_actual, b_version_expected))
                mismatched.append((a_revision, b_revision, b_version_actual))
        for a_revision, b_revision, actual in mismatched:
            print("{a_revision} --- {b_revision} should have been {a_revision} --- {actual}"
                  .format(a_revision=a_revision, b_revision=b_revision, actual=actual))
        exit(0)

    # Identify revisions
    try:
        a_revision = args.f or repo.last_tag()
        logger.info("Earlier revision identified as {}".format(a_revision))
        b_revision = args.to or repo.last_commit()
        logger.info("Later revision identified as {}".format(b_revision))
    except VersionControlException:
        logger.error("Failed to automatically determine comparison range.")
        exit(1)

    # Identify changelog policy
    changelog_file = None
    if args.changelog and not args.changelog_stdout:
        changelog_file = open(args.changelog, "w")
        logger.info("Writing changelog to {}".format(args.changelog))
    elif args.changelog_stdout and not args.changelog:
        changelog_file = sys.stdout
        logger.info("Writing changelog to stdout")
    elif args.changelog and args.changelog_stdout:
        logger.error("`--changelog` and `--changelog-stdout` are mutually exclusive")
        exit(1)

    # Determine bump
    a_handle, a_location = repo.get_commit(a_revision)
    b_handle, b_location = repo.get_commit(b_revision)
    if build_required:
        logger.info("Handler indicated that a build is required")
        # Options "--build-command" and "--build-root" should be passed in.
        if not args.build_command or not args.build_root:
            logger.error("The {} handler requires that the project is built, but no build command or build root were provided".format(args.handler))
            exit(1)
        a_units = codebase_to_units(a_location, args.build_command, args.build_root)
        b_units = codebase_to_units(b_location, args.build_command, args.build_root)
        # Need to set the 'location' property of all types in both codebases
        # to the location of the latter one. Comparing types may require
        # loading compiled components.
        b_build_location = os.path.join(b_location, args.build_root)
        _patch_types_with_location(a_units, b_build_location)
        _patch_types_with_location(b_units, b_build_location)
    else:
        logger.info("Handler indicated no build is required")
        if args.build_command or args.build_root:
            logger.warn("No build is required, but build-command or build-root given - IGNORING")
        a_units = codebase_to_units(a_location)
        b_units = codebase_to_units(b_location)

    logger.debug("Found {} units in variant A".format(len(a_units)))
    logger.debug("Found {} units in variant B".format(len(b_units)))
    bump = diff.compare_codebases(a_units, b_units, changelog_file)
    logger.info("Bump found to be {}".format(bump))
    if changelog_file not in {None, sys.stdout}:
        changelog_file.close()
        logger.debug("Changelog file closed")

    # Determine version
    a_version = Semver.from_string(args.from_version) if args.from_version is not None else Semver.guess_from_string(a_revision)
    logger.debug("Earlier version is {}".format(a_version))
    b_version = a_version.bump(bump)
    logger.debug("Later version is {}".format(b_version))
    print(b_version)

    # Clean up temporary directories
    a_handle.cleanup()
    b_handle.cleanup()

    # Return the new version if autobump is called from another Python program.
    # Note that this does not influence the exit code.
    return b_version


def main(_):
    # Do not run anything if the module is just imported.
    pass
