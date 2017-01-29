# Copyright 2016-2017 Christian Shtarkov
#
# This file is part of Autobump.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
"""
Convert a Java codebase into a list of Units, using introspection utilities written in Java.

This handler needs too additional Java utilities (found under 'libexec/') that do reflection
on compiled Java code.
"""

import os
import sys
import shutil
import logging
import tempfile
import subprocess
from xml.etree import ElementTree

from autobump import config
from autobump.capir import Type, Field, Parameter, Signature, Function, Unit
from autobump.common import popen

logger = logging.getLogger(__name__)
libexec = os.path.join(os.path.dirname(__file__), "..", "libexec")


# Type system
class _JavaNativeType(Type):
    """Representation of a Java type.

    When checking for compatibility with another type,
    an external utility will be invoked to perform introspection
    and find out if Java considers two types to be compatible."""
    def __init__(self, name, dimension=0):
        self.name = name
        self.dimension = dimension

    def is_compatible(self, other):
        assert type(self) is type(other), "Should never happen: comparing a _JavaNativeType to something else."
        assert hasattr(self, "location") and self.location is not None, "Should never happen: location should be set prior to calling is_compatible"

        if self.dimension != other.dimension:
            return False

        if self.name == other.name:
            return True
        else:
            return _run_type_compatibility_checker(self.location, self.name, other.name)

    def __eq__(self, other):
        return self.is_compatible(other) and other.is_compatible(self)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<JavaNativeType {} {}>".format(self.dimension, self.name)

    def __hash__(self):
        return hash((self.dimension, self.name))


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


def _compile_and_run_utility(utility, args):
    """Compile a utility somewhere in a temporary directory
    so it can be used this time, and then run it."""

    logger.warning("Compiling {} in place".format(utility))
    filename = utility + ".java"
    # First, try to compile in place.
    return_code, stdout, stderr = popen([config.javac()] + [filename], cwd=libexec)
    if return_code != 0:
        logger.warning("Failed to compile {} in place, trying in a tempdir"
                       .format(utility))
        with tempfile.TemporaryDirectory() as dir:
            shutil.copy(os.path.join(libexec, filename), dir)
            return_code, stdout, stderr = popen([config.javac()] + [filename], cwd=dir)
            if return_code != 0:
                logger.error("Failed to compile {}! Please compile manually.".format(utility))
                raise JavaUtilityException("{} needs to be compiled".format(utility))
            # Call the utility from the temporary directory
            return _run_utility(utility, args, basedir=dir)
    # Compilation succeeded in-place, call the utility normally
    return _run_utility(utility, args)


def _run_utility(utility, args, basedir=libexec):
    """Run a Java utility program with arguments."""
    javafile = os.path.join(basedir, utility + ".java")
    classfile = os.path.join(basedir, utility + ".class")
    if os.path.isfile(javafile) and not os.path.isfile(classfile):
        logger.warning("{} has not been compiled".format(utility))
        return _compile_and_run_utility(utility, args)
    return_code, stdout, stderr = popen([config.java()] + [utility] + args, cwd=basedir)
    if return_code != 0:
        raise JavaUtilityException(stderr)
    return stdout


def _xml_element_to_type(elt):
    assert elt.tag == "type"
    return _JavaNativeType(elt.attrib["name"], int(elt.attrib["dimension"]))


def _xml_element_to_field(elt):
    """Convert an XML <field> into a Field."""
    assert elt.tag == "field"
    return Field(elt.attrib["name"], _xml_element_to_type(elt.find("type")))


def _xml_get_signature_of_method(elt):
    """Convert all <signature>s of a <method> into a Signature."""
    assert elt.tag == "method"
    signature_elt = elt.find("signature")
    parameter_elts = signature_elt.findall("parameter")
    parameters = [Parameter(p.attrib["name"], _xml_element_to_type(p.find("type")))
                  for p in parameter_elts]
    return_type = Parameter("$AUTOBUMP_RETURN$", _xml_element_to_type(elt.find("type")))
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
    if config.java_classpath() != "":
        logger.debug("java_native/classpath set, using that as classpath")
        os.environ["CLASSPATH"] = config.java_classpath()
    if "CLASSPATH" not in os.environ:
        logger.warning("No CLASSPATH set")
    else:
        logger.info("CLASSPATH is:\n\t{}".format(os.environ["CLASSPATH"]))

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
        dirs[:] = [d for d in dirs if not config.dir_ignored(d)]
        classfiles = [f for f in files if f.endswith(".class") and not config.file_ignored(f)]
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
