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
Codebase diffing logic.

This is the heart of Autobump.

The main entrypoint to this module 'compare_codebases'
is used to determine what the appropriate version bump should be
by considering how a codebase has changed over time.

Those changes can also be emmitted to a changelog file if requested.
"""

import logging
import functools
from enum import Enum

from autobump import config
from autobump.capir import Unit

logger = logging.getLogger(__name__)


@functools.total_ordering
class Bump(Enum):
    none = 0
    patch = 1
    minor = 2
    major = 3

    def __lt__(self, other):
        if type(self) is type(other):
            return self.value < other.value
        raise NotImplementedError()


class Change(Enum):
    removed_default_value = "Removed a default value"
    changed_default_value = "Changed a default value"
    entity_was_introduced = "Entity was introduced"
    entity_was_removed = "Entity was removed"
    function_was_overloaded = "Function was overloaded"
    overloaded_function_removed = "Overloaded function removed"
    parameter_added_to_signature = "Parameter(s) added to function signature"
    parameter_defaults_added_to_signature = "Parameter(s) with default value(s) added to function signature"
    parameter_removed_from_signature = "Parameter(s) removed from function signature"
    type_changed_to_compatible_type = "Type was changed to a compatible type"
    type_changed_to_incompatible_type = "Type was changed to an incompatible type"

    @staticmethod
    def get_bump(change):
        bump_map = {
            Change.removed_default_value: Bump.major,
            Change.changed_default_value: Bump.patch,
            Change.entity_was_introduced: Bump.minor,
            Change.entity_was_removed: Bump.major,
            Change.function_was_overloaded: Bump.minor,
            Change.overloaded_function_removed: Bump.major,
            Change.parameter_added_to_signature: Bump.major,
            Change.parameter_defaults_added_to_signature: Bump.minor,
            Change.parameter_removed_from_signature: Bump.major,
            Change.type_changed_to_compatible_type: Bump.patch,
            Change.type_changed_to_incompatible_type: Bump.major
        }
        return bump_map.get(change)


def _join_path(path, name):
    """Join a prefix path and an entity name to form a new path."""
    return (path + "." if path != "" else "") + name


def _compare_types(a_ent, b_ent):
    """Compare types of two entities and return a list of Changes."""
    changes = []
    if a_ent.type != b_ent.type:
        logger.debug("Types are different for {} and {}:\n\tVariant A: {}\n\tVariant B: {}"
                     .format(a_ent, b_ent, a_ent.type, b_ent.type))
        if b_ent.type.is_compatible(a_ent.type):
            logger.debug("Furthermore, types are compatible")
            changes.append(Change.type_changed_to_compatible_type)
        else:
            logger.debug("Furthermore, types are NOT compatible")
            changes.append(Change.type_changed_to_incompatible_type)
    return changes


def _compare_signatures(a_ent, b_ent):
    """Compare signatures of two entities and return a list of Changes."""
    changes = []
    logger.debug("Comparing signatures of {} and {}\n\tVariant A: {}\n\tVariant B: {}"
                 .format(a_ent, b_ent, str(a_ent.signatures), str(b_ent.signatures)))

    if len(a_ent.signatures) == 1 and len(b_ent.signatures) == 1:
        return _compare_signatures_directly(a_ent.signatures[0], b_ent.signatures[0])
    if len(a_ent.signatures) < len(b_ent.signatures):
        logger.debug("Variant A has less signatures")
        changes.append(Change.function_was_overloaded)
    elif len(a_ent.signatures) > len(b_ent.signatures):
        logger.debug("Variant B has less signatures")
        changes.append(Change.overloaded_function_removed)

    a_signatures = set(a_ent.signatures)
    b_signatures = set(b_ent.signatures)
    not_in_b = a_signatures.difference(b_signatures)
    not_in_a = b_signatures.difference(a_signatures)
    compat_signatures = set()
    for a_sig in not_in_b:
        for b_sig in not_in_a:
            sig_changes = _compare_signatures_directly(a_sig, b_sig)
            sig_changes = [c for c in sig_changes if Change.get_bump(c) > Bump.patch]
            if len(sig_changes) == 0:
                compat_signatures.add(a_sig)
                compat_signatures.add(b_sig)
    if len(compat_signatures) > 0:
        logger.debug("There were some different, but compatible signatures\n\t{}"
                     .format(str(compat_signatures)))
    not_in_a = not_in_a.difference(compat_signatures)
    not_in_b = not_in_b.difference(compat_signatures)
    for signature in not_in_a:
        logger.debug("Signature added in variant B")
        changes.append(Change.function_was_overloaded)
    for signature in not_in_b:
        logger.debug("Signature missing from variant B")
        changes.append(Change.overloaded_function_removed)

    return changes


def _compare_signatures_directly(a_signature, b_signature):
    """Compare two Signature objects directly and return a list of Changes."""
    changes = []
    a_parameters = a_signature.parameters
    b_parameters = b_signature.parameters
    logger.debug("Comparing signatures directly")

    # Check for type compatibility
    for pi in range(min(len(a_parameters), len(b_parameters))):
        changes = changes + _compare_types(a_parameters[pi], b_parameters[pi])

    # Check whether size of signature has changed
    if len(a_parameters) < len(b_parameters):
        # Signature was expanded - check for default values.
        logger.debug("Signature was expanded in later version: {} became {}"
                     .format(len(a_parameters), len(b_parameters)))
        all_new_have_defaults = True
        for pi in range(len(a_parameters), len(b_parameters)):
            if b_parameters[pi].default_value is None:
                logger.debug("At least one new parameter missing default value: {}"
                             .format(b_parameters[pi]))
                all_new_have_defaults = False
                break
        if all_new_have_defaults:
            logger.debug("All new parameters have default values")
            changes.append(Change.parameter_defaults_added_to_signature)
        else:
            logger.debug("NOT all new parameters have default values")
            changes.append(Change.parameter_added_to_signature)
    elif len(a_parameters) > len(b_parameters):
        # Signature has shrunk - always a breaking change.
        logger.debug("Signature has shrunk in later version: {} became {}"
                     .format(len(a_parameters), len(b_parameters)))
        changes.append(Change.parameter_removed_from_signature)

    return changes


def _compare_entities(a_ent, b_ent, changelog_file, path=""):
    """Compare two code entities which have the same name.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change.
    """
    assert a_ent.name == b_ent.name, "Shouldn't compare entities with different names."
    assert type(a_ent) is type(b_ent), "Shouldn't compare entities of different types."

    path = _join_path(path, a_ent.name)
    logger.debug("Comparing {}" .format(path))

    if config.entity_ignored(path) and a_ent.name != "":
        logger.debug("Ignoring because of configuration")
        return Bump.patch

    highestBump = Bump.patch  # Biggest bump encountered so far.

    def _report_change(change, path):
        if changelog_file is not None:
            print("{}: {}".format(path, change.value), file=changelog_file)
        _report_bump(Change.get_bump(change))

    def _report_bump(bump):
        nonlocal highestBump
        if bump.value > highestBump.value:
            highestBump = bump

    # Map of the form:
    # (attribute required) -> (comparison function)
    comparisons = {
        "type": _compare_types,
        "signatures": _compare_signatures
    }

    for attribute, comparator in comparisons.items():
        if hasattr(a_ent, attribute):
            assert hasattr(b_ent, attribute), "Should never happen: entities have mismatching attributes."
            for change in comparator(a_ent, b_ent):
                _report_change(change, path)

    # Compare inner entities recursively
    for k, v in a_ent.__dict__.items():
        if type(v) is not dict:
            continue
        assert k in b_ent.__dict__, "Should never happen: comparing entities with different inner entities."
        a_inner = a_ent.__dict__[k]
        b_inner = b_ent.__dict__[k]
        for ki in {**a_inner, **b_inner}:

            if ki not in a_inner:
                # Handle case when a entity was added.
                logger.debug("Not found in variant A: {}".format(b_inner[ki].name))
                _report_change(Change.entity_was_introduced, _join_path(path, b_inner[ki].name))
                continue

            if ki not in b_inner:
                # Handle case when a entity was removed.
                logger.debug("Not found in variant B: {}".format(a_inner[ki].name))
                _report_change(Change.entity_was_removed, _join_path(path, a_inner[ki].name))
                continue

            # Handle general case when a entity may have changed.
            _report_bump(_compare_entities(a_inner[ki], b_inner[ki], changelog_file, path))

    return highestBump


def compare_codebases(a_units, b_units, changelog_file):
    """Compare codebases consisting of Units.

    Return a Bump enum based on whether
    there was a major, minor, patch or no change."""
    # Represent both codebases as a single unit, and compare that.
    a_unit = Unit("", dict(), dict(), a_units)
    b_unit = Unit("", dict(), dict(), b_units)
    return _compare_entities(a_unit, b_unit, changelog_file)
