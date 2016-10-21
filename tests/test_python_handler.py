import ast
import unittest
from autobump.handlers import python


def _source_to_unit(source):
    """Helper function to convert Python source code into a single Unit."""
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
        codebase = _source_to_unit(source)
        self.assertEqual(len(codebase.functions[0].signature.parameters), 0)

    def test_parameter_correct_count(self):
        source = """
def f(p1, p2):
    pass
        """
        codebase = _source_to_unit(source)
        self.assertEqual(len(codebase.functions[0].signature.parameters), 2)

    def test_parameter_names(self):
        source = """
def f(p1, p2):
    pass
        """
        codebase = _source_to_unit(source)
        parameters = codebase.functions[0].signature.parameters
        self.assertEqual(parameters[0].name, "p1")
        self.assertEqual(parameters[1].name, "p2")

    def test_parameter_defaults(self):
        source = """
def f(p1, p2, p3=True, p4=False):
    pass
        """
        codebase = _source_to_unit(source)
        parameters = codebase.functions[0].signature.parameters
        self.assertEqual(parameters[0].default_value, None)
        self.assertEqual(parameters[1].default_value, None)
        self.assertEqual(parameters[2].default_value, True)
        self.assertEqual(parameters[3].default_value, False)

    def test_parameter_default_none(self):
        source = """
def f(p1, p2=None, p3=True):
    pass
"""
        codebase = _source_to_unit(source)
        parameters = codebase.functions[0].signature.parameters
        self.assertEqual(parameters[0].default_value, None)
        self.assertNotEqual(parameters[1].default_value, None)
        self.assertEqual(parameters[2].default_value, True)


class TestClassConversion(unittest.TestCase):
    """Test how the Python handlers converts class
    definitions into a Unit."""

    def test_empty_class(self):
        source = """
class c(object):
    pass
        """
        codebase = _source_to_unit(source)
        unit = codebase.units[0]
        self.assertEqual(len(unit.fields), 0)
        self.assertEqual(len(unit.functions), 0)
        self.assertEqual(len(unit.units), 0)

    def test_class_with_fields_same_value(self):
        source = """
class c(object):
    f1 = None
    f2 = None
        """
        codebase = _source_to_unit(source)
        unit = codebase.units[0]
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
        codebase = _source_to_unit(source)
        unit = codebase.units[1]
        self.assertEqual(len([f for f in unit.fields if f.name == "f1"]), 1)
        self.assertEqual(len([f for f in unit.fields if f.name == "f2"]), 1)

    def test_class_with_fields_different_value(self):
        source = """
class c(object):
    f1 = "value1"
    f2 = "value2"
        """
        codebase = _source_to_unit(source)
        unit = codebase.units[0]
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
        codebase = _source_to_unit(source)
        unit = codebase.units[0]
        self.assertEqual(len([m for m in unit.functions if m.name == "m1"]), 1)
        self.assertEqual(len([m for m in unit.functions if m.name == "m2"]), 1)

    def test_class_with_inner_class(self):
        source = """
class c(object):
    class inner(object):
        pass
    pass
        """
        codebase = _source_to_unit(source)
        unit = codebase.units[0]
        self.assertEqual(len([u for u in unit.units if u.name == "inner"]), 1)


class TestTypeOfParameters(unittest.TestCase):
    """Test how types of parameters are determined."""

    def test_same_type(self):
        source = """
def func(a, b):
    a.m1()
    b.m1()
        """
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertEqual(type_of_a, type_of_b)

    def test_compatible_types_methods(self):
        source = """
def func(a, b):
    a.m1()
    b.m1()
    b.m2()
        """
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertTrue(type_of_a.is_compatible(type_of_b))

    def test_incompatible_types_methods(self):
        source = """
def func(a, b):
    a.m1()
    b.m1()
    b.m2()
        """
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertFalse(type_of_b.is_compatible(type_of_a))

    def test_compatible_types_fields(self):
        source = """
def func(a, b):
    a.f1 = 1
    a.f2 = 1
    b.f1 = 1
        """
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertTrue(type_of_b.is_compatible(type_of_a))

    def test_incompatible_types_fields(self):
        source = """
def func(a, b):
    a.f1 = 1
    b.f1 = 1
    b.f2 = 1
        """
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertFalse(type_of_b.is_compatible(type_of_a))

    def test_inner_uses_of_samename_variable(self):
        source = """
def func(a, b):
    a.m1()
    b.m1()
    class inner_class(object):
        def __init__(self, a):
            a.m2()
    def inner_func(b):
        b.m3()
"""
        codebase = _source_to_unit(source)
        function = codebase.functions[0]
        type_of_a = function.signature.parameters[0].type
        type_of_b = function.signature.parameters[1].type
        self.assertEqual(type_of_a, type_of_b)

if __name__ == "__main__":
    unittest.main()
