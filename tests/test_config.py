import unittest

from autobump import config
from autobump.config import with_config_override


class TestGetValues(unittest.TestCase):
    """Get values of configurable options."""

    def test_get_nonexistant(self):
        self.assertRaises(KeyError, config.get, "doesnt", "exist")

    @with_config_override("autobump", "git", "nondefault")
    def test_get_value(self):
        self.assertEqual(config.get("autobump", "git"), "nondefault")

class TestIgnored(unittest.TestCase):
    """Test whether files and directories get ignored."""

    @with_config_override("ignore", "files", "filename\n")
    def test_ignore_file(self):
        self.assertTrue(config.file_ignored("filename"))

    @with_config_override("ignore", "files", "filename1\nfilename2\n")
    def test_ignore_multiple_files(self):
        self.assertTrue(config.file_ignored("filename1"))
        self.assertTrue(config.file_ignored("filename2"))

    @with_config_override("ignore", "files_re", "^filenames?$")
    def test_ignore_file_regex(self):
        self.assertTrue(config.file_ignored("filename"))
        self.assertTrue(config.file_ignored("filenames"))
        self.assertFalse(config.file_ignored("filename_other"))

    @with_config_override("ignore", "dirs", "dirname\n")
    def test_ignore_dir(self):
        self.assertTrue(config.dir_ignored("dirname"))

    @with_config_override("ignore", "dirs", "dirname1\ndirname2\n")
    def test_ignore_multiple_dirs(self):
        self.assertTrue(config.dir_ignored("dirname1"))
        self.assertTrue(config.dir_ignored("dirname2"))

    @with_config_override("ignore", "dirs_re", "^dirnames?$")
    def test_ignore_dir_regex(self):
        self.assertTrue(config.dir_ignored("dirname"))
        self.assertTrue(config.dir_ignored("dirnames"))
        self.assertFalse(config.dir_ignored("dirname_other"))


if __name__ == "__main__":
    unittest.main()
