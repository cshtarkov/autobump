"""Implement source control handling for Mercurial."""
import os
import tempfile

from autobump import config
from autobump.common import popen, VersionControlException


def _clone_repo(repo, checkout_dir):
    """Clone a hg repository into a directory."""
    return_code, _, _ = popen([config.hg(), "clone", repo, checkout_dir])
    if return_code != 0:
        raise VersionControlException("Cloning {} into {} failed!"
                                      .format(repo, checkout_dir))


def _checkout_commit(checkout_dir, commit):
    """Checkout a Hg commit at some location."""
    return_code, _, _ = popen([config.hg(), "update", commit], cwd=checkout_dir)
    if return_code != 0:
        raise VersionControlException("Checking out commit {} at {} failed!"
                                      .format(commit, checkout_dir))


def hg_get_commit(repo, commit):
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


def hg_last_tag(repo):
    return_code, stdout, stderr = popen([config.hg(), "log", "-r", '"."', "--template", "{latesttag}"], cwd=repo)
    if return_code != 0:
        raise VersionControlException("Failed to get last tag of Hg repository {}"
                                      .format(repo))
    return stdout


def hg_all_tags(repo):
    return_code, stdout, stderr = popen([config.hg(), "log", "-r", 'tag()', "--template", '{tags}\n'], cwd=repo)
    if return_code != 0:
        raise VersionControlException("Failed to get tags of Hg repository {}"
                                      .format(repo))
    return stdout.split()


def hg_last_commit(repo):
    return_code, stdout, stderr = popen([config.hg(), "log", "-r", "tip", "--template", "{rev}"], cwd=repo)
    if return_code != 0:
        raise VersionControlException("Failed to get last commit of Hg repository {}"
                                             .format(repo))
    return stdout.split()[0]


get_commit = hg_get_commit
all_tags = hg_all_tags
last_tag = hg_last_tag
last_commit = hg_last_commit
