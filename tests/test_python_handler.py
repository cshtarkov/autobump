import ast
import unittest
from autobump.handlers import python


def _source_to_units(source):
    """Helper function to convert Python source code into a list
    of Units."""
    return python._container_to_unit("", ast.parse(source))


class TestVisibility(unittest.TestCase):
    """Test how the Python handler detects visibility
    just by the name of the entity."""

    def test_public_name(self):
        name = "public"
        self.assertTrue(python._is_public(name))

    def test_private_name(self):
        name = "_private"
        self.assertFalse(python._is_public(name))


class TestSignature(unittest.TestCase):
    """Test how the Python handler interprets function signatures."""

    def test_no_parameters(self):
        source = """
def f():
    pass
        """
        units = _source_to_units(source)
        self.assertEqual(len(units.functions[0].signature.parameters), 0)

    def test_parameter_correct_count(self):
        source = """
def f(p1, p2):
    pass
        """
        units = _source_to_units(source)
        self.assertEqual(len(units.functions[0].signature.parameters), 2)

    def test_parameter_names(self):
        source = """
def f(p1, p2):
    pass
        """
        units = _source_to_units(source)
        parameters = units.functions[0].signature.parameters
        self.assertEqual(parameters[0].name, "p1")
        self.assertEqual(parameters[1].name, "p2")

    def test_parameter_defaults(self):
        source = """
def f(p1, p2, p3=True, p4=False):
    pass
        """
        units = _source_to_units(source)
        parameters = units.functions[0].signature.parameters
        self.assertEqual(parameters[0].default_value, None)
        self.assertEqual(parameters[1].default_value, None)
        self.assertEqual(parameters[2].default_value, True)
        self.assertEqual(parameters[3].default_value, False)


class TestClassConversion(unittest.TestCase):
    """Test how the Python handlers converts class
    definitions into a Unit."""

    def test_empty_class(self):
        source = """
class c(object):
    pass
        """
        units = _source_to_units(source)
        unit = units.units[0]
        self.assertEqual(len(unit.fields), 0)
        self.assertEqual(len(unit.functions), 0)
        self.assertEqual(len(unit.units), 0)

    def test_class_with_fields_same_value(self):
        source = """
class c(object):
    f1 = None
    f2 = None
        """
        units = _source_to_units(source)
        unit = units.units[0]
        self.assertEqual(len([f for f in unit.fields if f.name == "f1"]), 1)
        self.assertEqual(len([f for f in unit.fields if f.name == "f2"]), 1)

    def test_class_with_fields_being_class_defs(self):
        source = """
class a(object):
    pass

class c(object):
    f1 = a
    f2 = a
        """
        units = _source_to_units(source)
        unit = units.units[1]
        self.assertEqual(len([f for f in unit.fields if f.name == "f1"]), 1)
        self.assertEqual(len([f for f in unit.fields if f.name == "f2"]), 1)

    def test_class_with_fields_different_value(self):
        source = """
class c(object):
    f1 = "value1"
    f2 = "value2"
        """
        units = _source_to_units(source)
        unit = units.units[0]
        self.assertEqual(len([f for f in unit.fields if f.name == "f1"]), 1)
        self.assertEqual(len([f for f in unit.fields if f.name == "f2"]), 1)

    def test_class_with_methods(self):
        source = """
class c(object):
    def m1():
        pass

    def m2(p1):
        pass
        """
        units = _source_to_units(source)
        unit = units.units[0]
        self.assertEqual(len([m for m in unit.functions if m.name == "m1"]), 1)
        self.assertEqual(len([m for m in unit.functions if m.name == "m2"]), 1)

    def test_class_with_inner_class(self):
        source = """
class c(object):
    class inner(object):
        pass
    pass
        """
        units = _source_to_units(source)
        unit = units.units[0]
        self.assertEqual(len([u for u in unit.units if u.name == "inner"]), 1)

if __name__ == "__main__":
    unittest.main()
