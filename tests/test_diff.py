import unittest

from autobump.diff import Bump, compare_codebases
from autobump.common import Type, Field, Parameter, Signature, Function


# Mock Type System
class _Generic(Type):
    pass


class _A(_Generic):
    pass


class _CompatWithA(_A):
    pass


class _IncompatWithA(_Generic):
    pass


_generic = _Generic()
_a = _A()
_compatWithA = _CompatWithA()
_incompatWithA = _IncompatWithA()


class TestSingleEntities(unittest.TestCase):
    """Test comparison of codebases consisting of a single entity.

    Each test gives two variants of the same codebase
    which contain a single entity
    and expects a major, minor, patch or no bump."""
    def setUp(self):
        self.first = dict()
        self.second = dict()

    def expect(self, bump):
        self.assertEqual(compare_codebases(self.first, self.second, None), bump)

    # Fields.

    def test_add_field(self):
        self.second["foo"] = (Field("foo", _generic))
        self.expect(Bump.minor)

    def test_remove_field(self):
        self.first["foo"] = (Field("foo", _generic))
        self.expect(Bump.major)

    def test_change_type_of_field_compatible(self):
        self.first["foo"] = (Field("foo", _a))
        self.second["foo"] = (Field("foo", _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_field_incompatible(self):
        self.first["foo"] = (Field("foo", _a))
        self.second["foo"] = (Field("foo", _incompatWithA))
        self.expect(Bump.major)

    # Functions.

    def test_add_function(self):
        self.second["foo"] = (Function("foo", _generic))
        self.expect(Bump.minor)

    def test_remove_function(self):
        self.first["foo"] = (Function("foo", _generic))
        self.expect(Bump.major)

    def test_change_type_of_visible_function_compatible(self):
        self.first["foo"] = (Function("foo", _a))
        self.second["foo"] = (Function("foo", _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_visible_function_incompatible(self):
        self.first["foo"] = (Function("foo", _a))
        self.second["foo"] = (Function("foo", _incompatWithA))
        self.expect(Bump.major)

    # Function signatures.

    def test_change_signature_add_parameter_nodefault(self):
        self.first["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                            Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                           Parameter("b", _generic),
                                            Parameter("c", _generic)])]))
        self.expect(Bump.major)

    def test_change_signature_add_parameter_default(self):
        self.first["foo"] = (Function("foo", _generic, [Signature([Parameter("a", _generic),
                                                                Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                           Parameter("b", _generic),
                                            Parameter("c", _generic, default_value=True)])]))
        self.expect(Bump.minor)

    def test_change_signature_remove_parameter_nodefault(self):
        self.first["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                            Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("a", _generic)])]))
        self.expect(Bump.major)

    def test_change_signature_remove_parameter_default(self):
        self.first["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                            Parameter("b", _generic, default_value=True)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("a", _generic)])]))
        self.expect(Bump.major)

    def test_change_signature_rename_parameter(self):
        self.first["foo"] = (Function("foo", _generic,
                                   [Signature([Parameter("a", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("b", _generic)])]))
        self.expect(Bump.patch)

    def test_change_signature_rename_parameters(self):
        self.first["foo"] = (Function("foo", _generic,
                                [Signature([Parameter("a", _generic),
                                            Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                 [Signature([Parameter("b", _generic),
                                             Parameter("a", _generic)])]))
        self.expect(Bump.patch)

    def test_change_signature_parameter_type_compatible(self):
        self.first["foo"] = (Function("foo", _a,
                                   [Signature([Parameter("a", _generic)])]))
        self.second["foo"] = (Function("foo", _compatWithA,
                                    [Signature([Parameter("a", _generic)])]))
        self.expect(Bump.patch)

    def test_change_signature_parameter_type_incompatible(self):
        self.first["foo"] = (Function("foo", _a,
                                   [Signature([Parameter("a", _generic)])]))
        self.second["foo"] = (Function("foo", _incompatWithA,
                                    [Signature([Parameter("a", _generic)])]))
        self.expect(Bump.major)

    def test_multiple_signatures_compat(self):
        self.first["foo"] = (Function("foo", _generic,
                                   [Signature([Parameter("a", _a)]),
                                    Signature([Parameter("a", _a), Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("a", _a)]),
                                     Signature([Parameter("a", _compatWithA), Parameter("b", _generic)])]))
        self.expect(Bump.patch)

    def test_multiple_signatures_new_one(self):
        self.first["foo"] = (Function("foo", _generic,
                                   [Signature([Parameter("a", _a)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("a", _a)]),
                                     Signature([Parameter("a", _a), Parameter("b", _generic)])]))
        self.expect(Bump.minor)

    def test_multiple_signatures_remove_one(self):
        self.first["foo"] = (Function("foo", _generic,
                                   [Signature([Parameter("a", _a)]),
                                    Signature([Parameter("a", _a), Parameter("b", _generic)])]))
        self.second["foo"] = (Function("foo", _generic,
                                    [Signature([Parameter("a", _a)])]))
        self.expect(Bump.major)

if __name__ == "__main__":
    unittest.main()
