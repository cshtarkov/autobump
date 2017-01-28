import os
import unittest
import tempfile
import subprocess
from subprocess import PIPE

from autobump.capir import Unit
from autobump.common import VersionControlException
from autobump.handlers import git


def _run_git(checkout_dir, args):
    """Run Git inside a directory with a list of arguments."""
    child = subprocess.Popen(["git"] + args, cwd=checkout_dir, stdout=PIPE, stderr=PIPE)
    child.communicate()
    if child.returncode != 0:
        raise VersionControlException("\'git {}\' failed!".format(args))


def mock_transformator(checkout_dir):
    """Convert a location on disk containing files
    to a list of units.

    An empty, public unit is created for each file."""
    units = []
    for _, _, files in os.walk(checkout_dir):
        for file in files:
            units.append(Unit(file, [], [], []))
    return units


class TestGitRepoConversion(unittest.TestCase):
    """Test whether the Git handler converts a repo
    to a list of units correctly.

    The transformator function is mocked."""
    def setUp(self):
        self.dir_handle = tempfile.TemporaryDirectory()
        self.dir = self.dir_handle.name
        _run_git(self.dir, ["init"])
        _run_git(self.dir, ["config", "user.email", "mock@autobump.com"])
        _run_git(self.dir, ["config", "user.name", "Mock"])

    def one_commit_fixture(self):
        with open(os.path.join(self.dir, "file1"), "w"):
            pass
        _run_git(self.dir, ["add", "file1"])
        _run_git(self.dir, ["commit", "-a", "-m", '"first commit"'])

    def two_commits_fixture(self):
        with open(os.path.join(self.dir, "file1"), "w"):
            pass
        with open(os.path.join(self.dir, "file2"), "w"):
            pass
        _run_git(self.dir, ["add", "file1"])
        _run_git(self.dir, ["commit", "-a", "-m", '"first commit"'])
        _run_git(self.dir, ["add", "file2"])
        _run_git(self.dir, ["commit", "-a", "-m", '"second commit"'])

    def tearDown(self):
        self.dir_handle.cleanup()

    def test_current_commit(self):
        self.one_commit_fixture()
        handle, location = git.get_commit(self.dir, "HEAD")
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)

    def test_previous_commit(self):
        self.two_commits_fixture()
        handle, location = git.get_commit(self.dir, "HEAD~1")
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)
        self.assertEqual(len([u for u in units if u.name == "file2"]), 0)

    def test_last_commit(self):
        self.two_commits_fixture()
        handle, location = git.get_commit(self.dir, git.last_commit(self.dir))
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)
        self.assertEqual(len([u for u in units if u.name == "file2"]), 1)

    @unittest.skipIf("TRAVIS" in os.environ,
                     "Travis ships an outdated version of Git.")
    def test_last_tag(self):
        self.one_commit_fixture()
        _run_git(self.dir, ["tag", "v1.0.0"])
        self.assertEqual(git.last_tag(self.dir), "v1.0.0")

    @unittest.skipIf("TRAVIS" in os.environ,
                     "Travis ships an outdated version of Git.")
    def test_all_tags(self):
        self.two_commits_fixture()
        _run_git(self.dir, ["checkout", "HEAD~1"])
        _run_git(self.dir, ["tag", "v1.0.0"])
        _run_git(self.dir, ["checkout", "master"])
        _run_git(self.dir, ["tag", "v2.0.0"])
        all_tags = git.all_tags(self.dir)
        self.assertEqual(len(all_tags), 2)
        self.assertEqual(all_tags[0], "v1.0.0")
        self.assertEqual(all_tags[1], "v2.0.0")


if __name__ == "__main__":
    unittest.main()
