import unittest
from autobump.core import Bump
from autobump.__init__ import _Semver


class TestSemver(unittest.TestCase):
    """Test representation of a semantic version."""

    def test_create(self):
        ver = _Semver(5, 3, 2)
        self.assertEqual(ver.major, 5)
        self.assertEqual(ver.minor, 3)
        self.assertEqual(ver.patch, 2)

    def test_create_invalid(self):
        self.assertRaises(AssertionError, _Semver, "a", 3, 2)

    def test_create_from_string(self):
        ver = _Semver.from_string("5.3.2")
        self.assertEqual(ver.major, 5)
        self.assertEqual(ver.minor, 3)
        self.assertEqual(ver.patch, 2)

    def test_create_from_tuple(self):
        ver = _Semver.from_tuple((5, 3, 2))
        self.assertEqual(ver.major, 5)
        self.assertEqual(ver.minor, 3)
        self.assertEqual(ver.patch, 2)

    def test_guess_from_string(self):
        guesses = {
            "v1": "1.0.0",
            "v2.3": "2.3.0",
            "v5.3.1": "5.3.1",
            "version5": "5.0.0",
            "1.2.3": "1.2.3",
            "8": "8.0.0",
            "9.0": "9.0.0"
        }
        for string, version in guesses.items():
            self.assertEqual(str(_Semver.guess_from_string(string)), version)

    def test_guess_from_string_invalid(self):
        self.assertRaises(_Semver.NotAVersionNumber, _Semver.guess_from_string, "not a version")

    def test_bump(self):
        a = _Semver(2, 1, 0)
        b = a.bump(Bump.major)
        self.assertEqual(b.major, 3)
        b = a.bump(Bump.minor)
        self.assertEqual(b.minor, 2)
        b = a.bump(Bump.patch)
        self.assertEqual(b.patch, 1)
