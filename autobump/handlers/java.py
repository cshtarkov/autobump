"""Convert a Java codebase into a list of Units."""
import javalang
from autobump import common

# Type System
class _JavaType(common.Type):
    pass

# Set of files to exclude
_excluded_files = [
]

_excluded_dirs = [
]

def _is_public(node):
    """Determine visibility of an AST node."""
    assert isinstance(node, javalang.ast.Node)
    return "public" in node.modifiers

def _class_or_interface_to_unit(node):
    """Convert a class or interface declaration into a Unit."""
    assert isinstance(node, javalang.ast.ClassDeclaration) or \
           isinstance(node, javalang.ast.InterfaceDeclaration)
    fields = []
    functions = []
    units = []
    for field in [f for f in node.fields if _is_public(f)]:
        fields.append(common.Field(f.name, f.type.name))
    for functions in [m for m in node.methods if _is_public(m)]:
        pass
