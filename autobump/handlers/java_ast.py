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
Convert a Java codebase into a list of Units using the AST.

This handler does not require any external utilities. It uses the library
'javalang' to get the AST of all Java files in the project.
"""

import os
import copy
import logging
import javalang

from autobump import config
from autobump.capir import Type, Field, Parameter, Signature, Function, Unit

logger = logging.getLogger(__name__)

# When qualifying types, we can (mostly) safely skip all of these.
_primitive_types = {"void", "byte", "short", "int", "long", "float", "double", "boolean", "char"}
_builtin_types = {"T", "String", "Object", "Class", "List", "Set", "Map", "Throwable", "Collection"}

_source_file_ext = ".java"


class _JavaType(Type):

    def __init__(self, name, dimension=0):
        self.name = name
        self.dimension = dimension
        self.children = set()

    def is_compatible(self, other):
        # Check if it's the same type
        if self == other:
            return True
        # Check if it's the same dimension.
        if self.dimension != other.dimension:
            return False
        # Check if it's a direct descendant.
        if len({jt for jt in self.children if jt.name == other.name}) == 1:
            return True
        # Recursively check all children.
        for child in self.children:
            if child.is_compatible(other):
                return True
        return False

    def __eq__(self, other):
        return self.name == other.name and self.dimension == other.dimension

    def __hash__(self):
        return hash((self.dimension, self.name))

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<JavaType {} {}, children: {}>".format(self.dimension, self.name, self.children)


class _JavaTypeSystem(object):
    """Represents a collection of types available to a Java codebase.

    Use 'add_qualified_type' to add fully-qualified type names to the system,
    e.g. "java.util.List".

    When done, use 'finalize' to resolve all types and build Type
    objects. Type objects can be looked up by using 'lookup'."""

    def __init__(self):
        self.types = dict()
        self.finalized = False

    def add_qualified_type(self, type_name, type_node_and_compilation):
        """Add a fully qualified 'type_name' with its AST node and compilation unit."""
        assert type(type_node_and_compilation) is tuple
        # Add the type as it is
        self.types[type_name] = type_node_and_compilation

    def finalize(self):
        """Replace all Type AST nodes with Type objects."""
        self.type_objects = {}
        for type_name in self.types.keys():
            node, compilation = self.types[type_name]
            if type_name not in self.type_objects:
                self.type_objects[type_name] = _JavaType(type_name)
            type_object = self.type_objects[type_name]

            # Check 'extends' for this type
            if hasattr(node, "extends") and node.extends is not None:
                if isinstance(node.extends, list):
                    # No, Java doesn't allow multiple inheritance,
                    # but an interface can extend several other interfaces.
                    # We can reuse the same logic as a class implementing multiple
                    # interfaces.
                    assert not hasattr(node, "implements")
                    node.implements = node.extends
                else:
                    extends = _qualify_type(node.extends, compilation)
                    if extends in self.type_objects:
                        self.type_objects[extends].children.add(type_object)
                    else:
                        extended_object = _JavaType(extends)
                        self.type_objects[extends] = extended_object
                        self.type_objects[extends].children.add(type_object)

            # Check 'implements' for this type
            if hasattr(node, "implements") and node.implements is not None:
                implements = [_qualify_type(r, compilation) for r in node.implements]
                for interface in implements:
                    if interface in self.type_objects:
                        self.type_objects[interface].children.add(type_object)
                    else:
                        interface_object = _JavaType(interface)
                        self.type_objects[interface] = interface_object
                        self.type_objects[interface].children.add(type_object)

        # Also need to add all primitive types and built-in types
        for primitive_type in _primitive_types.union(_builtin_types):
            type_object = _JavaType(primitive_type)
            self.type_objects[primitive_type] = type_object

        self.types = self.type_objects
        self.finalized = True

    def lookup(self, type_name):
        """Lookup a fully-qualified type name and get a Type object.

        Implicitly finalizes the JavaTypeSystem, if not done already."""
        if not self.finalized:
            self.finalize()

        dimension = _array_dimension(type_name)
        type_wo_dimension = _strip_array_dimension(type_name)
        if type_wo_dimension not in self.types:
            message = "{} is an external type".format(type_wo_dimension)
            if config.java_error_on_external_types():
                logger.error(message)
                exit(1)
            else:
                logger.warning(message)
                return _JavaType(type_name)

        type_object = copy.deepcopy(self.types[type_wo_dimension])
        type_object.dimension = dimension
        return type_object

    def qualify_lookup(self, type, compilation):
        """Qualify and lookup a type name and get a Type object.

        Implicitly finalizes the JavaTypeSystem, if not done already."""
        return self.lookup(_qualify_type(type, compilation))


_dummyType = _JavaType("dummy")
_dummyType.is_compatible = lambda t: True


def _array_dimension(name):
    for dimension in range(len(name)):
        if name[dimension] != '[':
            break
    return dimension


def _prefix_array_dimension(name, dimension):
    return "[" * dimension + name


def _strip_array_dimension(name):
    return name[_array_dimension(name):]


def _is_public(node):
    """Determine visibility of an AST node."""
    return hasattr(node, "modifiers") and "public" in node.modifiers


def _get_declarator_names(field):
    """Return list of declarator names of a field AST node."""
    assert isinstance(field, javalang.tree.FieldDeclaration)
    return [d.name for d in field.declarators]


def _qualify_type(type, compilation):
    """Return the fully-qualified name of a type reference in a compilation unit."""
    name = type.name
    dimension = len(getattr(type, "dimensions", []))
    if name in _primitive_types or name in _builtin_types:
        return _prefix_array_dimension(name, dimension)
    candidates = [i for i in compilation.imports
                  if i.path.endswith(name) and (i.path.find(name) == 0 or i.path[i.path.rfind(name) - 1] == ".")]
    assert len(candidates) <= 1, \
           "Don't know what to do: more than one candidate for qualifying {} found in {}".format(name, compilation.filename)
    if len(candidates) == 1:
        # Import statement exactly matched - must be this definition.
        return _prefix_array_dimension(candidates[0].path, dimension)
    else:
        # No import statement matched - should be in this package.
        # TODO: Handle wildcard imports somehow.
        assert name.find(".") == -1, \
               "Should never happen: no import statement found, yet {} is relative!".format(name)
        if compilation.package is not None:
            return _prefix_array_dimension(compilation.package.name + "." + name, dimension)
        else:
            return _prefix_array_dimension(name, dimension)


def _get_parameters(method, type_system, compilation):
    """Return a list of Parameters to a method."""
    parameters = []
    for p in method.parameters:
        name = p.name
        type = type_system.qualify_lookup(p.type, compilation)
        parameters.append(Parameter(name, type))
    return parameters


def _get_return_type(method, type_system, compilation):
    """Return the return type of a method."""
    if method.return_type is None:
        void = javalang.tree.Type(name="void", dimensions=[])
        return type_system.qualify_lookup(void, compilation)
    return type_system.qualify_lookup(method.return_type, compilation)


def _class_or_interface_to_unit(node, compilation, type_system):
    """Convert a class or interface declaration ('node') into a Unit.

    Requires the 'compilation' where the node so it can be used to look up type information."""
    assert isinstance(node, javalang.tree.ClassDeclaration) or \
           isinstance(node, javalang.tree.InterfaceDeclaration) or \
           isinstance(node, javalang.tree.AnnotationDeclaration) or \
           isinstance(node, javalang.tree.EnumDeclaration)

    # TODO: Handle annotation declarations
    if isinstance(node, javalang.tree.AnnotationDeclaration):
        return Unit("annotation", {}, {}, {})
    # TODO: Handle enum declarations
    if isinstance(node, javalang.tree.EnumDeclaration):
        return Unit("enum", {}, {}, {})

    fields = dict()
    functions = dict()
    units = dict()
    for n in [n for n in node.body if _is_public(n)]:

        # Convert fields.
        if isinstance(n, javalang.tree.FieldDeclaration):
            for declarator_name in _get_declarator_names(n):
                type_object = type_system.qualify_lookup(n.type, compilation)
                fields[declarator_name] = Field(declarator_name, type_object)

        # Convert methods.
        elif isinstance(n, javalang.tree.MethodDeclaration):
            parameters = _get_parameters(n, type_system, compilation)
            return_type = _get_return_type(n, type_system, compilation)
            # Java supports method overloading, where methods with the
            # same name can be differentiated by their parameters and return type.
            # To fit this into autobump's common representation, we set
            # the first parameter of the method to be the return type.
            # Then, we set a dummy type that is compatible with anything as the
            # actual return type of the function.
            parameters = [Parameter("$AUTOBUMP_RETURN$", return_type)] + parameters
            if n.name in functions:
                functions[n.name].signatures.append(Signature(parameters))
            else:
                functions[n.name] = Function(n.name,
                                                    _dummyType,
                                                    [Signature(parameters)])

        # Convert inner classes and interfaces.
        elif isinstance(n, javalang.tree.ClassDeclaration) or \
             isinstance(n, javalang.tree.InterfaceDeclaration):
            units[n.name] = _class_or_interface_to_unit(n, compilation, type_system)

    fqn = _qualify_type(node, compilation)
    return Unit(fqn, fields, functions, units)


def _source_to_compilation(filename, source):
    """Convert source text from 'filename' into a compilation unit."""
    try:
        tree = javalang.parse.parse(source)
    except javalang.parser.JavaSyntaxError as e:
        logger.error("Java Syntax Error  {}:{}: {}"
                    .format(filename, e.at, e.description))
        logger.error("Stopped parsing {}".format(filename))
        if not config.java_omit_on_error():
            exit(1)
        else:
            tree = javalang.parse.parse("")
    tree.filename = filename
    return tree


def _compilation_to_unit(compilation, type_system):
    """Convert a compilation unit to a Unit.

    In Java, there can be at most one class or interface declaration
    per file. To avoid redundancy, the file is not considered a separate
    Unit."""
    assert len(compilation.types) <= 1, \
           "Don't know what to do: {} contains more than one top-level type declaration!".format(compilation.filename)
    if len(compilation.types) == 0:
        return Unit("", {}, {}, {})
    return _class_or_interface_to_unit(compilation.types[0], compilation, type_system)


def _compilation_get_types(compilation):
    """Get all types declared in compilation unit."""
    types = []
    prefix = compilation.package.name + "." if compilation.package is not None else ""

    def get_inner_definitions(node, path):
        types = []
        for n in node.body:
            if not (isinstance(n, javalang.tree.ClassDeclaration) or
                    isinstance(n, javalang.tree.InterfaceDeclaration)):
                continue
            types.append((path + n.name, n))
            types = types + get_inner_definitions(n, path + n.name + ".")
        return types

    for type in compilation.types:
        types.append((prefix + type.name, type))
        types = types + get_inner_definitions(type, prefix + type.name + ".")

    return types


def java_codebase_to_units(location):
    """Return a list of Units representing a Java codebase in 'location'."""

    # This needs to perform two passes on all Java files.
    #
    # In the first pass:
    #   1) Java files are translated to compilation units (aka AST).
    #   2) The type system is enriched with all types declared in this codebase.
    #
    # In the second pass:
    #   1) Referential types are resolved when referring to this codebase.
    #   2) All compilation units are translated into Units.

    units = dict()

    # First pass
    type_system = _JavaTypeSystem()
    compilations = []
    for root, dirs, files in os.walk(location):
        dirs[:] = [d for d in dirs if not config.dir_ignored(d)]
        javafiles = [f for f in files if f.endswith(_source_file_ext) and not config.file_ignored(f)]
        for javafile in javafiles:
            with open(os.path.join(root, javafile), "r") as f:
                compilation = _source_to_compilation(javafile, f.read())
                for type_name, type_node in _compilation_get_types(compilation):
                    type_system.add_qualified_type(type_name, (type_node, compilation))
                compilations.append(compilation)

    type_system.finalize()

    # Second pass
    for compilation in compilations:
        unit = _compilation_to_unit(compilation, type_system)
        units[unit.name] = unit

    return units


build_required = False
codebase_to_units = java_codebase_to_units
