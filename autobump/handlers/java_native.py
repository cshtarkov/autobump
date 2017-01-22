"""Convert a Java codebase into a list of Units, using introspection utilities written in Java."""
import os
import re
import sys
import logging
import subprocess
from subprocess import PIPE
from xml.etree import ElementTree

from autobump import config
from autobump.capir import Type, Field, Parameter, Signature, Function, Unit

logger = logging.getLogger(__name__)
libexec = os.path.join(os.path.dirname(__file__), "..", "libexec")

# Set of files to exclude
_excluded_files = [
    re.compile("^package\-info\.java$")
]

_excluded_dirs = [
    re.compile("^[Tt]ests?$")
]


# Type system
class _JavaNativeType(Type):
    """Representation of a Java type.

    When checking for compatibility with another type,
    an external utility will be invoked to perform introspection
    and find out if Java considers two types to be compatible."""
    def __init__(self, name):
        self.name = name

    def _array_nesting(self):
        """Return the amount of nesting in an array declaration.
        E.g. int[][] is 2, int[] is 1.
        Declaration of ordinary variables have an array nesting of 0."""
        nesting = 0
        for nesting in range(len(self.name)):
            if self.name[nesting] != '[':
                break
        return nesting

    def _strip_nesting(self):
        """Return the type of the array declaration."""
        nesting = self._array_nesting()
        if nesting == 0:
            return self.name
        encoding = self.name[nesting]
        if encoding == "L":
            # Encodes a class name.
            return self.name[nesting + 1:]
        encoding_map = {
            "Z": "boolean",
            "B": "byte",
            "C": "char",
            "D": "double",
            "F": "float",
            "I": "int",
            "J": "long",
            "S": "short"
        }
        return encoding_map[encoding]

    def is_compatible(self, other):
        assert type(self) is type(other), "Should never happen: comparing a _JavaNativeType to something else."
        assert hasattr(self, "location") and self.location is not None, "Should never happen: location should be set prior to calling is_compatible"
        # The two have different nesting - e.g. one is an array, the other one isn't.
        if self._array_nesting() != other._array_nesting():
            return False

        if config.java_lazy_type_checking():
            return self.name == other.name
        else:
            return _run_type_compatibility_checker(self.location, self._strip_nesting(), other._strip_nesting())

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<JavaNativeType {}>".format(self.name)

    def __hash__(self):
        return hash(self.name)


_dummyType = _JavaNativeType("dummy")
_dummyType.is_compatible = lambda t: True


class JavaUtilityException(Exception):
    pass


def _run_inspector(location, classnames):
    """Run the Inspector program to get the XML representation
    of classes found in 'location'."""
    return _run_utility("Inspector", [location] + classnames)


def _run_type_compatibility_checker(location, superclass, subclass):
    """Run the TypeCompatibilityChecker program and return a boolean
    indicating whether 'superclass' can really be substituted with 'subclass'."""
    output = _run_utility("TypeCompatibilityChecker", [location, superclass, subclass])
    return output == "true"


def _run_utility(utility, args):
    """Run a Java utility program with arguments."""
    javafile = os.path.join(libexec, utility + ".java")
    classfile = os.path.join(libexec, utility + ".class")
    if os.path.isfile(javafile) and not os.path.isfile(classfile):
        # This is a valid utility, but it's not been compiled.
        logger.error("{} has not been compiled!".format(utility))
        exit(1)
    child = subprocess.Popen([config.java()] + [utility] + args, cwd=libexec, stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = child.communicate()
    if child.returncode != 0:
        raise JavaUtilityException(stderr_data.decode("ascii").strip())
    return stdout_data.decode("ascii").strip()


def _xml_element_to_field(elt):
    """Convert an XML <field> into a Field."""
    assert elt.tag == "field"
    return Field(elt.attrib["name"], _JavaNativeType(elt.attrib["type"]))


def _xml_get_signature_of_method(elt):
    """Convert all <signature>s of a <method> into a Signature."""
    assert elt.tag == "method"
    signature_elt = elt.find("signature")
    parameter_elts = signature_elt.findall("parameter")
    parameters = [Parameter(p.attrib["name"], _JavaNativeType(p.attrib["type"]))
                  for p in parameter_elts]
    return_type = Parameter("$AUTOBUMP_RETURN$", _JavaNativeType(elt.attrib["returns"]))
    parameters = [return_type] + parameters
    return Signature(parameters)


def _xml_element_to_unit(elt):
    """Convert an XML <class> element into a Unit."""
    functions = dict()
    fields = dict()
    units = dict()
    for child in elt:
        if child.tag == "field":
            field = _xml_element_to_field(child)
            fields[field.name] = field
        elif child.tag == "method":
            signature = _xml_get_signature_of_method(child)
            if child.attrib["name"] in functions:
                functions[child.attrib["name"]].signatures.append(signature)
            else:
                function = Function(child.attrib["name"], _dummyType, [signature])
                functions[function.name] = function
        elif child.tag == "class":
            unit = _xml_element_to_unit(child)
            units[unit.name] = unit
    return Unit(elt.attrib["name"], fields, functions, units)


def java_codebase_to_units(location, build_command, build_root):
    """Convert a Java codebase found at 'location' into a list of units.

    Works by compiling it with 'build_command' and then inspecting the
    class files under 'location/build_root'."""
    # Compile the classes
    logger.info("Starting build process")
    if "CLASSPATH" in os.environ:
        logger.debug("CLASSPATH variable set")
    if config.classpath() != "":
        logger.debug("java_native/classpath set, using that as classpath")
        os.environ["CLASSPATH"] = config.classpath()
    if "CLASSPATH" not in os.environ:
        logger.warning("No CLASSPATH set")
    try:
        subprocess.run(build_command,
                       cwd=location,
                       shell=True,
                       check=True,
                       stdout=sys.stderr,
                       stderr=sys.stderr)
    except subprocess.CalledProcessError:
        logger.error("Failed to call {}".format(build_command))
        exit(1)
    logger.info("Build completed")

    # Get absolute path to build root
    build_root = os.path.join(location, build_root)
    logger.debug("Absolute build root is {}".format(build_root))

    # Get a list of fully-qualified class names
    fqns = []
    for root, dirs, files in os.walk(build_root):
        dirs[:] = [d for d in dirs if not any(r.search(d) for r in _excluded_dirs)]
        classfiles = [f for f in files if f.endswith(".class") and not any(r.search(f) for r in _excluded_files)]
        prefix = root[len(build_root):].replace(os.sep, ".")
        if len(prefix) > 0 and prefix[0] == ".":
            prefix = prefix[1:]
        fqns = fqns + [((prefix + ".") if prefix != "" else "") + os.path.splitext(n)[0] for n in classfiles]
    logger.debug("{} classes identified".format(len(fqns)))

    # Convert the XML representation of these classes to Unit
    xml = _run_inspector(build_root, fqns)
    root = ElementTree.fromstring(xml)
    units = dict()
    for child in root:
        # TODO: Validation of the XML shouldn't be done using assertions.
        # Is validation even necessary in this case?
        assert child.tag == "class", "Found element in XML that's not <class>!"
        unit = _xml_element_to_unit(child)
        units[unit.name] = unit
    return units

build_required = True
codebase_to_units = java_codebase_to_units
