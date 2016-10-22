"""Implement source control handling for Git."""
import os
import tempfile
import subprocess
from subprocess import PIPE
from autobump.common import VersionControlException


def _clone_repo(repo, checkout_dir):
    """Clone a git repository into a directory."""
    child = subprocess.Popen(["git", "clone", repo, checkout_dir], stdout=PIPE, stderr=PIPE)
    child.communicate()
    if child.returncode != 0:
        raise VersionControlException("Cloning {} into {} failed!".format(repo, checkout_dir))


def _checkout_commit(checkout_dir, commit):
    """Checkout a Git commit at some location."""
    child = subprocess.Popen(["git", "checkout", commit], cwd=checkout_dir, stdout=PIPE, stderr=PIPE)
    child.communicate()
    if child.returncode != 0:
        raise VersionControlException("Checking out commit {} at {} failed!".format(commit, checkout_dir))


def git_commit_to_units(repo, commit, transformator):
    """Converts a commit from a repository into a list of units.

    The transformator function should be able to convert a location
    on disk where the codebase is into a list of Units."""
    repo_path = os.path.abspath(repo)
    repo_name = os.path.basename(repo)
    with tempfile.TemporaryDirectory() as temp_dir:
        checkout_dir = os.path.join(temp_dir, repo_name)
        _clone_repo(repo_path, checkout_dir)
        _checkout_commit(checkout_dir, commit)
        return transformator(checkout_dir)

commit_to_units = git_commit_to_units
