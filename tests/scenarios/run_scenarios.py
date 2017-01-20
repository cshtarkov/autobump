"""Runs autobump as a whole program on a repository with a Python codebase."""

import os
import re
import imp
import sys
import tempfile
import subprocess
from subprocess import PIPE

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


def call_git(repo, *args, silent=True):
    """Call Git in some repository with some arguments.

    If the exit code is not 0, an exception is raised."""
    stdout_pipe, stderr_pipe = (PIPE, PIPE) if silent else (sys.stdout, sys.stderr)
    cmd = ["git"] + list(args)
    child = subprocess.Popen(cmd,
                             cwd=repo,
                             stdout=stdout_pipe,
                             stderr=stderr_pipe)
    child.communicate()
    if child.returncode != 0:
        raise subprocess.CalledProcessError(child.returncode, cmd)


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


def reconstruct(commit_history, repo):
    """Reconstruct a repository based on its commit
    history."""

    # First, create an empty repository.
    call_git(repo, "init")
    call_git(repo, "config", "user.email", "mock@autobump.com")
    call_git(repo, "config", "user.name", "Mock")

    # Then, apply the first patch to get things started.
    message, version, patch = commit_history[0]
    git_patch(repo, message, patch)
    call_git(repo, "tag", version)

    # Commit the remaining patches.
    for _, after in IteratorWithRunner(commit_history):
        message, new_version, patch = after
        git_patch(repo, message, patch)
        call_git(repo, "tag", new_version)


def reconstruct_and_verify(commit_history, handler, build_command, build_root):
    """Verify that a reconstructed repository matches
    the expected version at every commit."""

    failed = 0
    with tempfile.TemporaryDirectory() as repo:
        reconstruct(commit_history, repo)

        for before, after in IteratorWithRunner(commit_history):
            _, previous_version, _ = before
            message, new_version, patch = after
            proposed_version = call_autobump(handler,
                                             "-r", repo,
                                             "--from", previous_version,
                                             "--to", new_version,
                                             "--build-command", build_command,
                                             "--build-root", build_root)
            if new_version != proposed_version:
                failed += 1
                print("\nVersion mismatch: expected {}, got {}.\nMessage and patch:\n{}\n{}"
                      .format(new_version, proposed_version, message, patch))

    return failed


def run_scenarios():
    """Find all scenario files in the same directory
    as this file and try to run them.

    A scenario file is a Python source file which contains a single list
    showing the commit history of a repository, along with what version
    is expected every commit to be.
    """
    scenario_re = re.compile(r"^(?!run_scenarios)(.+)\.py$")
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
            commit_history = scenario.commit_history
            handler = scenario.handler
            build_command = getattr(scenario, "build_command", "none")
            build_root = getattr(scenario, "build_root", "none")
            failed += reconstruct_and_verify(commit_history, handler, build_command, build_root)
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
