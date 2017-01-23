import java.net.URL;
import java.net.URLClassLoader;
import java.net.MalformedURLException;

import java.io.File;

/**
 *
 * Utility program that checks the compatibility of two Java classes
 * (or interfaces). Compatibility is defined in the same way as autobump
 * defines it:
 *
 *           A is compatible with B <=> A can be substituted by B
 *
 * Usage: java TypeCompatibilityChecker [build-location] [superclass] [subclass]
 *   where [build-location] is a path to a directory where the tree of Java classes resides.
 *         [superclass] is the fully-qualified name of type A.
 *         [subclass] is the fully-qualified name of type B.
 *
 * This program is invoked by autobump's Java handler to assist with
 * checking the compatibility of types, e.g. when the type of a parameter to a method
 * has changed, but autobump is not sure whether that's a breaking change.
 *
 */
public class TypeCompatibilityChecker {

    private static void abort(String message, int status) {
        System.err.println("TypeCompatibilityChecker: " + message);
        System.exit(status);
    }

    private static void abort(String message) {
        abort(message, 1);
    }

    /**
     * Find a class by its name, potentially using a ClassLoader if it's not a primitive type.
     */
    private static Class findClass(String className, ClassLoader loader) throws ClassNotFoundException {
        switch(className) {
        case "void": return void.class;
        case "boolean": return boolean.class;
        case "byte": return byte.class;
        case "char": return char.class;
        case "double": return double.class;
        case "float": return float.class;
        case "int": return int.class;
        case "long": return long.class;
        case "short": return short.class;
        default: return loader.loadClass(className);
        }
    }

    private static ClassLoader instantiateClassLoader(String bin) throws MalformedURLException {
        URL url = new URL("file://" + bin + File.separator);
        URL[] urls = new URL[] {url};
        ClassLoader loader = new URLClassLoader(urls);
        return loader;
    }

    public static void main(String[] args) {

        // Validate and parse parameters
        if (args.length < 3) {
            abort("Invalid number of arguments: expected [build-location] [superclass] [subclass]");
        }

        ClassLoader loader = null;
        Class superclass = null;
        Class subclass = null;
        try {
            // Constructing the ClassLoader and the subclass should never fail.
            loader = instantiateClassLoader(args[0]);
            superclass = findClass(args[1], loader);
            subclass = findClass(args[2], loader);
        } catch(MalformedURLException ex) {
            abort(String.format("%s is not a valid location", args[0]));
        } catch(ClassNotFoundException ex) {
            System.out.println("false");
            System.exit(0);
        }

        // Check type compatibility
        if (superclass.isAssignableFrom(subclass)) {
            System.out.println("true");
        } else {
            System.out.println("false");
        }
    }

}
