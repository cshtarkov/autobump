import os
import tempfile
import unittest

from autobump.config import config_overrides
from autobump.handlers import clojure


class TestClojureHandlerBase(unittest.TestCase):
    """Used to set up a simple Clojure codebase in a temporary
    location.

    Does not contain any actual tests. Test cases
    are meant to inherit from this class so that they
    all have a non-trivial fixture."""
    @classmethod
    def setUpClass(cls):

        sources = [
            ("lib/core.clj",
            """
            (ns lib.core)

            (def constant 3.14)
            (def ^{:private true} private-def)

            (defn- private [])
            (defn no-args [])
            (defn two-args [a b])
            (defn destructured-args-vec [[a b]])
            (defn destructured-args-map [{a :a b :b}])
            (defn optional-args-vec [a b & [c d]])
            (defn optional-args-map [a b & {c :c d :d}])
            (defn multiple-signatures
              ([a] nil)
              ([a b] nil))
            (defn type-hinting [^String s ^Integer i ^Object m])
            (defmacro some-macro [])
            (defmacro some-macro-arg [a])

            (defrecord RecordA [f1 f2])
            (defprotocol ProtocolA
              (method1 [a])
              (method2 [a b]))
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

            with config_overrides({"clojure": {"classpath": dir + ":"}}):
                cls.codebase = clojure.codebase_to_units(dir)

    def setUp(self):
        self.codebase = self.__class__.codebase


class TestUnits(TestClojureHandlerBase):

    def setUp(self):
        super(TestUnits, self).setUp()

    def test_ns(self):
        self.assertTrue("lib.core" in self.codebase)
        self.assertTrue("lib.other" in self.codebase)


class TestFields(TestClojureHandlerBase):

    def setUp(self):
        super(TestFields, self).setUp()

    def test_field_private(self):
        self.assertFalse("private-def" in self.codebase["lib.core"].fields)

    def test_field_visible(self):
        self.assertTrue("constant" in self.codebase["lib.core"].fields)

    def test_protocol_field(self):
        self.assertTrue("ProtocolA" in self.codebase["lib.core"].fields)


class TestFunctions(TestClojureHandlerBase):

    def setUp(self):
        super(TestFunctions, self).setUp()
        self.functions = self.codebase["lib.core"].functions

    def test_private_function(self):
        self.assertFalse("private" in self.functions)

    def test_public_function(self):
        self.assertTrue("no-args" in self.functions)

    def test_macro(self):
        self.assertTrue("some-macro" in self.functions)

    def test_macro_arg(self):
        self.assertTrue("some-macro-arg" in self.functions)
        self.assertEqual(1, len(self.functions["some-macro-arg"].signatures[0].parameters))

    def test_empty_signature(self):
        self.assertEqual(0, len(self.functions["no-args"].signatures[0].parameters))

    def test_several_arguments(self):
        self.assertEqual(2, len(self.functions["two-args"].signatures[0].parameters))

    def test_destructured_args_vector(self):
        parameters = self.functions["destructured-args-vec"].signatures[0].parameters
        # TODO: Treat this as a single "anon-vector" or multiple variables?
        # TODO: Check whether the destructured variables are optional?
        self.assertEqual(1, len(parameters))

    def test_destructured_args_map(self):
        parameters = self.functions["destructured-args-map"].signatures[0].parameters
        self.assertEqual(1, len(parameters))

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

    def test_record_functions(self):
        self.assertTrue("->RecordA" in self.functions)
        self.assertTrue("map->RecordA" in self.functions)

    def test_protocol_methods(self):
        self.assertTrue("method1" in self.functions)
        self.assertTrue("method2" in self.functions)


class TestTypes(TestClojureHandlerBase):

    def setUp(self):
        super(TestTypes, self).setUp()

    def test_type_hinting(self):
        parameters = self.codebase["lib.core"].functions["type-hinting"].signatures[0].parameters
        self.assertFalse(parameters[0].type.is_compatible(parameters[1].type))
        self.assertTrue(parameters[0].type.is_compatible(parameters[2].type))

    def test_type_compatibility(self):
        parameters = self.codebase["lib.core"].functions["type-hinting"].signatures[0].parameters
        # String replaced by Object
        self.assertTrue(parameters[0].type.is_compatible(parameters[2].type))
        # Object replaced by String
        self.assertFalse(parameters[2].type.is_compatible(parameters[0].type))


if __name__ == "__main__":
    unittest.main()
