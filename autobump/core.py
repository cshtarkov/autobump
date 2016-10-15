"""Core codebase comparison logic."""
from enum import Enum
from autobump.common import Unit


class Bump(Enum):
    none = 0
    patch = 1
    minor = 2
    major = 3


class Change(Enum):
    introduced_default_value = "Introduced default value where there was previously none"
    removed_default_value = "Removed a default value"
    changed_default_value = "Changed a default value"
    property_was_introduced = "Property was introduced"
    property_was_removed = "Property was removed"
    parameter_added_to_signature = "Parameter was added to function signature"
    parameter_removed_from_signature = "Parameter was removed from function signature"
    type_changed_to_compatible_type = "Type was changed to a compatible type"
    type_changed_to_incompatible_type = "Type was changed to an incompatible type"

    @staticmethod
    def get_bump(change):
        bump_map = {
            Change.introduced_default_value: Bump.none,  # TODO: What bump is this?
            Change.removed_default_value: Bump.major,
            Change.changed_default_value: Bump.patch,
            Change.property_was_introduced: Bump.minor,
            Change.property_was_removed: Bump.major,
            Change.type_changed_to_compatible_type: Bump.none,  # TODO: What bump is this?
            Change.type_changed_to_incompatible_type: Bump.major
        }
        return bump_map.get(change)


def _list_to_dict_by_name(code_properties):
    """Convert a list of CodeProperties to a dictionary,
    the key being the property name.

    E.g. [Parameter("foo"), Parameter("bar")] ->
         { "foo": Parameter("foo"), "bar": Parameter("bar") }"""
    d = {}
    for prop in code_properties:
        d[prop.name] = prop
    return d


def _log_change(change, name):
    """Report a change in a code property."""
    print(name + ": " + change.value)


def _compare_properties(a_prop, b_prop, path=""):
    """Compare two code properties which have the same name.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    assert a_prop.name == b_prop.name, "Shouldn't compare properties with different names."
    assert type(a_prop) is type(b_prop), "Shouldn't compare properties of different types."

    path = (path + "." if path != "" else path) + a_prop.name

    highestBump = Bump.patch  # Biggest bump encountered so far.

    def _report_change(change, path, logger=_log_change):
        logger(change, path)
        _report_bump(Change.get_bump(change))

    def _report_bump(bump):
        nonlocal highestBump
        if bump.value > highestBump.value:
            highestBump = bump

    # Compare types
    if hasattr(a_prop, "type"):
        assert hasattr(b_prop, "type"), "Should never happen: comparing properties when one has 'type' and other doesn't."
        if a_prop.type is not b_prop.type:
            if a_prop.type.is_compatible(b_prop.type):
                _report_change(Change.type_changed_to_compatible_type, path)
            else:
                _report_change(Change.type_changed_to_incompatible_type, path)

    # Compare default values
    if hasattr(a_prop, "default_value"):
        assert hasattr(b_prop, "default_value"), "Should never happen: comparing properties when one has 'default_value' and other doesn't."
        if a_prop.default_value is None and b_prop.default_value is not None:
            _report_change(Change.introduced_default_value, path)
        elif a_prop.default_value is not None and b_prop.default_value is None:
            _report_change(Change.removed_default_value, path)
        elif a_prop.default_value != b_prop.default_value:
            _report_change(Change.changed_default_value, path)

    # Compare inner properties recursively
    for k, v in a_prop.__dict__.items():
        if type(v) is not list:
            continue
        assert k in b_prop.__dict__, "Should never happen: comparing properties with different inner properties."
        a_inner = _list_to_dict_by_name(a_prop.__dict__[k])
        b_inner = _list_to_dict_by_name(b_prop.__dict__[k])
        for ki in {**a_inner, **b_inner}:

            if ki not in a_inner:
                # Handle case when a property was added.
                _report_change(Change.property_was_introduced, path + "." + b_inner[ki].name)
                continue

            if ki not in b_inner:
                # Handle case when a property was removed.
                _report_change(Change.property_was_removed, a_inner[ki].name)
                continue

            # Handle general case when a property may have changed.
            _report_bump(_compare_properties(a_inner[ki], b_inner[ki], path))

    return highestBump


def compare_codebases(a_units, b_units):
    """Compare codebases consisting of Units.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    # Represent both codebases as a single unit, and compare that.
    a_unit = Unit("codebase", [], [], a_units)
    b_unit = Unit("codebase", [], [], b_units)
    return _compare_properties(a_unit, b_unit)
