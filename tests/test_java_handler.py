import os
import tempfile
import unittest
from autobump.handlers import java


class TestJavaHandlerBase(unittest.TestCase):
    """Used to set up a simple Java codebase in a temporary
    location.

    Does not contain any actual tests. Test cases
    are meant to inherit from this class so that they
    all have a non-trivial fixture."""
    def setUp(self):

        sources = [
            ("packageX/ClassA.java",
            """
            package packageX;

            public class ClassA {
                public void returnsVoid() {}
                public ClassB returnsB(ClassB b) { return b; }
                private void privateReturnsVoid() {}
            }
            """),

            ("packageX/ClassB.java",
            """
            package packageX;

            public class ClassB {
                private static final int ONE = 1;
                public static final int FIVE = 5;
                public ClassA returnsB(ClassA b) { return b; }
            }
            """),

            ("packageY/ClassC.java",
            """
            package packageY;
            import packageX.ClassA;
            import packageX.ClassB;

            public class ClassC extends ClassA {
                public void overloaded(int a) {}
                public void overloaded(int a, ClassA b) {}
                public void overloaded(int a, ClassB b) {}
                public class Inner {
                }
            }
            """),

            ("packageY/InterfaceD.java",
            """
            package packageY;

            public interface InterfaceD {
                public static final boolean INTERFACE_D = true;
            }
            """),

            ("packageY/ClassD.java",
            """
            package packageY;
            import packageX.ClassA;

            public class ClassD extends ClassC implements InterfaceD {
                public static void acceptsClassD(ClassD p) {}
                public static void acceptsIfaceD(InterfaceD p) {}
                public static void acceptsClassA(ClassA p) {}
                public static void acceptsClassC(ClassC p) {}
            }
            """)
        ]

        with tempfile.TemporaryDirectory() as dir:
            for filename, source in sources:
                fullpath = os.path.join(dir, filename)
                os.makedirs(os.path.dirname(fullpath), exist_ok=True)
                with open(fullpath, "w") as f:
                    f.write(source)
            self.codebase = java.codebase_to_units(dir)


class TestClasses(TestJavaHandlerBase):

    def test_class_names(self):
        self.assertTrue("ClassA" in self.codebase)
        self.assertTrue("ClassB" in self.codebase)
        self.assertTrue("ClassC" in self.codebase)
        self.assertTrue("InterfaceD" in self.codebase)
        self.assertTrue("ClassD" in self.codebase)

    def test_class_functions(self):
        self.assertTrue("returnsVoid" in self.codebase["ClassA"].functions)
        self.assertFalse("privateReturnsVoid" in self.codebase["ClassA"].functions)

    def test_class_fields(self):
        self.assertTrue("FIVE" in self.codebase["ClassB"].fields)
        self.assertFalse("ONE" in self.codebase["ClassB"].fields)

    def test_inner_class(self):
        self.assertTrue("Inner" in self.codebase["ClassC"].units)


class TestMethodOverloading(TestJavaHandlerBase):

    def test_overloading_possible(self):
        self.assertEqual(len(self.codebase["ClassC"].functions["overloaded"].signatures), 3)

    def test_additional_parameter(self):
        signature = self.codebase["ClassC"].functions["overloaded"].signatures[1]
        self.assertEqual(signature.parameters[1].type.name, "packageX.ClassA")

    def test_parameter_different_type(self):
        signature = self.codebase["ClassC"].functions["overloaded"].signatures[2]
        self.assertEqual(signature.parameters[1].type.name, "packageX.ClassB")


class TestTypes(TestJavaHandlerBase):

    def test_superclass_compatible_with_subclass(self):
        superclass = self.codebase["ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["ClassD"].functions["acceptsClassC"].signatures[0].parameters[0].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_subclass_not_compatible_with_superclass(self):
        superclass = self.codebase["ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["ClassD"].functions["acceptsClassC"].signatures[0].parameters[0].type
        self.assertFalse(subclass.is_compatible(superclass))

    def test_superclass_compatible_with_subclass_skip_one(self):
        superclass = self.codebase["ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_interface_compatible_with_class(self):
        interface = self.codebase["ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[0].type
        subclass = self.codebase["ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertTrue(interface.is_compatible(subclass))

    def test_class_not_compatible_with_interface(self):
        interface = self.codebase["ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[0].type
        subclass = self.codebase["ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertFalse(subclass.is_compatible(interface))

if __name__ == "__main__":
    unittest.main()