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
    entity_was_introduced = "Entity was introduced"
    entity_was_removed = "Entity was removed"
    parameter_added_to_signature = "Parameter(s) added to function signature"
    parameter_defaults_added_to_signature = "Parameter(s) with default value(s) added to function signature"
    parameter_removed_from_signature = "Parameter(s) removed from function signature"
    type_changed_to_compatible_type = "Type was changed to a compatible type"
    type_changed_to_incompatible_type = "Type was changed to an incompatible type"

    @staticmethod
    def get_bump(change):
        bump_map = {
            Change.introduced_default_value: Bump.none,  # TODO: What bump is this?
            Change.removed_default_value: Bump.major,
            Change.changed_default_value: Bump.patch,
            Change.entity_was_introduced: Bump.minor,
            Change.entity_was_removed: Bump.major,
            Change.parameter_added_to_signature: Bump.major,
            Change.parameter_defaults_added_to_signature: Bump.minor,
            Change.parameter_removed_from_signature: Bump.major,
            Change.type_changed_to_compatible_type: Bump.none,  # TODO: What bump is this?
            Change.type_changed_to_incompatible_type: Bump.major
        }
        return bump_map.get(change)


def _list_to_dict_by_name(entities):
    """Convert a list of Entities to a dictionary,
    the key being the entity name.

    E.g. [Parameter("foo"), Parameter("bar")] ->
         { "foo": Parameter("foo"), "bar": Parameter("bar") }"""
    d = {}
    for ent in entities:
        d[ent.name] = ent
    return d


def _log_change(change, name):
    """Report a change in a entity."""
    print(name + ": " + change.value)


def _compare_types(a_ent, b_ent):
    """Compare types of two entities and return a list of Changes."""
    changes = []
    if a_ent.type != b_ent.type:
        if a_ent.type.is_compatible(b_ent.type):
            changes.append(Change.type_changed_to_compatible_type)
        else:
            changes.append(Change.type_changed_to_incompatible_type)
    return changes


def _compare_signature(a_ent, b_ent):
    """Compare signatures of two entities and return a list of Changes."""

    changes = []
    a_parameters = a_ent.signature.parameters
    b_parameters = b_ent.signature.parameters

    # Check for type compatibility
    for pi in range(min(len(a_parameters), len(b_parameters))):
        if a_parameters[pi].type != b_parameters[pi].type:
            if not a_parameters[pi].type.is_compatible(b_parameters[pi].type):
                changes.append(Change.type_changed_to_incompatible_type)
            else:
                changes.append(Change.type_changed_to_compatible_type)
    # Check whether size of signature has changed
    if len(a_parameters) < len(b_parameters):
        # Signature was expanded - check for default values.
        all_new_have_defaults = True
        for pi in range(len(a_parameters), len(b_parameters)):
            if b_parameters[pi].default_value is None:
                all_new_have_defaults = False
                break
        if all_new_have_defaults:
            changes.append(Change.parameter_defaults_added_to_signature)
        else:
            changes.append(Change.parameter_added_to_signature)
    elif len(a_parameters) > len(b_parameters):
        # Signature has shrunk - always a breaking change.
        changes.append(Change.parameter_removed_from_signature)

    return changes


def _compare_entities(a_ent, b_ent, path=""):
    """Compare two code entities which have the same name.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    assert a_ent.name == b_ent.name, "Shouldn't compare entities with different names."
    assert type(a_ent) is type(b_ent), "Shouldn't compare entities of different types."

    path = (path + "." if path != "" else path) + a_ent.name

    highestBump = Bump.patch  # Biggest bump encountered so far.

    def _report_change(change, path, logger=_log_change):
        logger(change, path)
        _report_bump(Change.get_bump(change))

    def _report_bump(bump):
        nonlocal highestBump
        if bump.value > highestBump.value:
            highestBump = bump

    # Map of the form:
    # (attribute required) -> (comparison function)
    comparisons = {
        "type": _compare_types,
        "signature": _compare_signature
    }

    for attribute, comparator in comparisons.items():
        if hasattr(a_ent, attribute):
            assert hasattr(b_ent, attribute), "Should never happen: entities have mismatching attributes."
            for change in comparator(a_ent, b_ent):
                _report_change(change, path)

    # Compare inner entities recursively
    for k, v in a_ent.__dict__.items():
        if type(v) is not list:
            continue
        assert k in b_ent.__dict__, "Should never happen: comparing entities with different inner entities."
        a_inner = _list_to_dict_by_name(a_ent.__dict__[k])
        b_inner = _list_to_dict_by_name(b_ent.__dict__[k])
        for ki in {**a_inner, **b_inner}:

            if ki not in a_inner:
                # Handle case when a entity was added.
                _report_change(Change.entity_was_introduced, path + "." + b_inner[ki].name)
                continue

            if ki not in b_inner:
                # Handle case when a entity was removed.
                _report_change(Change.entity_was_removed, path + "." + a_inner[ki].name)
                continue

            # Handle general case when a entity may have changed.
            _report_bump(_compare_entities(a_inner[ki], b_inner[ki], path))

    return highestBump


def compare_codebases(a_units, b_units):
    """Compare codebases consisting of Units.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    # Represent both codebases as a single unit, and compare that.
    a_unit = Unit("codebase", [], [], a_units)
    b_unit = Unit("codebase", [], [], b_units)
    return _compare_entities(a_unit, b_unit)
