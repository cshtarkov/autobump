import os
import unittest
import tempfile

from autobump.capir import Unit
from autobump.common import popen, VersionControlException
from autobump.handlers import hg


def _run_hg(checkout_dir, args):
    """Run Hg inside a directory with a list of arguments."""
    return_code, _, _ = popen(["hg"] + args, cwd=checkout_dir)
    if return_code != 0:
        raise VersionControlException("\'hg {}\' failed!".format(args))


def mock_transformator(checkout_dir):
    """Convert a location on disk containing files
    to a list of units.

    An empty, public unit is created for each file."""
    # TODO: This can be imported from the git test
    units = []
    for _, _, files in os.walk(checkout_dir):
        for file in files:
            units.append(Unit(file, [], [], []))
    return units


class TestHgRepoConversion(unittest.TestCase):
    """Test whether the Hg handler converts a repo
    to a list of units correctly.

    The transformator function is mocked."""
    def setUp(self):
        self.dir_handle = tempfile.TemporaryDirectory()
        self.dir = self.dir_handle.name
        _run_hg(self.dir, ["init"])
        hgrc_contents = """
[ui]
username = Mock <mock@autobump.com>
"""
        with open(os.path.join(self.dir, ".hg/hgrc"), "w") as hgrc:
            print(hgrc_contents, file=hgrc)

    def one_commit_fixture(self):
        with open(os.path.join(self.dir, "file1"), "w"):
            pass
        _run_hg(self.dir, ["add", "file1"])
        _run_hg(self.dir, ["commit", "-m", '"first commit"'])

    def two_commits_fixture(self):
        with open(os.path.join(self.dir, "file1"), "w"):
            pass
        with open(os.path.join(self.dir, "file2"), "w"):
            pass
        _run_hg(self.dir, ["add", "file1"])
        _run_hg(self.dir, ["commit", "-m", '"first commit"'])
        _run_hg(self.dir, ["add", "file2"])
        _run_hg(self.dir, ["commit", "-m", '"second commit"'])

    def tearDown(self):
        self.dir_handle.cleanup()

    def test_current_commit(self):
        self.one_commit_fixture()
        handle, location = hg.get_commit(self.dir, "0")
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)

    def test_previous_commit(self):
        self.two_commits_fixture()
        handle, location = hg.get_commit(self.dir, "0")
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)
        self.assertEqual(len([u for u in units if u.name == "file2"]), 0)

    def test_last_commit(self):
        self.two_commits_fixture()
        handle, location = hg.get_commit(self.dir, hg.last_commit(self.dir))
        units = mock_transformator(location)
        handle.cleanup()
        self.assertEqual(len([u for u in units if u.name == "file1"]), 1)
        self.assertEqual(len([u for u in units if u.name == "file2"]), 1)

    def test_last_tag(self):
        self.one_commit_fixture()
        _run_hg(self.dir, ["tag", "v1.0.0"])
        self.assertEqual(hg.last_tag(self.dir), "v1.0.0")

    def test_all_tags(self):
        self.two_commits_fixture()
        _run_hg(self.dir, ["update", "0"])
        _run_hg(self.dir, ["tag", "v1.0.0", "-f"])
        _run_hg(self.dir, ["update", "1"])
        _run_hg(self.dir, ["tag", "v2.0.0", "-f"])
        all_tags = hg.all_tags(self.dir)
        self.assertEqual(len(all_tags), 2)
        self.assertEqual(all_tags[0], "v1.0.0")
        self.assertEqual(all_tags[1], "v2.0.0")


if __name__ == "__main__":
    unittest.main()
