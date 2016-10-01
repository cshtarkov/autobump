"""Core codebase comparison logic."""
from enum import Enum
from autobump.common import Visibility, Unit


class Bump(Enum):
    none = 0
    patch = 1
    minor = 2
    major = 3


class Change(Enum):
    visibility_from_public_to_nonpublic = "Visibility went from public to non-public"
    visibility_became_public = "Visibility became public"
    introduced_default_value = "Introduced default value where there was previously none"
    removed_default_value = "Removed a default value"
    changed_default_value = "Changed a default value"


def _list_to_dict_by_name(code_properties):
    """Convert a list of CodeProperties to a dictionary,
    the key being the property name.

    E.g. [Parameter("foo"), Parameter("bar")] ->
         { "foo": Parameter("foo"), "bar": Parameter("bar") }"""
    d = {}
    for prop in code_properties:
        d[prop.name] = prop
    return d


def _report_change(change, name):
    """Report a change in a code property."""
    print(name + ": " + change.value)


def _compare_properties(a_prop, b_prop):
    """Compare two code properties which have the same name.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    assert a_prop.name == b_prop.name, "Shouldn't compare properties with different names."
    assert type(a_prop) is type(b_prop), "Shouldn't compare properties of different types."

    highestBump = Bump.none  # Biggest bump encountered so far.

    def _report_bump(bump):
        nonlocal highestBump
        if bump.value > highestBump.value:
            highestBump = bump

    # Compare visibility
    if hasattr(a_prop, "visibility"):
        assert hasattr(b_prop, "visibility"), "Should never happen: comparing properties when one has 'visibility' and other doesn't."
        if a_prop.visibility == Visibility.public and b_prop.visibility != Visibility.public:
            _report_change(Change.visibility_from_public_to_nonpublic, a_prop.name)
            _report_bump(Bump.major)
        if a_prop.visibility != Visibility.public and b_prop.visibility == Visibility.public:
            _report_change(Change.visibility_became_public, a_prop.name)
            _report_bump(Bump.minor)

    # Compare default values
    if hasattr(a_prop, "default_value"):
        assert hasattr(b_prop, "default_value"), "Should never happen: comparing properties when one has 'visibility' and other doesn't."
        if a_prop.default_value is None and b_prop.default_value is not None:
            _report_change(Change.introduced_default_value, a_prop.name)
            # TODO: What bump is this?
        elif a_prop.default_value is not None and b_prop.default_value is None:
            _report_change(Change.removed_default_value, a_prop.name)
            _report_bump(Bump.major)
        elif a_prop.default_value != b_prop.default_value:
            _report_change(Change.changed_default_value, a_prop.name)
            _report_bump(Bump.patch)

    # Compare inner properties recursively
    for k, v in a_prop.__dict__.items():
        if type(v) is not list:
            continue
        assert k in b_prop.__dict__, "Should never happen: comparing properties with different inner properties."
        a_inner = _list_to_dict_by_name(a_prop.__dict__[k])
        b_inner = _list_to_dict_by_name(b_prop.__dict__[k])
        for ki in {**a_inner, **b_inner}:
            if ki not in a_inner:
                # TODO: Handle case when a property is added.
                pass
            if ki not in b_inner:
                # TODO: Handle case when a property is removed.
                pass
            _report_bump(_compare_properties(a_inner[ki], b_inner[ki]))

    return highestBump


def compare_codebases(a_units, b_units):
    """Compare codebases consisting of Units.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    a_unit = Unit("codebase", [], [], a_units)
    b_unit = Unit("codebase", [], [], b_units)
    return _compare_properties(a_unit, b_unit)
