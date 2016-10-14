import unittest
from autobump.core import Bump, compare_codebases
from autobump.common import Visibility, Type, Field, Parameter, Signature, Function


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


class TestSingleProperties(unittest.TestCase):
    """Test comparison of codebases consisting of a single property.

    Each test gives two variants of the same codebase
    which contain a single code property
    and expects a major, minor, patch or no bump."""
    def setUp(self):
        self.first = []
        self.second = []

    def expect(self, bump):
        self.assertEqual(compare_codebases(self.first, self.second), bump)

    # Fields.

    def test_reduce_visibility_of_field(self):
        self.first.append(Field("foo", Visibility.public, _generic))
        self.second.append(Field("foo", Visibility.unit, _generic))
        self.expect(Bump.major)

    def test_increase_visibility_of_field(self):
        self.first.append(Field("foo", Visibility.unit, _generic))
        self.second.append(Field("foo", Visibility.public, _generic))
        self.expect(Bump.minor)

    def test_add_nonvisibile_field(self):
        self.second.append(Field("foo", Visibility.unit, _generic))
        self.expect(Bump.patch)

    def test_add_visible_field(self):
        self.second.append(Field("foo", Visibility.public, _generic))
        self.expect(Bump.minor)

    def test_remove_nonvisible_field(self):
        self.first.append(Field("foo", Visibility.unit, _generic))
        self.expect(Bump.patch)

    def test_remove_visible_field(self):
        self.first.append(Field("foo", Visibility.public, _generic))
        self.expect(Bump.major)

    def test_change_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, _generic, default_value=1))
        self.second.append(Field("foo", Visibility.public, _generic, default_value=2))
        # TODO: What bump is this?

    def test_remove_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, _generic, default_value=1))
        self.second.append(Field("foo", Visibility.public, _generic, default_value=None))
        self.expect(Bump.major)

    def test_add_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, _generic, default_value=None))
        self.second.append(Field("foo", Visibility.public, _generic, default_value=1))
        # TODO: What bump is this?

    def test_change_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, _generic, default_value=1))
        self.second.append(Field("foo", Visibility.unit, _generic, default_value=2))
        self.expect(Bump.patch)

    def test_remove_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, _generic, default_value=1))
        self.second.append(Field("foo", Visibility.unit, _generic, default_value=None))
        self.expect(Bump.patch)

    def test_add_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, _generic, default_value=None))
        self.second.append(Field("foo", Visibility.unit, _generic, default_value=1))
        self.expect(Bump.patch)

    def test_change_type_of_nonvisible_field_compatible(self):
        self.first.append(Field("foo", Visibility.unit, _a))
        self.second.append(Field("foo", Visibility.unit, _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_nonvisible_field_incompatible(self):
        self.first.append(Field("foo", Visibility.unit, _a))
        self.second.append(Field("foo", Visibility.unit, _incompatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_visible_field_compatible(self):
        self.first.append(Field("foo", Visibility.public, _a))
        self.second.append(Field("foo", Visibility.public, _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_visible_field_incompatible(self):
        self.first.append(Field("foo", Visibility.public, _a))
        self.second.append(Field("foo", Visibility.public, _incompatWithA))
        self.expect(Bump.major)

    # Functions.

    def test_reduce_visibility_of_function(self):
        self.first.append(Function("foo", Visibility.public, _generic))
        self.second.append(Function("foo", Visibility.unit, _generic))
        self.expect(Bump.major)

    def test_increase_visibility_of_function(self):
        self.first.append(Function("foo", Visibility.unit, _generic))
        self.second.append(Function("foo", Visibility.public, _generic))
        self.expect(Bump.minor)

    def test_add_nonvisibile_function(self):
        self.second.append(Function("foo", Visibility.unit, _generic))
        self.expect(Bump.patch)

    def test_add_visible_function(self):
        self.second.append(Function("foo", Visibility.public, _generic))
        self.expect(Bump.minor)

    def test_remove_nonvisible_function(self):
        self.first.append(Function("foo", Visibility.unit, _generic))
        self.expect(Bump.patch)

    def test_remove_visible_function(self):
        self.first.append(Function("foo", Visibility.public, _generic))
        self.expect(Bump.major)

    def test_change_type_of_nonvisible_function_compatible(self):
        self.first.append(Function("foo", Visibility.unit, _a))
        self.second.append(Function("foo", Visibility.unit, _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_nonvisible_function_incompatible(self):
        self.first.append(Function("foo", Visibility.unit, _a))
        self.second.append(Function("foo", Visibility.unit, _incompatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_visible_function_compatible(self):
        self.first.append(Function("foo", Visibility.public, _a))
        self.second.append(Function("foo", Visibility.public, _compatWithA))
        self.expect(Bump.patch)

    def test_change_type_of_visible_function_incompatible(self):
        self.first.append(Function("foo", Visibility.public, _a))
        self.second.append(Function("foo", Visibility.public, _incompatWithA))
        self.expect(Bump.major)

    # Function signatures.

    def test_change_signature_add_parameter_nodefault(self):
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic),
                                           Parameter("b", _generic)])))
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic),
                                           Parameter("b", _generic),
                                           Parameter("c", _generic)])))
        self.expect(Bump.major)

    def test_change_signature_add_parameter_default(self):
        self.first.append(Function("foo", Visibility.public, _generic, Signature([Parameter("a", _generic),
                                           Parameter("b", _generic)])))
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic),
                                           Parameter("b", _generic),
                                           Parameter("c", _generic, default_value=True)])))
        # TODO: What bump is this?

    def test_change_signature_remove_parameter_nodefault(self):
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic),
                                           Parameter("b", _generic)])))
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic)])))
        self.expect(Bump.major)

    def test_change_signature_remove_parameter_default(self):
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic),
                                           Parameter("b", _generic, default_value=True)])))
        self.first.append(Function("foo", Visibility.public, _generic,
                                Signature([Parameter("a", _generic)])))
        # TODO: What bump is this?

if __name__ == "__main__":
    unittest.main()
