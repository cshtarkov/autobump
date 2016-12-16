"""Runs autobump as a whole program on a repository with a Python codebase."""

import os
import re
import imp
import sys
import tempfile
import subprocess

from autobump.__init__ import autobump


class IteratorWithRunner(object):
    """Iterator over an entire list, returning
    tuples of the form (a[i], a[i+k]).
    Iterations stops once i+k is the final element."""
    def __init__(self, a, k=1):
        self.a = a
        self.k = k

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i + self.k >= len(self.a):
            raise StopIteration
        self.i += 1
        return (self.a[self.i - 1], self.a[self.i - 1 + self.k])


def call_autobump(*args):
    """Call autobump as if it was called as a standalone program.
    Returns the new version number as reported by autobump."""
    old_argv = sys.argv
    sys.argv[1:] = ["-d"] + list(args)
    version = autobump()
    sys.argv = old_argv
    return str(version)


def call_git(repo, *args):
    """Call Git in some repository with some arguments.

    If the exit code is not 0, an exception is raised."""
    child = subprocess.Popen(["git"] + list(args),
                             cwd=repo)
    child.communicate()
    if child.returncode != 0:
        raise subprocess.CalledProcessError()


def git_patch(repo, message, patch):
    """Apply a patch to a repository and immediately
    afterwards commit with a message."""
    patch_file = tempfile.NamedTemporaryFile(delete=False)
    patch_file.write(patch.encode("ascii"))
    patch_file.close()
    call_git(repo, "apply", patch_file.name)
    call_git(repo, "add", "-A")
    call_git(repo, "commit", "-a", "-m", message)
    os.unlink(patch_file.name)


def reconstruct_and_verify(commit_history):
    """Reconstruct a repository based on its commit
    history and check whether the version proposed by
    autobump match the expected ones."""

    failed = 0
    with tempfile.TemporaryDirectory() as repo:
        # First, create an empty repository.
        call_git(repo, "init")
        call_git(repo, "config", "user.email", "mock@autobump.com")
        call_git(repo, "config", "user.name", "Mock")

        # Then, apply the first patch to get things started.
        message, version, patch = commit_history[0]
        git_patch(repo, message, patch)
        call_git(repo, "tag", version)

        # Commit the remaining patches, each time tagging
        # the commit and checking whether the proposed version
        # matches the expected one.
        for before, after in IteratorWithRunner(commit_history):
            _, previous_version, _ = before
            message, new_version, patch = after
            git_patch(repo, message, patch)
            # TODO: Don't hardcode language.
            proposed_version = call_autobump("python", "-r", repo)
            call_git(repo, "tag", new_version)
            if new_version != proposed_version:
                failed += 1
                call_git(repo, "diff", previous_version, new_version)

    return failed


def run_scenarios():
    """Find all scenario files in the same directory
    as this file and try to run them.

    A scenario file is a Python source file which contains a single list
    showing the commit history of a repository, along with what version
    is expected every commit to be.
    """
    scenario_re = re.compile(r"^(?!run\-scenarios)(.+)\.py$")
    scenario_dir = os.path.dirname(__file__)
    if scenario_dir == "":
        scenario_dir = os.getcwd()
    scenario_files = [s for s in os.listdir(scenario_dir) if scenario_re.search(s)]

    total = 0
    failed = 0
    errors = 0
    for scenario_file in scenario_files:
        scenario_name = scenario_re.search(scenario_file).group(1)
        try:
            module = imp.find_module(scenario_name, [scenario_dir])
            scenario = imp.load_module(scenario_name, *module)
            print("Running scenario: {}".format(scenario_name))
            total += len(scenario.commit_history) - 1
            failed += reconstruct_and_verify(scenario.commit_history)
        except ImportError as ex:
            errors += 1
            print("Failed to run scenario: {}".format(scenario_name))
            print(ex)

    print()
    print("{} tests, {} failed, {} errors."
          .format(total, failed, errors))
    exit(failed > 0 or errors > 0)


if __name__ == "__main__":
    run_scenarios()
