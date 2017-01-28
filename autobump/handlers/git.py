"""Implement source control handling for Git."""
import os
import tempfile

from autobump import config
from autobump.common import popen, VersionControlException


def _clone_repo(repo, checkout_dir):
    """Clone a git repository into a directory."""
    return_code, _, _ = popen([config.git(), "clone", repo, checkout_dir])
    if return_code != 0:
        raise VersionControlException("Cloning {} into {} failed!"
                                      .format(repo, checkout_dir))


def _checkout_commit(checkout_dir, commit):
    """Checkout a Git commit at some location."""
    return_code, _, _ = popen([config.git(), "checkout", commit], cwd=checkout_dir)
    if return_code != 0:
        raise VersionControlException("Checking out commit {} at {} failed!"
                                      .format(commit, checkout_dir))


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
    return temp_dir_handle, checkout_dir


def git_all_tags(repo):
    return_code, stdout, stderr = popen([config.git(), "tag", "--sort", "version:refname"], cwd=repo)
    if return_code != 0:
        raise VersionControlException("Failed to get tags of Git repository {}\n{}"
                                      .format(repo, stderr))
    return stdout.split()


def git_last_tag(repo):
    all_tags = git_all_tags(repo)
    if len(all_tags) == 0:
        raise VersionControlException("No last tag")
    return all_tags[-1]


def git_last_commit(repo):
    return_code, stdout, stderr = popen([config.git(), "log", "-1", "--oneline"], cwd=repo)
    if return_code != 0:
        raise VersionControlException("Failed to get last commit of Git repository {}"
                                      .format(repo))
    return stdout.split()[0]


get_commit = git_get_commit
all_tags = git_all_tags
last_tag = git_last_tag
last_commit = git_last_commit
