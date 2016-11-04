import os
import tempfile
import unittest
import subprocess
from subprocess import PIPE
from autobump.handlers import java
from autobump.handlers import java_native


def _run_javac(sources):
    """Helper method to run the Java compiler on a list of source files."""
    class JavaCompilerException(Exception):
        pass
    child = subprocess.Popen(["javac"] + sources, stdout=PIPE, stderr=PIPE)
    child.communicate()
    if child.returncode != 0:
        raise JavaCompilerException("Compiing a list of sources failed!")


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

        self.dir_handle = tempfile.TemporaryDirectory()
        self.dir = self.dir_handle.name
        # Write the above class definitions to source files.
        files = []
        for filename, source in sources:
            fullpath = os.path.join(self.dir, filename)
            files.append(fullpath)
            os.makedirs(os.path.dirname(fullpath), exist_ok=True)
            with open(fullpath, "w") as f:
                f.write(source)

        # Now compile everything.
        _run_javac(files)

        # Get two codebases for the two different handlers.
        self.codebase = java.codebase_to_units(self.dir)
        self.codebase_native = java_native.codebase_to_units(self.dir)

    def tearDown(self):
        self.dir_handle.cleanup()


class TestClasses(TestJavaHandlerBase):

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


class TestClassesNative(TestClasses):

    def setUp(self):
        super(TestClassesNative, self).setUp()
        self.codebase = self.codebase_native

    def test_inner_class(self):
        self.assertTrue("packageY.ClassC$Inner" in self.codebase["packageY.ClassC"].units)


class TestMethodOverloading(TestJavaHandlerBase):

    def test_overloading_possible(self):
        self.assertEqual(len(self.codebase["packageY.ClassC"].functions["overloaded"].signatures), 3)

    def test_additional_parameter(self):
        function = self.codebase["packageY.ClassC"].functions["overloaded"]
        self.assertTrue(any(len(sig.parameters) == 2 and sig.parameters[1].type.name == "packageX.ClassA" for sig in function.signatures))

    def test_parameter_different_type(self):
        function = self.codebase["packageY.ClassC"].functions["overloaded"]
        self.assertTrue(any(len(sig.parameters) == 2 and sig.parameters[1].type.name == "packageX.ClassB" for sig in function.signatures))


class TestMethodOverloadingNative(TestMethodOverloading):

    def setUp(self):
        super(TestMethodOverloadingNative, self).setUp()
        self.codebase = self.codebase_native


class TestTypes(TestJavaHandlerBase):

    def test_superclass_compatible_with_subclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassC"].signatures[0].parameters[0].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_subclass_not_compatible_with_superclass(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassC"].signatures[0].parameters[0].type
        self.assertFalse(subclass.is_compatible(superclass))

    def test_superclass_compatible_with_subclass_skip_one(self):
        superclass = self.codebase["packageY.ClassD"].functions["acceptsClassA"].signatures[0].parameters[0].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertTrue(superclass.is_compatible(subclass))

    def test_interface_compatible_with_class(self):
        interface = self.codebase["packageY.ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[0].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertTrue(interface.is_compatible(subclass))

    def test_class_not_compatible_with_interface(self):
        interface = self.codebase["packageY.ClassD"].functions["acceptsIfaceD"].signatures[0].parameters[0].type
        subclass = self.codebase["packageY.ClassD"].functions["acceptsClassD"].signatures[0].parameters[0].type
        self.assertFalse(subclass.is_compatible(interface))


class TestTypesNative(TestTypes):

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
