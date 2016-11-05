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


def git_get_commit(repo, commit):
    """Get a directory containing a commit found in a repository.

    The caller is responsible for cleaning up the directory afterwards
    by calling cleanup() on the handle."""
    repo_path = os.path.abspath(repo)
    repo_name = os.path.basename(repo)
    temp_dir_handle = tempfile.TemporaryDirectory()
    temp_dir = temp_dir_handle.name
    checkout_dir = os.path.join(temp_dir, repo_name)
    _clone_repo(repo_path, checkout_dir)
    _checkout_commit(checkout_dir, commit)
    return temp_dir_handle, temp_dir

get_commit = git_get_commit
