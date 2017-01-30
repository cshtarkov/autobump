"""Runs autobump as a whole program on a repository with a Python codebase."""

import os
import re
import imp
import sys
import argparse
import tempfile
from subprocess import CalledProcessError

from autobump.common import popen
from autobump.__init__ import evaluate


def call_git(repo, *args):
    """Call Git in some repository with some arguments.

    If the exit code is not 0, an exception is raised.
    """
    cmd = ["git"] + list(args)
    return_code, _, _ = popen(cmd, cwd=repo)
    if return_code != 0:
        raise CalledProcessError(return_code, cmd)


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

    call_git(repo, "init")
    call_git(repo, "config", "user.email", "mock@autobump.com")
    call_git(repo, "config", "user.name", "Mock")

    _, first_version, _ = commit_history[0]
    all_versions = []

    for commit in commit_history:
        message, new_version, patch = commit
        git_patch(repo, message, patch)
        call_git(repo, "tag", new_version)
        last_version = new_version
        all_versions.append(last_version)

    return first_version, last_version, all_versions


def reconstruct_and_verify(commit_history, setUp, tearDown, **kwargs):
    """Verify that a reconstructed repository matches
    the expected version at every commit."""

    with tempfile.TemporaryDirectory() as repo:
        args = argparse.Namespace(**kwargs)
        args.f, args.to, all_versions = reconstruct(commit_history, repo)
        args.repo = repo
        args.changelog = None
        args.changelog_stdout = None
        args.from_version = None
        args.to_version = None
        args.silence = False
        args.info = False
        args.debug = True
        setUp(repo)
        failed = evaluate(args, all_versions)
        tearDown(repo)

    return failed


def run_scenarios():
    """Find all scenario files in the same directory
    as this file and try to run them. If there are command line arguments,
    run those instead.

    A scenario file is a Python source file which contains a single list
    showing the commit history of a repository, along with what version
    is expected every commit to be.
    """
    scenario_re = re.compile(r"^(?!run_scenarios)(.+)\.py$")
    scenario_dir = os.path.dirname(__file__)
    if scenario_dir == "":
        scenario_dir = os.getcwd()
    if len(sys.argv) <= 1:
        scenario_files = [s for s in os.listdir(scenario_dir) if scenario_re.search(s)]
    else:
        scenario_files = sys.argv[1:]

    total = 0
    failed = 0
    errors = 0
    for scenario_file in scenario_files:
        scenario_name = scenario_re.search(scenario_file).group(1)
        try:
            module = imp.find_module(scenario_name, [scenario_dir])
            scenario = imp.load_module(scenario_name, *module)
            assert hasattr(scenario, "handler")
            print("Running scenario: {}".format(scenario_name))
            total += len(scenario.commit_history) - 1
            commit_history = scenario.commit_history
            setUp = getattr(scenario, "setUp", lambda r: None)
            tearDown = getattr(scenario, "tearDown", lambda r: None)
            failed += reconstruct_and_verify(commit_history,
                                             setUp,
                                             tearDown,
                                             handler=getattr(scenario, "handler"),
                                             build_command=getattr(scenario, "build_command", None),
                                             build_root=getattr(scenario, "build_root", None))
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
