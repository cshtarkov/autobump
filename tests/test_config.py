import unittest
import configparser

from autobump import config
from autobump.config import config_override


class TestGetValues(unittest.TestCase):
    """Get values of configurable options."""

    def test_get_nonexistant(self):
        self.assertRaises(KeyError, config.get, "doesnt", "exist")

    @config_override("autobump", "git", "nondefault")
    def test_get_value(self):
        self.assertEqual(config.get("autobump", "git"), "nondefault")


class TestPermaOverride(unittest.TestCase):
    """Test permanently overriding values."""

    @config_override("autobump", "git", "git")
    def test_override_cached(self):
        config.set("autobump", "git", "nondefault")
        self.assertEqual(config.get("autobump", "git"), "nondefault")

    def test_override_noncached(self):
        config.set("autobump", "clojure", "nondefault")
        self.assertEqual(config.get("autobump", "clojure"), "nondefault")

    @config_override("autobump", "git", "nondefault")
    def test_permaoverride_already_overriden(self):
        config.set("autobump", "git", "other")
        self.assertEqual(config.get("autobump", "git"), "other")


class TestOverride(unittest.TestCase):
    """Test overriding values."""

    def test_override_with_context(self):
        with config.config_overrides({"clojure": {"classpath": "/opt:"}}):
            self.assertEqual(config.get("clojure", "classpath"), "/opt:")

    def test_override_with_decorator(self):
        @config_override("autobump", "hg", "nondefault")
        def inside():
            return config.get("autobump", "hg")
        self.assertEqual(inside(), "nondefault")


class TestIgnored(unittest.TestCase):
    """Test whether files and directories get ignored."""

    @config_override("ignore", "files", "filename\n")
    def test_ignore_file(self):
        self.assertTrue(config.file_ignored("filename"))

    @config_override("ignore", "files", "filename1\nfilename2\n")
    def test_ignore_multiple_files(self):
        self.assertTrue(config.file_ignored("filename1"))
        self.assertTrue(config.file_ignored("filename2"))

    @config_override("ignore", "dirs", "dirname\n")
    def test_ignore_dir(self):
        self.assertTrue(config.dir_ignored("dirname"))

    @config_override("ignore", "dirs", "dirname1\ndirname2\n")
    def test_ignore_multiple_dirs(self):
        self.assertTrue(config.dir_ignored("dirname1"))
        self.assertTrue(config.dir_ignored("dirname2"))

    @config_override("ignore", "entities", "entityname\n")
    def test_ignore_entity(self):
        self.assertTrue(config.entity_ignored("entityname"))

    @config_override("ignore", "entities", "entityname1\nentityname2\n")
    def test_ignore_multiple_entities(self):
        self.assertTrue(config.entity_ignored("entityname1"))
        self.assertTrue(config.entity_ignored("entityname2"))


class TestOnlyConsider(unittest.TestCase):
    """Test whitelists."""

    @config_override("only_consider", "files", "special.txt")
    def test_only_file(self):
        self.assertFalse(config.file_ignored("special.txt"))
        self.assertTrue(config.file_ignored("somethingelse.txt"))

    @config_override("only_consider", "dirs", "special")
    def test_only_dir(self):
        self.assertFalse(config.dir_ignored("special"))
        self.assertTrue(config.dir_ignored("somethingelse"))

    @config_override("only_consider", "entities", "Entity")
    def test_only_entity(self):
        self.assertFalse(config.entity_ignored("Entity"))
        self.assertTrue(config.entity_ignored("AnotherOne"))


class TestExportConfig(unittest.TestCase):
    """Test exporting the config."""

    def test_exported_config_same_as_current_config(self):
        exported = configparser.ConfigParser()
        exported.read_string(config.export_config())
        for category in config.defaults:
            for name in config.defaults[category]:
                self.assertEqual(config._value_to_string(config.get(category, name)), exported[category][name])


if __name__ == "__main__":
    unittest.main()
