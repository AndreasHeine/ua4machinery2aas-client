"""Unit tests for the shared helper functions in common.helper."""

import datetime
import types
import uuid

import pytest
from asyncua import ua

from common.helper import (
    as_int_or_none,
    ensure_list,
    make_expanded_nodeid_from_string,
    make_nodeid_string,
    pick_field,
    utf8_base64_url_encode,
    variant_to_json_serializable,
)

MACHINERY_NAMESPACE = "http://MyControledMachine-Namespace/UA"
NAMESPACE_ARRAY = ["http://opcfoundation.org/UA/", MACHINERY_NAMESPACE]


def test_utf8_base64_url_encode_removes_padding() -> None:
    """BaSyx identifiers are Base64-URL encoded without padding characters."""
    encoded = utf8_base64_url_encode("urn:example:machine")
    assert "=" not in encoded
    assert encoded == "dXJuOmV4YW1wbGU6bWFjaGluZQ"


def test_ensure_list_normalizes_array_shapes() -> None:
    """None, a single structure and a real array all become a list."""
    assert ensure_list(None) == []
    assert ensure_list("single") == ["single"]
    assert ensure_list({"ID": "one"}) == [{"ID": "one"}]
    assert ensure_list([1, 2]) == [1, 2]
    assert ensure_list((1, 2)) == [1, 2]


def test_pick_field_uses_the_first_available_field_name() -> None:
    """Field names that differ between information models are tolerated."""
    assert pick_field({"State": 1}, "JobState", "State") == 1
    assert pick_field({"JobState": 1, "State": 2}, "JobState", "State") == 1
    assert pick_field({"JobState": None, "State": 2}, "JobState", "State") == 2
    assert pick_field({"Other": 3}, "JobState", "State") is None


def test_as_int_or_none_converts_numeric_values() -> None:
    """Numeric-ish values map to int, everything else maps to None."""
    assert as_int_or_none(5) == 5
    assert as_int_or_none("5") == 5
    assert as_int_or_none(" 5 ") == 5
    assert as_int_or_none(True) == 1
    assert as_int_or_none(5.0) == 5
    assert as_int_or_none(5.5) is None
    assert as_int_or_none("5.5") is None
    assert as_int_or_none("unknown") is None
    assert as_int_or_none(None) is None
    assert as_int_or_none(b"5") is None


def test_make_nodeid_string_keeps_identifier_types() -> None:
    """Numeric, string, guid and bytestring identifiers survive the round trip."""
    assert make_nodeid_string("ns=2;s=Machine", NAMESPACE_ARRAY) == "ns=2;s=Machine"
    assert make_nodeid_string("ns=2;i=456", NAMESPACE_ARRAY) == "ns=2;i=456"
    assert make_nodeid_string("i=1234", NAMESPACE_ARRAY) == "ns=0;i=1234"

    guid = uuid.uuid4()
    assert make_nodeid_string(f"ns=2;g={guid}", NAMESPACE_ARRAY) == f"ns=2;g={guid}"
    assert make_nodeid_string("ns=2;b=YWJj", NAMESPACE_ARRAY) == "ns=2;b=YWJj"


def test_make_nodeid_string_normalizes_server_prefix() -> None:
    """`svr=` is a common typo for `srv=` and both forms resolve to the same NodeId."""
    assert make_nodeid_string("svr=0;ns=2;i=7", NAMESPACE_ARRAY) == "ns=2;i=7"
    assert make_nodeid_string("srv=0;ns=2;i=7", NAMESPACE_ARRAY) == "ns=2;i=7"


def test_make_nodeid_string_maps_namespace_uri_to_index() -> None:
    """`nsu=` identifiers are resolved against the namespace array of the server."""
    assert make_nodeid_string(f"nsu={MACHINERY_NAMESPACE};s=Machine", NAMESPACE_ARRAY) == "ns=1;s=Machine"
    assert make_nodeid_string("nsu=http://unknown-namespace/UA;s=Machine", NAMESPACE_ARRAY) == "ns=0;s=Machine"


def test_make_nodeid_string_rejects_unparsable_values() -> None:
    """A malformed NodeId must raise ValueError instead of an opaque asyncua error."""
    with pytest.raises(ValueError):
        make_nodeid_string("this-is-not-a-nodeid", NAMESPACE_ARRAY)


def test_make_expanded_nodeid_keeps_namespace_uri() -> None:
    """The expanded form keeps both the mapped index and the original namespace URI."""
    expanded = make_expanded_nodeid_from_string(f"nsu={MACHINERY_NAMESPACE};s=Machine", NAMESPACE_ARRAY)
    assert expanded.NamespaceIndex == 1
    assert expanded.NamespaceUri == MACHINERY_NAMESPACE
    assert expanded.Identifier == "Machine"


def test_variant_to_json_serializable_scalars() -> None:
    """Plain values and ua.Variant wrappers become JSON compatible values."""
    assert variant_to_json_serializable(ua.Variant(7)) == 7
    assert variant_to_json_serializable(ua.Variant("text")) == "text"
    assert variant_to_json_serializable(None) is None
    assert variant_to_json_serializable(b"abc") == "YWJj"

    identifier = uuid.uuid4()
    assert variant_to_json_serializable(identifier) == str(identifier)


def test_variant_to_json_serializable_dates_use_iso8601() -> None:
    """Dates and datetimes are emitted as XSD compatible ISO 8601 strings."""
    moment = datetime.datetime(2026, 6, 5, 14, 48, 1, tzinfo=datetime.timezone.utc)
    assert variant_to_json_serializable(moment) == "2026-06-05T14:48:01+00:00"
    assert variant_to_json_serializable(datetime.date(2026, 6, 5)) == "2026-06-05"


def test_variant_to_json_serializable_structure_objects() -> None:
    """Structure instances are serialized through their public attributes."""
    structure = types.SimpleNamespace(ID="root", Value=1)
    result = variant_to_json_serializable({"Parameter": structure})
    assert result == {"Parameter": {"ID": "root", "Value": 1}}


def test_variant_to_json_serializable_serializes_aliased_objects_twice() -> None:
    """Shared (but not circular) objects must not be replaced by a placeholder."""
    shared = {"Text": "same"}
    result = variant_to_json_serializable({"first": shared, "second": shared})
    assert result["first"] == {"Text": "same"}
    assert result["second"] == {"Text": "same"}


def test_variant_to_json_serializable_breaks_circular_references() -> None:
    """Real cycles end the recursion instead of raising RecursionError."""
    looping: dict = {"name": "loop"}
    looping["self"] = looping
    assert variant_to_json_serializable(looping) == {"name": "loop", "self": "<circular-reference>"}

    items: list = [1]
    items.append(items)
    assert variant_to_json_serializable(items) == [1, "<circular-reference>"]
