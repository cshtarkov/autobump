import unittest
from autobump.core import Bump, compare_codebases
from autobump.common import Visibility, Field, Parameter, Function, Unit


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
        self.first.append(Field("foo", Visibility.public))
        self.second.append(Field("foo", Visibility.unit))
        self.expect(Bump.major)

    def test_increase_visibility_of_field(self):
        self.first.append(Field("foo", Visibility.unit))
        self.second.append(Field("foo", Visibility.public))
        self.expect(Bump.minor)

    def test_add_nonvisibile_field(self):
        self.second.append(Field("foo", Visibility.unit))
        self.expect(Bump.patch)

    def test_add_visible_field(self):
        self.second.append(Field("foo", Visibility.public))
        self.expect(Bump.minor)

    def test_remove_nonvisible_field(self):
        self.first.append(Field("foo", Visibility.unit))
        self.expect(Bump.patch)

    def test_remove_visible_field(self):
        self.first.append(Field("foo", Visibility.public))
        self.expect(Bump.major)

    def test_change_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, default_value=1))
        self.second.append(Field("foo", Visibility.public, default_value=2))
        # TODO: What bump is this?

    def test_remove_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, default_value=1))
        self.second.append(Field("foo", Visibility.public, default_value=None))
        self.expect(Bump.major)

    def test_add_visible_field_default_value(self):
        self.first.append(Field("foo", Visibility.public, default_value=None))
        self.second.append(Field("foo", Visibility.public, default_value=1))
        # TODO: What bump is this?

    def test_change_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, default_value=1))
        self.second.append(Field("foo", Visibility.unit, default_value=2))
        self.expect(Bump.patch)

    def test_remove_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, default_value=1))
        self.second.append(Field("foo", Visibility.unit, default_value=None))
        self.expect(Bump.patch)

    def test_add_nonvisible_field_default_value(self):
        self.first.append(Field("foo", Visibility.unit, default_value=None))
        self.second.append(Field("foo", Visibility.unit, default_value=1))
        self.expect(Bump.patch)

    # Parameters to functions.

    def test_add_parameter(self):
        self.second.append(Parameter("foo"))
        self.expect(Bump.major)

    def test_add_parameter_with_default_value(self):
        self.second.append(Parameter("foo"))
        # TODO: What bump is this?

    def test_remove_parameter(self):
        self.first.append(Parameter("foo"))
        self.expect(Bump.major)

    def test_remove_parameter_with_default_value(self):
        self.first.append(Parameter("foo", default_value=1))
        self.expect(Bump.major)

    def test_give_parameter_default_value(self):
        self.first.append(Parameter("foo"))
        self.second.append(Parameter("foo", default_value=1))
        self.expect(Bump.patch)

    def test_take_away_parameter_default_value(self):
        self.first.append(Parameter("foo", default_value=1))
        self.second.append(Parameter("foo"))
        self.expect(Bump.major)

    # Functions.

    def test_reduce_visibility_of_function(self):
        self.first.append(Function("foo", Visibility.public))
        self.second.append(Function("foo", Visibility.unit))
        self.expect(Bump.major)

    def test_increase_visibility_of_function(self):
        self.first.append(Function("foo", Visibility.unit))
        self.second.append(Function("foo", Visibility.public))
        self.expect(Bump.minor)

    def test_add_nonvisibile_function(self):
        self.second.append(Function("foo", Visibility.unit))
        self.expect(Bump.patch)

    def test_add_visible_function(self):
        self.second.append(Function("foo", Visibility.public))
        self.expect(Bump.minor)

    def test_remove_nonvisible_function(self):
        self.first.append(Function("foo", Visibility.unit))
        self.expect(Bump.patch)

    def test_remove_visible_function(self):
        self.first.append(Function("foo", Visibility.public))
        self.expect(Bump.major)


if __name__ == "__main__":
    unittest.main()
