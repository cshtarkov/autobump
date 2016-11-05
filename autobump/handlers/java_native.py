"""Convert a Java codebase into a list of Units, using introspection utilities written in Java."""
import os
import logging
import subprocess
from subprocess import PIPE
from xml.etree import ElementTree
from autobump import common

logger = logging.getLogger(__name__)
libexec = os.path.join(os.path.dirname(__file__), "..", "libexec")

# Set of files to exclude
_excluded_files = [
]

_excluded_dirs = [
]


# Type system
class _JavaNativeType(common.Type):
    """Representation of a Java type.

    When checking for compatibility with another type,
    an external utility will be invoked to perform introspection
    and find out if Java considers two types to be compatible."""
    def __init__(self, name):
        self.name = name

    def is_compatible(self, other):
        assert type(self) is type(other), "Should never happen: comparing a _JavaNativeType to something else."
        assert hasattr(self, "location") and self.location is not None, "Should never happen: location should be set prior to calling is_compatible"
        return _run_type_compatibility_checker(self.location, self.name, other.name)

    def __eq__(self, other):
        return self.name == other.name


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
    child = subprocess.Popen(["java"] + [utility] + args, cwd=libexec, stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = child.communicate()
    if child.returncode != 0:
        raise JavaUtilityException(stderr_data.decode("ascii").strip())
    return stdout_data.decode("ascii").strip()


def _xml_element_to_unit(elt):
    """Convert an XML <class> element into a Unit."""
    functions = dict()
    fields = dict()
    units = dict()
    for child in elt:
        if child.tag == "field":
            field = common.Field(child.attrib["name"], child.attrib["type"])
            fields[field.name] = field
        elif child.tag == "method":
            signature_elt = child.find("signature")
            parameter_elts = signature_elt.findall("parameter")
            parameters = [common.Parameter(p.attrib["name"], _JavaNativeType(p.attrib["type"])) for p in parameter_elts]
            signature = common.Signature(parameters)
            if child.attrib["name"] in functions:
                functions[child.attrib["name"]].signatures.append(signature)
            else:
                function = common.Function(child.attrib["name"], child.attrib["returns"], [signature])
                functions[function.name] = function
        elif child.tag == "class":
            unit = _xml_element_to_unit(child)
            units[unit.name] = unit
    return common.Unit(elt.attrib["name"], fields, functions, units)


def java_codebase_to_units(location, build_instruction, build_root):
    """Convert a Java codebase found at 'location' into a list of units.

    Works by compiling it with 'build_instruction' and then inspecting the
    class files under 'location/build_root'."""
    # Compile the classes
    try:
        subprocess.run(build_instruction, cwd=location, shell=True, check=True, stdout=PIPE)
    except subprocess.CalledProcessError:
        logger.error("Failed to call {}".format(build_instruction))
        exit(1)

    # Get absolute path to build root
    build_root = os.path.join(location, build_root)

    # Get a list of fully-qualified class names
    fqns = []
    for root, dirs, files in os.walk(build_root):
        dirs[:] = [d for d in dirs if not any(r.match(d) for r in _excluded_dirs)]
        classfiles = [f for f in files if f.endswith(".class") and not any(r.match(f) for r in _excluded_files)]
        prefix = root[len(build_root):].replace(os.sep, ".")
        # TODO: Hack.
        if len(prefix) > 0 and prefix[0] == ".":
            prefix = prefix[1:]
        fqns = fqns + [prefix + "." + os.path.splitext(n)[0] for n in classfiles]

    # Convert the XML representation of these classes to common.Unit
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
