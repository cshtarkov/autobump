import os
import tempfile
import unittest

from autobump.handlers import java_ast
from autobump.handlers import java_native


class TestJavaHandlerBase(unittest.TestCase):
    """Used to set up a simple Java codebase in a temporary
    location.

    Does not contain any actual tests. Test cases
    are meant to inherit from this class so that they
    all have a non-trivial fixture."""
    @classmethod
    def setUpClass(cls):

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

            ("packageY/InterfaceE.java",
            """
            package packageY;

            public interface InterfaceE {
            }
            """),

            ("packageY/InterfaceX.java",
             """
             package packageY;

             public interface InterfaceX extends InterfaceD, InterfaceE {
             }
             """),

            ("packageY/ClassD.java",
            """
            package packageY;
            import packageX.ClassA;

            public class ClassD extends ClassC implements InterfaceD {
                public static void acceptsClassD(ClassD p) {}
                public static void acceptsIfaceD(InterfaceD p) {}
                public static void acceptsIfaceE(InterfaceE p) {}
                public static void acceptsIfaceX(InterfaceX p) {}
                public static void acceptsClassA(ClassA p) {}
                public static void acceptsClassC(ClassC p) {}
                public static void acceptsArrayClassC(ClassC[] p) {}
                public static void acceptsArrayClassA(ClassA[] p) {}
            }
            """)

        ]

        cls.dir_handle = tempfile.TemporaryDirectory()
        cls.dir = cls.dir_handle.name
        # Write the above class definitions to source files.
        files = []
        for filename, source in sources:
            fullpath = os.path.join(cls.dir, filename)
            files.append(fullpath)
            os.makedirs(os.path.dirname(fullpath), exist_ok=True)
            with open(fullpath, "w") as f:
                f.write(source)

        # Get two codebases for the two different handlers.
        cls.codebase_ast = java_ast.codebase_to_units(cls.dir)
        cls.codebase_native = java_native.codebase_to_units(cls.dir, 'javac `find -name "*.java" | xargs`', '.')

        # By default, run the java_ast handler tests.
        # The java_native handler will need to override setUp()
        # and reassign cls.codebase.
        cls.codebase = cls.codebase_ast

    @classmethod
    def tearDownClass(cls):
        cls.dir_handle.cleanup()

    def setUp(self):
        self.codebase = self.__class__.codebase
        self.codebase_ast = self.__class__.codebase_ast


class TestClassesAST(TestJavaHandlerBase):

    def test_class_names(self):
        self.assertTrue("packageX.ClassA" in self.codebase)
        self.assertTrue("packageX.ClassB" in self.codebase)
        self.assertTrue("packageY.ClassC" in self.codebase)
        self.assertTrue("packageY.InterfaceD" in self.codebase)
        self.assertTrue("packageY.ClassD" in self.codebase)

    def test_class_functions(self):
        self.assertTrue("returnsVoid" in self.codebase["packageX.ClassA"].functions)
        self.assertFalse("privateReturnsVoid" in self.codebase["packageX.ClassA"].functions)

    def test_class_fields(self):
        self.assertTrue("FIVE" in self.codebase["packageX.ClassB"].fields)
        self.assertFalse("ONE" in self.codebase["packageX.ClassB"].fields)

    def test_inner_class(self):
        self.assertTrue("Inner" in self.codebase["packageY.ClassC"].units)


class TestClassesNative(TestClassesAST):

    def setUp(self):
        super(TestClassesNative, self).setUp()
        self.codebase = self.codebase_native

    # java_ast and java_native disagree on what inner classes should be called,
    # so we need to override this test.
    def test_inner_class(self):
        self.assertTrue("packageY.ClassC$Inner" in self.codebase["packageY.ClassC"].units)


class TestMethodOverloadingAST(TestJavaHandlerBase):

    def test_overloading_possible(self):
        self.assertEqual(len(self.codebase["packageY.ClassC"].functions["overloaded"].signatures), 3)

    def test_additional_parameter(self):
        function = self.codebase["packageY.ClassC"].functions["overloaded"]
        self.assertTrue(any(len(sig.parameters) == 3 and sig.parameters[2].type.name == "packageX.ClassA" for sig in function.signatures))

    def test_parameter_different_type(self):
        function = self.codebase["packageY.ClassC"].functions["overloaded"]
        self.assertTrue(any(len(sig.parameters) == 3 and sig.parameters[2].type.name == "packageX.ClassB" for sig in function.signatures))


class TestMethodOverloadingNative(TestMethodOverloadingAST):

    def setUp(self):
        super(TestMethodOverloadingNative, self).setUp()
        self.codebase = self.codebase_native


class TestTypesAST(TestJavaHandlerBase):

    def test_type_and_array_of_type_are_different(self):
        t = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[1].type
        arrayT = self.codebase["packageY.ClassD"].functions["acceptsArrayClassA"].signatures[0].parameters[1].type
        self.assertFalse(t.is_compatible(arrayT))
        self.assertFalse(arrayT.is_compatible(t))

    def test_superclass_compatible_with_subclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassC"].signatures[0].parameters[1].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_superclass_array_compatible_with_subclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsArrayClassA"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsArrayClassC"].signatures[0].parameters[1].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_subclass_not_compatible_with_superclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassC"].signatures[0].parameters[1].type
        self.assertFalse(subclass.is_compatible(superclass))

    def test_subclass_array_not_compatible_with_superclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsArrayClassA"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsArrayClassC"].signatures[0].parameters[1].type
        self.assertFalse(subclass.is_compatible(superclass))

    def test_superclass_compatible_with_subclass_skip_one(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[1].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_interface_compatible_with_class(self):
        interface = self.codebase["packageY.ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[1].type
        self.assertTrue(interface.is_compatible(subclass))

    def test_class_not_compatible_with_interface(self):
        interface = self.codebase["packageY.ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[1].type
        self.assertFalse(subclass.is_compatible(interface))

    def test_interface_extension(self):
        interface1 = self.codebase["packageY.ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[1].type
        interface2 = self.codebase["packageY.ClassD"].functions["acceptsIfaceE"].signatures[0].parameters[1].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsIfaceX"].signatures[0].parameters[1].type
        self.assertTrue(interface1.is_compatible(subclass))
        self.assertTrue(interface2.is_compatible(subclass))


class TestTypesNative(TestTypesAST):

    def setUp(self):
        super(TestTypesNative, self).setUp()
        self.codebase = self.codebase_native
        # Need to patch the 'location' of every type - i.e.
        # where TypeCompatibilityChecker will try to find the
        # class files.
        for function in self.codebase["packageY.ClassD"].functions.values():
            for signature in function.signatures:
                for parameter in signature.parameters:
                    parameter.type.location = self.dir


if __name__ == "__main__":
    unittest.main()
