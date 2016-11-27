import os
import tempfile
import unittest
from autobump.handlers import clojure


class TestClojureHandlerBase(unittest.TestCase):
    """Used to set up a simple Clojure codebase in a temporary
    location.

    Does not contain any actual tests. Test cases
    are meant to inherit from this class so that they
    all have a non-trivial fixture."""
    def setUp(self):

        sources = [
            ("lib/core.clj",
            """
            (ns lib.core)

            (def constant 3.14)

            (defn- private [])
            (defn no-args [])
            (defn two-args [a b])
            (defn optional-args-vec [a b & [c d]])
            (defn optional-args-map [a b & {c :c d :d}])
            (defn multiple-signatures
              ([a] nil)
              ([a b] nil))
            (defn type-hinting [^String s ^Integer i ^String m])
            """),

            ("lib/other.clj",
             """
             (ns lib.other)
             """)
             ]

        with tempfile.TemporaryDirectory() as dir:
            # Write the above class definitions to source files.
            files = []
            for filename, source in sources:
                fullpath = os.path.join(dir, filename)
                files.append(fullpath)
                os.makedirs(os.path.dirname(fullpath), exist_ok=True)
                with open(fullpath, "w") as f:
                    f.write(source)

            self.codebase = clojure.codebase_to_units(dir)


class TestUnits(TestClojureHandlerBase):

    def setUp(self):
        super(TestUnits, self).setUp()

    def test_ns(self):
        self.assertTrue("lib.core" in self.codebase)
        self.assertTrue("lib.other" in self.codebase)


class TestFields(TestClojureHandlerBase):

    def setUp(self):
        super(TestFields, self).setUp()

    def test_field_visible(self):
        self.assertTrue("constant" in self.codebase["lib.core"].fields)


class TestFunctions(TestClojureHandlerBase):

    def setUp(self):
        super(TestFunctions, self).setUp()
        self.functions = self.codebase["lib.core"].functions

    def test_private_function(self):
        self.assertFalse("private" in self.functions)

    def test_public_function(self):
        self.assertTrue("no-args" in self.functions)

    def test_empty_signature(self):
        self.assertEqual(0, len(self.functions["no-args"].signatures[0].parameters))

    def test_several_arguments(self):
        self.assertEqual(2, len(self.functions["two-args"].signatures[0].parameters))

    def test_optional_args_vector(self):
        parameters = self.functions["optional-args-vec"].signatures[0].parameters
        self.assertEqual(4, len(parameters))
        self.assertTrue(parameters[2].default_value)
        self.assertTrue(parameters[3].default_value)

    def test_optional_args_map(self):
        parameters = self.functions["optional-args-map"].signatures[0].parameters
        self.assertEqual(4, len(parameters))
        self.assertTrue(parameters[2].default_value)
        self.assertTrue(parameters[3].default_value)

    def test_multiple_signatures(self):
        signatures = self.functions["multiple-signatures"].signatures
        self.assertEqual(2, len(signatures))
        self.assertEqual(1, len(signatures[0].parameters))
        self.assertEqual(2, len(signatures[1].parameters))


class TestTypes(TestClojureHandlerBase):

    def setUp(self):
        super(TestTypes, self).setUp()

    def test_type_hinting(self):
        parameters = self.codebase["lib.core"].functions["type-hinting"].signatures[0].parameters
        self.assertFalse(parameters[0].type.is_compatible(parameters[1].type))
        self.assertTrue(parameters[0].type.is_compatible(parameters[2].type))


if __name__ == "__main__":
    unittest.main()